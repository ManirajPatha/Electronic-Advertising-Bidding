import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://www.bidnetdirect.com"
START_URL = "https://www.bidnetdirect.com/california/cityofsantaclara/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def clean_text(text):
    if not text:
        return None

    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\xa0", " ")

    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


def get_soup(url):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_text(element):
    return clean_text(element.get_text(strip=True)) if element else None


def scrape_detail_page(url):
    print(f" Scraping -> {url}")

    soup = get_soup(url)
    data = {}

    title_tag = soup.find("h1")
    data["title"] = extract_text(title_tag)

    fields = soup.select(".mets-field")

    for f in fields:
        label_tag = f.find("span", class_="mets-field-label")
        value_tag = f.find("div", class_="mets-field-body")

        if label_tag:
            label = clean_text(label_tag.get_text(strip=True).replace(":", ""))
        else:
            continue

        if "locked" in f.get("class", []):
            data[label] = "Locked - Registered members only"
        else:
            data[label] = extract_text(value_tag)

    return data


def scrape_main_page():
    soup = get_soup(START_URL)
    all_rows = soup.select("tr.mets-table-row")

    links = []
    for row in all_rows:
        link_tag = row.find("a", class_="solicitation-link")
        if link_tag:
            link = BASE_URL + link_tag["href"]
            links.append(link)

    return links


def main():
    print("Fetching opportunity list...")
    links = scrape_main_page()

    results = []

    for link in links:
        try:
            info = scrape_detail_page(link)
            info["url"] = link
            results.append(info)
            time.sleep(1)
        except Exception as e:
            print("Error scraping", link, str(e))

    with open("City_of_Santa_Clara.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\nDone! Saved to SantaClara.json")


if __name__ == "__main__":
    main()