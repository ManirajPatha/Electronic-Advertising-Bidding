import requests
from bs4 import BeautifulSoup
import json

BASE = "https://www.cityoforinda.gov/"
LIST_URL = "https://www.cityoforinda.gov/Bids.aspx"


def clean_text(el):
    """Extract visible text, keeping line breaks."""
    if not el:
        return ""
    return el.get_text("\n", strip=True)


def scrape_detail(url):
    """Scrape every field inside the bid detail page."""
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    top_table = soup.find("table", summary="Bid details")
    if top_table:
        for tr in top_table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                key = clean_text(tds[0]).replace(":", "")
                value = clean_text(tds[1])
                data[key] = value

    big_table = soup.find("div", class_="fr-view")
    if big_table:
        rows = big_table.find_all("tr")
        current_key = None

        for tr in rows:
            header = tr.find("span", class_="BidListHeader")
            value = tr.find("span", class_="BidDetail")

            if header:
                current_key = clean_text(header).replace(":", "")
                data[current_key] = ""
            elif value and current_key:
                data[current_key] = value.get_text("\n", strip=True)

    data["Detail URL"] = url

    return data


def scrape_all():
    """Scrape listing page and visit each opportunity."""
    r = requests.get(LIST_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    all_bids = []

    rows = soup.find_all("div", class_="listItemsRow")

    for row in rows:
        a = row.find("a")
        if not a:
            continue

        rel = a.get("href").lstrip("/")
        detail_url = BASE + rel

        print(f"Scraping → {detail_url}")
        bid_data = scrape_detail(detail_url)
        all_bids.append(bid_data)

    return all_bids


bids = scrape_all()

with open("orinda_full_bids.json", "w", encoding="utf8") as f:
    json.dump(bids, f, ensure_ascii=False, indent=4)

print("Saved → orinda_full_bids.json")
