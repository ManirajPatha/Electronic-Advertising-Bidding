from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

url = "https://biddingo.com/sanjose"

driver = webdriver.Chrome()
driver.maximize_window()
driver.get(url)

wait = WebDriverWait(driver, 20)
time.sleep(3)

try:
    close_buttons = driver.find_elements(By.XPATH, "//button[contains(@class,'close') or contains(@aria-label,'Close')]")
    for btn in close_buttons:
        try:
            btn.click()
            time.sleep(1)
        except:
            pass
except:
    pass


try:
    type_dropdown = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'mat-select-trigger')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", type_dropdown)
    time.sleep(1)
    
    try:
        type_dropdown.click()
    except:
        driver.execute_script("arguments[0].click();", type_dropdown)
    
    time.sleep(1)
    
    posted_date_option = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Posted Date')]"))
    )
    posted_date_option.click()
    
    time.sleep(1)
    
    search_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Search')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_btn)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", search_btn)
    time.sleep(3)
    
except Exception as e:
    print(f"Error during filtering: {e}")
    print("Continuing without filter...")

results = []


def scrape_document_takers(detail_url):
    """
    Opens detail page → Clicks Document Takers → Scrapes table.
    Returns list of entries.
    """
    driver.get(detail_url)
    time.sleep(2)

    try:
        doc_takers_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//h5[contains(., 'Document Takers')]"))
        )

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", doc_takers_btn)
        time.sleep(1)
        
        driver.execute_script("arguments[0].click();", doc_takers_btn)
        time.sleep(2)
        
    except Exception as e:
        print(f"Could not click Document Takers: {e}")
        return []

    try:
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//table//tr[contains(@class,'mat-row')]"))
        )
    except:
        print("No document takers table found")
        return []

    time.sleep(1)

    table_rows = driver.find_elements(By.XPATH, "//table//tr[contains(@class,'mat-row')]")

    takers = []

    for tr in table_rows:
        try:
            company = tr.find_element(By.XPATH, ".//td[contains(@class,'cdk-column-company')]//h5").text.strip()
        except:
            company = ""

        try:
            address = tr.find_element(By.XPATH, ".//td[contains(@class,'cdk-column-address')]//p").text.strip()
        except:
            address = ""

        try:
            phone = tr.find_element(By.XPATH, ".//td[contains(@class,'cdk-column-telephone')]//p").text.strip()
        except:
            phone = ""

        try:
            site_meeting = tr.find_element(By.XPATH, ".//td[contains(@class,'cdk-column-sitemeeting')]//p").text.strip()
        except:
            site_meeting = ""

        if company:
            takers.append({
                "company": company,
                "address": address,
                "phone": phone,
                "site_meeting": site_meeting
            })

    print(f"Found {len(takers)} document takers")
    return takers


def scrape_current_page():
    """Scrapes open bids + goes inside each detail page."""
    rows = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//table//tr[contains(@class,'mat-row')]"))
    )

    for row in rows:
        try:
            status = row.find_element(By.XPATH, ".//td[contains(@class,'mat-column-status')]").text.strip()
            if status != "Open for Bidding":
                continue

            solicitation_number = row.find_element(By.XPATH, ".//td[contains(@class,'tenderNumber')]").text.strip()
            solicitation_name = row.find_element(By.XPATH, ".//td[contains(@class,'tenderName')]").text.strip()
            closing_date = row.find_element(By.XPATH, ".//td[contains(@class,'tenderClosingDate')]").text.strip()
            posted_date = row.find_element(By.XPATH, ".//td[contains(@class,'publishedDate')]").text.strip()
            days_left = row.find_element(By.XPATH, ".//td[contains(@class,'dayLeft')]").text.strip()

            detail_url = row.find_element(By.XPATH, ".//td[contains(@class,'tenderNumber')]//a").get_attribute("href")
            print(f"Opening detail page: {solicitation_number}")
            doc_takers = scrape_document_takers(detail_url)

            results.append({
                "solicitation_number": solicitation_number,
                "solicitation_name": solicitation_name,
                "closing_date": closing_date,
                "posted_date": posted_date,
                "days_left": days_left,
                "status": status,
                "detail_url": detail_url,
                "document_takers": doc_takers
            })

            driver.back()
            time.sleep(2)

        except Exception as e:
            print("Row skipped:", e)

page_number = 1

while True:
    print(f"\nScraping page {page_number} ...")
    scrape_current_page()

    try:
        next_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@class,'mat-paginator-navigation-next')]")
            )
        )

        if next_button.get_attribute("disabled") == "true":
            print("\nNo more pages.")
            break

        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(2)
        page_number += 1

    except Exception:
        print("\nPagination ended.")
        break

driver.quit()

with open("City_of_San_Jose.json", "w") as f:
    json.dump(results, f, indent=4)

print("\nScraping complete!")
print("Total records:", len(results))