import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

START_URL = "https://qcpi.questcdn.com/cdn/posting/?group=2332161&provider=2332161&projType=all"

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 30)
driver.get(START_URL)

results = []


def wait_for_table():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table_id tbody tr")))
    time.sleep(1)


def go_back_home():
    driver.execute_script("show_postings();")
    wait_for_table()


def scrape_detail_page():
    wait.until(EC.presence_of_element_located((By.ID, "view-bid-posting")))
    time.sleep(1)

    details = {}

    container = driver.find_element(By.ID, "view-bid-posting")

    header_data = {}
    try:
        header_div = container.find_element(By.CSS_SELECTOR, ".posting-second-header")
        bolds = header_div.find_elements(By.TAG_NAME, "b")
        for b in bolds:
            txt = b.text.strip()
            if ":" in txt:
                k, v = txt.split(":", 1)
                header_data[k.strip()] = v.strip()
    except Exception:
        pass

    if header_data:
        details["Quest Header"] = header_data

    accordions = container.find_elements(By.CSS_SELECTOR, "button.accordion")

    for btn in accordions:
        section_title = btn.text.strip()
        if not section_title:
            continue

        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(0.3)

        try:
            panel = btn.find_element(By.XPATH, "following-sibling::div[1]")
        except Exception:
            continue

        if section_title == "Primary Contact Information":
            section_dict = {}

            try:
                h4s = panel.find_elements(By.TAG_NAME, "h4")
            except Exception:
                h4s = []

            for h4 in h4s:
                sub_title = h4.text.strip()
                if not sub_title:
                    continue

                try:
                    sub_table = h4.find_element(By.XPATH, "following-sibling::table[1]")
                except Exception:
                    continue

                rows = sub_table.find_elements(By.TAG_NAME, "tr")
                sub_data = {}

                for tr in rows:
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 2:
                        label = tds[0].text.replace(":", "").strip()
                        value = tds[1].text.strip()
                        if label:
                            sub_data[label] = value

                if sub_data:
                    section_dict[sub_title] = sub_data

            if section_dict:
                details[section_title] = section_dict
            continue

        tables = panel.find_elements(By.CSS_SELECTOR, "table.posting-table")
        sec_data = {}

        for table in tables:
            rows = table.find_elements(By.TAG_NAME, "tr")
            for tr in rows:
                tds = tr.find_elements(By.TAG_NAME, "td")
                if len(tds) >= 2:
                    label = tds[0].text.replace(":", "").strip()
                    value = tds[1].text.strip()
                    if label and value:
                        if label in sec_data:
                            sec_data[label] += " || " + value
                        else:
                            sec_data[label] = value

        if sec_data:
            details[section_title] = sec_data

    return details


def click_next_page():
    try:
        next_btn = driver.find_element(By.ID, "table_id_next")
        if "disabled" in next_btn.get_attribute("class"):
            return False
        driver.execute_script("arguments[0].click();", next_btn)
        wait_for_table()
        return True
    except Exception:
        return False


while True:
    wait_for_table()

    rows = driver.find_elements(By.CSS_SELECTOR, "#table_id tbody tr")
    row_count = len(rows)
    print(f"[INFO] Rows on page: {row_count}")

    for i in range(row_count):
        wait_for_table()
        rows = driver.find_elements(By.CSS_SELECTOR, "#table_id tbody tr")
        row = rows[i]

        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 11:
            continue

        post_date = tds[0].text.strip()
        quest_number_txt = tds[1].text.strip()
        category_code = tds[2].text.strip()
        bid_request_name = tds[3].text.strip()
        bid_closing_date = tds[4].text.strip()
        city = tds[5].text.strip()
        county = tds[6].text.strip()
        state = tds[7].text.strip()
        owner = tds[8].text.strip()
        solicitor = tds[9].text.strip()
        posting_type = tds[10].text.strip()
        bid_award_type = tds[11].text.strip() if len(tds) > 11 else ""

        try:
            quest_link = tds[1].find_element(By.TAG_NAME, "a")
        except Exception:
            continue

        onclick_val = quest_link.get_attribute("onclick") or ""
        if "prevnext(" in onclick_val:
            quest_id = onclick_val.split("prevnext(")[1].split(")")[0].strip()
        else:
            quest_id = quest_number_txt

        record = {
            "post_date": post_date,
            "quest_number": quest_number_txt,
            "category_code": category_code,
            "bid_request_name": bid_request_name,
            "bid_closing_date": bid_closing_date,
            "city": city,
            "county": county,
            "state": state,
            "owner": owner,
            "solicitor": solicitor,
            "posting_type": posting_type,
            "bid_award_type": bid_award_type,
        }

        print(f"[DETAIL] Opening Quest #{quest_id} - {bid_request_name}")

        driver.execute_script(f"prevnext({quest_id});")

        record["details"] = scrape_detail_page()

        go_back_home()

        results.append(record)

    if not click_next_page():
        print("[INFO] No more pages.")
        break

with open("questcdn_el_dorado_full.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print("[DONE] Saved questcdn_el_dorado_full.json")
driver.quit()
