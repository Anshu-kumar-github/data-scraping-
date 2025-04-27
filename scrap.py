import requests
from bs4 import BeautifulSoup
import csv
import openpyxl
import time
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://www.hindustantimes.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
WAIT_TIME = 2  # seconds between requests

def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_article(url):
    html = fetch_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    title = soup.find('h1')
    author = soup.select_one('span[class*="author"], a[class*="author"]')
    date = soup.find('span', class_='dateTime')
    content_block = soup.find('div', class_='storyDetails')
    category_links = soup.select('ul.breadcrumb li a')

    article = {
        'Title': title.text.strip() if title else "N/A",
        'Author': author.text.strip() if author else "N/A",
        'Published Time': date.text.strip() if date else "N/A",
        'URL': url,
        'Categories': ', '.join(a.text.strip() for a in category_links[1:]) if category_links else "N/A",
        'Full Text': '\n\n'.join(p.text.strip() for p in content_block.find_all('p')) if content_block else "N/A"
    }
    return article

def save_to_csv(articles, filename):
    keys = ['Title', 'Author', 'Published Time', 'URL', 'Categories', 'Full Text']
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for article in articles:
            writer.writerow(article)
            # Write an empty row after each article for separation
            writer.writerow({})

def save_to_txt(articles, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for idx, article in enumerate(articles, start=1):
            f.write(f"ARTICLE #{idx}\n")
            f.write("="*40 + "\n")
            for key, value in article.items():
                f.write(f"{key}:\n{value}\n\n")
            f.write("-"*80 + "\n\n")  # separator between articles

def save_to_excel(articles, filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scraped Articles"

    headers = ['Title', 'Author', 'Published Time', 'URL', 'Categories', 'Full Text']
    ws.append(headers)

    for article in articles:
        row = [article.get(key, "") for key in headers]
        ws.append(row)
        # Add a separator row after each article (optional for Excel)
        ws.append(["-"*10 for _ in headers])

    wb.save(filename)

def scrape_articles(category, max_articles, file_type):
    articles = []
    page = 1

    print("\nScraping started...")

    while len(articles) < max_articles:
        if page == 1:
            url = f"{BASE_URL}/{category}/"
        else:
            url = f"{BASE_URL}/{category}/page-{page}"

        html = fetch_html(url)
        if not html:
            break

        soup = BeautifulSoup(html, 'lxml')
        links = soup.select('div[class*="cartHolder"] a')

        if not links:
            print("No more articles found.")
            break

        for link in links:
            if len(articles) >= max_articles:
                break
            href = link.get('href')
            if not href or '/photos/' in href or '/videos/' in href:
                continue

            full_url = urljoin(BASE_URL, href)

            if any(a['URL'] == full_url for a in articles):
                continue

            article = extract_article(full_url)
            if article:
                articles.append(article)
                print(f"Scraped: {article['Title'][:60]}...")

            time.sleep(WAIT_TIME)

        page += 1
        time.sleep(WAIT_TIME)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"hindustan_times_{category}_{date_str}.{file_type}"

    if file_type == 'csv':
        save_to_csv(articles, filename)
    elif file_type == 'txt':
        save_to_txt(articles, filename)
    elif file_type == 'xlsx':
        save_to_excel(articles, filename)
    else:
        print("Unknown file type. Saving as CSV.")
        save_to_csv(articles, filename)

    print(f"\n✅ Scraped {len(articles)} articles and saved to '{filename}'.")

if __name__ == "__main__":
    categories = {
        '1': 'india-news',
        '2': 'world-news',
        '3': 'business',
        '4': 'cities',
        '5': 'entertainment',
        '6': 'sports'
    }

    print("\nAvailable categories:")
    for num, cat in categories.items():
        print(f"{num}. {cat}")

    choice = input("\nEnter category number (default is 'business'): ").strip()
    selected_category = categories.get(choice, 'business')

    try:
        max_articles = int(input("How many articles to scrape? (default 10): ").strip() or 10)
    except ValueError:
        max_articles = 10

    print("\nChoose file type to save:")
    print("1. CSV")
    print("2. TXT")
    print("3. EXCEL")
    file_choice = input("Enter choice (default CSV): ").strip()

    file_type = 'csv'
    if file_choice == '2':
        file_type = 'txt'
    elif file_choice == '3':
        file_type = 'xlsx'

    scrape_articles(selected_category, max_articles, file_type)
