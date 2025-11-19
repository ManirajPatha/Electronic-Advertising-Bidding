import json
import time
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

URL = "https://vendors.planetbids.com/portal/14599/bo/bo-search"
OUTPUT_JSON = "stanislaus_bids_bidding.json"
WAIT_TIME = 30


def setup_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


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


def scrape_one_bid(driver: webdriver.Chrome, wait: WebDriverWait) -> Dict:
    data: Dict[str, object] = {}

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

    return data


def go_back_to_search(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    print("[INFO] Clicking 'Back to Bid Search'")

    back_link = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//a[contains(@href,'/portal/14599/bo/bo-search') "
                "and contains(normalize-space(.), 'Back to Bid Search')]",
            )
        )
    )
    driver.execute_script("arguments[0].click();", back_link)

    get_results_table(driver, wait)


def scrape_all_bids(driver: webdriver.Chrome, wait: WebDriverWait) -> List[Dict]:
    table = get_results_table(driver, wait)
    rows = table.find_elements(By.XPATH, ".//tbody/tr")
    total_rows = len(rows)
    print(f"[INFO] Found {total_rows} bidding rows.")

    all_bids: List[Dict] = []

    for index in range(total_rows):
        print(f"[INFO] Processing row {index + 1}/{total_rows}")

        table = get_results_table(driver, wait)
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        row = rows[index]

        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) >= 2:
            bid_title = tds[1].text.strip()
        else:
            bid_title = row.text.strip()

        print(f"   ↳ Opening bid: {bid_title}")

        driver.execute_script("arguments[0].scrollIntoView(true);", row)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", row)

        bid_data = scrape_one_bid(driver, wait)
        bid_data.setdefault("Bid Title", bid_title)
        all_bids.append(bid_data)

        go_back_to_search(driver, wait)

    return all_bids


def main():
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

        all_bids = scrape_all_bids(driver, wait)

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(all_bids, f, ensure_ascii=False, indent=2)

        print(f"[OK] Saved {len(all_bids)} bids to {OUTPUT_JSON}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
