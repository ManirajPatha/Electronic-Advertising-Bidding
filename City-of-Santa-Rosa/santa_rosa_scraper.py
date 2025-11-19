import json
import os
import time
from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)

URL = "https://vendors.planetbids.com/portal/20314/bo/bo-search"
OUTPUT_JSON = "santa_rosa_bids_bidding.json"
WAIT_TIME = 30


def setup_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


def make_bid_id(posted: str, title: str, invitation: str) -> str:
    parts = [
        (posted or "").strip(),
        (title or "").strip(),
        (invitation or "").strip(),
    ]
    return " | ".join(parts)


def derive_bid_id_from_existing(bid: Dict, idx: int) -> str:
    if "bid_id" in bid:
        return bid["bid_id"]

    parts = []
    title = bid.get("Bid Title")
    if title:
        parts.append(str(title).strip())

    info = bid.get("Bid Information", {})
    if isinstance(info, dict):
        for section in info.values():
            if isinstance(section, dict):
                num = (
                    section.get("Bid Number")
                    or section.get("Bid #")
                    or section.get("Bid #:")
                )
                if num:
                    parts.append(str(num).strip())
                    break

    if parts:
        bid_id = " | ".join(parts)
    else:
        bid_id = f"legacy_{idx}"

    bid["bid_id"] = bid_id
    return bid_id


def load_existing_bids(path: str) -> Tuple[List[Dict], Dict[str, Dict]]:
    if not os.path.exists(path):
        print("[INFO] No existing JSON found, starting fresh.")
        return [], {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("[WARN] Existing JSON is not a list, ignoring.")
            return [], {}
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
        return [], {}

    by_id: Dict[str, Dict] = {}
    for idx, bid in enumerate(data):
        bid_id = derive_bid_id_from_existing(bid, idx)
        by_id[bid_id] = bid

    print(f"[INFO] Loaded {len(by_id)} existing bids from {path}")
    return data, by_id


def save_bids(path: str, bids: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bids, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved {len(bids)} total bids to {path}")


def select_stage_bidding(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    print("[INFO] Selecting Stage = Bidding")

    stage_select_el = wait.until(
        EC.element_to_be_clickable((By.ID, "stageId-field"))
    )

    stage_select = Select(stage_select_el)
    try:
        stage_select.select_by_value("3")
    except NoSuchElementException:
        stage_select.select_by_visible_text("Bidding")

    time.sleep(0.5)

    print("[INFO] Clicking Search button")
    search_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(@class,'search-btn') and normalize-space()='Search']",
            )
        )
    )
    driver.execute_script("arguments[0].click();", search_btn)

    time.sleep(2)


def get_results_table(driver: webdriver.Chrome, wait: WebDriverWait):
    print("[INFO] Waiting for results table with rows...")
    table = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//table[.//tbody/tr]")
        )
    )
    return table


def scrape_bid_information(driver: webdriver.Chrome, wait: WebDriverWait) -> Dict:
    try:
        bid_info_tab = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(.,'Bid Information')]")
            )
        )
        bid_info_tab.click()
    except TimeoutException:
        pass

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//h3[contains(@class,'section-heading') and contains(.,'Bid Detail')]",
            )
        )
    )

    rows = driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'row') and .//div[contains(@class,'bid-detail-item-title')]]",
    )

    sections: Dict[str, Dict[str, str]] = {}

    for row in rows:
        try:
            title_el = row.find_element(
                By.XPATH,
                ".//div[contains(@class,'bid-detail-item-title')]",
            )
            value_el = row.find_element(
                By.XPATH,
                ".//div[contains(@class,'bid-detail-item-value')]",
            )
        except NoSuchElementException:
            continue

        label = " ".join(title_el.text.split()).rstrip(":")
        value = value_el.text.strip()

        try:
            header_el = row.find_element(
                By.XPATH,
                ".//preceding::h3[contains(@class,'section-heading')][1]",
            )
            section_name = " ".join(header_el.text.split())
        except NoSuchElementException:
            section_name = "Bid Information"

        if section_name not in sections:
            sections[section_name] = {}

        sections[section_name][label] = value

    return sections


def scrape_prospective_bidders(
    driver: webdriver.Chrome, wait: WebDriverWait
) -> List[Dict[str, str]]:
    bidders: List[Dict[str, str]] = []

    try:
        tab = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(.,'Prospective Bidders')]")
            )
        )
        tab.click()
    except TimeoutException:
        print("[WARN] Prospective Bidders tab not found")
        return bidders

    try:
        table = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//table[contains(@class,'pb-datatable') and "
                    ".//thead//th[.//span[contains(@class,'span-title') and normalize-space()='Vendor']] ]",
                )
            )
        )
    except TimeoutException:
        print("[WARN] Prospective Bidders table not found")
        return bidders

    headers = [
        span.text.strip()
        for span in table.find_elements(
            By.XPATH, ".//thead/tr/th/span[contains(@class,'span-title')]"
        )
    ]
    if not headers:
        headers = ["Vendor", "Type", "Status", "Pre-Bid Meeting Attendee"]

    rows = table.find_elements(By.XPATH, ".//tbody/tr")
    for row in rows:
        cells = row.find_elements(By.XPATH, "./td")
        if not cells:
            continue

        row_data: Dict[str, object] = {}
        for idx, cell in enumerate(cells):
            col_name = headers[idx] if idx < len(headers) else f"Column_{idx+1}"
            text = cell.text.strip()

            if col_name == "Vendor":
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                row_data[col_name] = lines
            else:
                row_data[col_name] = text

        if row_data:
            bidders.append(row_data)

    return bidders


def scrape_one_bid(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    bid_id: str,
    summary: Dict[str, str],
) -> Dict:
    data: Dict[str, object] = {"bid_id": bid_id, "Summary": summary}

    try:
        title_el = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//h2[contains(@class,'page-title') or contains(@class,'title') "
                    "or @id='lblTitle' or @id='lblBidTitle']",
                )
            )
        )
        data["Bid Title"] = title_el.text.strip()
    except TimeoutException:
        try:
            title_el = driver.find_element(By.XPATH, "(//h1 | //h2)[1]")
            data["Bid Title"] = title_el.text.strip()
        except NoSuchElementException:
            pass

    data["Bid Information"] = scrape_bid_information(driver, wait)

    data["Prospective Bidders"] = scrape_prospective_bidders(driver, wait)

    try:
        data["Detail URL"] = driver.current_url
    except Exception:
        pass

    return data


def go_back_to_search(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    print("[INFO] Clicking 'Back to Bid Search'")

    back_link = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//a[contains(@href,'/portal/20314/bo/bo-search') "
                "and contains(normalize-space(.), 'Back to Bid Search')]",
            )
        )
    )
    driver.execute_script("arguments[0].click();", back_link)

    get_results_table(driver, wait)


def scrape_new_bids(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    existing_ids: set,
) -> List[Dict]:
    table = get_results_table(driver, wait)
    rows = table.find_elements(By.XPATH, ".//tbody/tr")
    total_rows = len(rows)
    print(f"[INFO] Found {total_rows} bidding rows on website.")

    new_bids: List[Dict] = []

    for index in range(total_rows):
        print(f"[INFO] Processing row {index + 1}/{total_rows}")

        table = get_results_table(driver, wait)
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        row = rows[index]

        cells = row.find_elements(By.TAG_NAME, "td")

        posted = cells[0].text.strip() if len(cells) >= 1 else ""
        project_title = cells[1].text.strip() if len(cells) >= 2 else row.text.strip()
        invitation_no = cells[2].text.strip() if len(cells) >= 3 else ""
        due_date = cells[3].text.strip() if len(cells) >= 4 else ""
        remaining = cells[4].text.strip() if len(cells) >= 5 else ""
        stage = cells[5].text.strip() if len(cells) >= 6 else ""
        fmt = cells[6].text.strip() if len(cells) >= 7 else ""

        bid_id = make_bid_id(posted, project_title, invitation_no)

        if bid_id in existing_ids:
            print(f"   [SKIP] Already scraped: {bid_id}")
            continue

        print(f"   [NEW] Scraping bid: {bid_id}")

        try:
            if len(cells) >= 2:
                link_el = cells[1].find_element(By.TAG_NAME, "a")
            else:
                link_el = row
        except NoSuchElementException:
            link_el = row

        driver.execute_script("arguments[0].scrollIntoView(true);", link_el)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", link_el)

        summary = {
            "Posted": posted,
            "Project Title": project_title,
            "Invitation #": invitation_no,
            "Due Date": due_date,
            "Remaining": remaining,
            "Stage": stage,
            "Format": fmt,
        }

        bid_data = scrape_one_bid(driver, wait, bid_id, summary)
        new_bids.append(bid_data)

        go_back_to_search(driver, wait)

    print(f"[INFO] New bids scraped this run: {len(new_bids)}")
    return new_bids


def main():
    existing_bids, existing_by_id = load_existing_bids(OUTPUT_JSON)
    existing_ids = set(existing_by_id.keys())

    driver = setup_driver()
    wait = WebDriverWait(driver, WAIT_TIME)

    try:
        driver.get(URL)

        wait.until(
            EC.presence_of_element_located(
                (By.ID, "stageId-field")
            )
        )

        select_stage_bidding(driver, wait)

        new_bids = scrape_new_bids(driver, wait, existing_ids)

        all_bids = existing_bids + new_bids
        save_bids(OUTPUT_JSON, all_bids)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
