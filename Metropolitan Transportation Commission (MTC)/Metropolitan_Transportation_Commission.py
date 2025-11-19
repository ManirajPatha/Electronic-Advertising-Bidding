from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json

url = "https://mtc.bonfirehub.com/portal/?tab=openOpportunities"

driver = webdriver.Chrome()
driver.maximize_window()
driver.get(url)

wait = WebDriverWait(driver, 30)

print("Checking for CAPTCHA... Please complete if asked.")
time.sleep(5)

print("Waiting for page to load completely...")
try:
    wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
    print("Page loaded successfully!")
except:
    print("Please complete the CAPTCHA if present, then press Enter to continue...")
    input("Press Enter after completing CAPTCHA: ")

time.sleep(3)

results = []
processed_refs = set()


def check_for_captcha():
    """Check if CAPTCHA is present and wait for user to complete it."""
    try:
        captcha_indicators = [
            "//iframe[contains(@src, 'captcha')]",
            "//div[contains(@class, 'captcha')]",
            "//*[contains(@id, 'captcha')]",
            "//iframe[contains(@title, 'reCAPTCHA')]"
        ]
        
        for indicator in captcha_indicators:
            try:
                driver.find_element(By.XPATH, indicator)
                print("CAPTCHA detected! Please complete it...")
                input("Press Enter after completing CAPTCHA: ")
                time.sleep(2)
                return True
            except NoSuchElementException:
                continue
        
        page_source = driver.page_source.lower()
        if 'captcha' in page_source or 'recaptcha' in page_source:
            print("Possible CAPTCHA detected! Please verify and complete if present...")
            input("Press Enter to continue: ")
            time.sleep(2)
            return True
            
    except Exception as e:
        print(f"Error checking for CAPTCHA: {e}")
    
    return False


def scrape_document_takers():
    """Scrapes Document Takers table."""
    takers = []
    try:
        doc_takers_section = driver.find_element(By.XPATH, "//h3[contains(text(), 'Document Takers')]")
        print("Found Document Takers section")

        time.sleep(2)
        
        table = driver.find_element(By.ID, "publicDocumentTakersTable")
        rows = table.find_elements(By.XPATH, ".//tbody//tr[not(contains(@class,'dataTables_empty'))]")
        
        print(f"Found {len(rows)} document takers")
        
        for row in rows:
            try:
                vendor = row.find_element(By.XPATH, ".//td[1]").text.strip()
                files = row.find_element(By.XPATH, ".//td[2]").text.strip()
                
                takers.append({
                    "vendor": vendor,
                    "num_files": files
                })
            except Exception as e:
                print(f"Error parsing document taker row: {e}")
                continue
                
    except NoSuchElementException:
        print("No Document Takers section found")
    except Exception as e:
        print(f"Error scraping document takers: {e}")

    return takers


def scrape_interested_contractors():
    """Scrapes Prime/General Contractors and Subcontractors."""
    contractors = {
        "prime_contractors": [],
        "subcontractors": []
    }
    
    try:
        contractors_section = driver.find_element(By.XPATH, "//h3[contains(text(), 'Interested Contractors')]")
        print("Found Interested Contractors section")
        time.sleep(1)
        
        try:
            prime_table = driver.find_element(By.ID, "primeContractorsTable")
            prime_rows = prime_table.find_elements(By.XPATH, ".//tbody//tr[not(contains(@class,'dataTables_empty'))]")
            print(f"Found {len(prime_rows)} prime contractors")
            
            for row in prime_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    contractors["prime_contractors"].append({
                        "vendor": cells[0].text.strip(),
                        "contact": cells[1].text.strip(),
                        "email": cells[2].text.strip(),
                        "phone": cells[3].text.strip(),
                        "subcontract_services": cells[4].text.strip()
                    })
                except Exception as e:
                    print(f"Error parsing prime contractor row: {e}")
                    continue
        except:
            print("No prime contractors data")
        
        try:
            sub_tab = driver.find_element(By.XPATH, "//a[@href='#subContractorsContainer']")
            driver.execute_script("arguments[0].click();", sub_tab)
            time.sleep(2)
            
            sub_table = driver.find_element(By.ID, "subContractorsTable")
            sub_rows = sub_table.find_elements(By.XPATH, ".//tbody//tr[not(contains(@class,'dataTables_empty'))]")
            
            print(f"Found {len(sub_rows)} subcontractors")
            
            for row in sub_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    contractors["subcontractors"].append({
                        "vendor": cells[0].text.strip(),
                        "contact": cells[1].text.strip(),
                        "email": cells[2].text.strip(),
                        "phone": cells[3].text.strip(),
                        "subcontract_services": cells[4].text.strip()
                    })
                except Exception as e:
                    print(f"Error parsing subcontractor row: {e}")
                    continue
        except:
            print("No subcontractors data")
            
    except NoSuchElementException:
        print("No Interested Contractors section found")
    except Exception as e:
        print(f"Error scraping interested contractors: {e}")
    
    return contractors


def scrape_opportunity_details(detail_url):
    """Opens detail page and scrapes all information."""
    driver.get(detail_url)
    time.sleep(3)
    
    check_for_captcha()
    
    details = {}
    
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "projectDetailSection")))
        sections = driver.find_elements(By.CLASS_NAME, "projectDetailSection")
        
        for section in sections:
            text = section.text.strip()
            
            if "Project:" in text:
                details["project"] = text.replace("Project:", "").strip()
            elif "Ref. #:" in text:
                details["ref_number"] = text.replace("Ref. #:", "").strip()
            elif "Type:" in text:
                details["type"] = text.replace("Type:", "").strip()
            elif "Status:" in text:
                details["status"] = text.replace("Status:", "").strip()
            elif "Open Date:" in text:
                details["open_date"] = text.replace("Open Date:", "").strip()
            elif "Questions Due Date:" in text:
                details["questions_due_date"] = text.replace("Questions Due Date:", "").strip()
            elif "Contact Information:" in text:
                details["contact_information"] = text.replace("Contact Information:", "").strip()
            elif "Close Date:" in text:
                details["close_date"] = text.replace("Close Date:", "").strip()
            elif "Days Left:" in text:
                details["days_left"] = text.replace("Days Left:", "").strip()
        
        try:
            description_elem = driver.find_element(By.XPATH, "//div[@class='bfMarkdown markdown_formatted']")
            details["project_description"] = description_elem.text.strip()
        except:
            details["project_description"] = ""
        
        details["document_takers"] = scrape_document_takers()
        
        contractors = scrape_interested_contractors()
        details["prime_contractors"] = contractors["prime_contractors"]
        details["subcontractors"] = contractors["subcontractors"]
        
    except TimeoutException:
        print("Timeout loading opportunity details. Checking for CAPTCHA...")
        if check_for_captcha():
            return scrape_opportunity_details(detail_url)
    except Exception as e:
        print(f"Error scraping opportunity details: {e}")
    
    return details


def get_row_count():
    """Get the current number of rows in the table."""
    try:
        table = driver.find_element(By.ID, "DataTables_Table_0")
        rows = table.find_elements(By.XPATH, ".//tbody//tr[contains(@class,'odd') or contains(@class,'even')]")
        return len(rows)
    except:
        return 0


def get_row_data(row_index):
    """Get data from a specific row by index."""
    try:
        table = wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
        time.sleep(1)
        
        rows = table.find_elements(By.XPATH, ".//tbody//tr[contains(@class,'odd') or contains(@class,'even')]")
        
        if row_index >= len(rows):
            return None
        
        row = rows[row_index]
        
        status = row.find_element(By.XPATH, ".//td[1]//div[contains(@class,'statusTag')]").text.strip()
        ref_number = row.find_element(By.XPATH, ".//td[2]").text.strip()
        if not ref_number or ref_number == "N/A":
            ref_number = f"ROW-{row_index+1}"
        project_name = row.find_element(By.XPATH, ".//td[3]//b").text.strip()
        close_date = row.find_element(By.XPATH, ".//td[4]").text.strip()
        days_left = row.find_element(By.XPATH, ".//td[5]//div").text.strip()
        
        view_button = row.find_element(By.XPATH, ".//td[6]//a")
        detail_url = view_button.get_attribute("href")
        
        return {
            "status": status,
            "ref_number": ref_number,
            "project_name": project_name,
            "close_date": close_date,
            "days_left": days_left,
            "detail_url": detail_url
        }
    except Exception as e:
        print(f"Error getting row data: {e}")
        return None


def scrape_opportunities_table():
    """Scrapes the main opportunities table."""
    
    try:
        table = wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
    except TimeoutException:
        print("Table not found. Please complete CAPTCHA if present.")
        input("Press Enter after completing CAPTCHA: ")
        table = wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
    
    time.sleep(2)
    
    total_rows = get_row_count()
    print(f"\nFound {total_rows} opportunities to scrape\n")
    
    row_index = 0
    while row_index < total_rows:
        try:
            row_data = get_row_data(row_index)
            
            if row_data is None:
                print(f"Could not get data for row {row_index + 1}")
                row_index += 1
                continue
            
            if row_data["ref_number"] in processed_refs:
                print(f"[{row_index + 1}/{total_rows}] Skipping already processed: {row_data['ref_number']}")
                row_index += 1
                continue
            
            print(f"[{row_index + 1}/{total_rows}] Processing: {row_data['ref_number']} - {row_data['project_name'][:50]}...")
            
            opportunity_details = scrape_opportunity_details(row_data["detail_url"])
            opportunity = {
                **row_data,
                **opportunity_details
            }
            
            results.append(opportunity)
            processed_refs.add(row_data["ref_number"])
            
            print(f"Successfully scraped {row_data['ref_number']}")
            
            driver.back()
            time.sleep(2)
            
            check_for_captcha()
            
            wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
            time.sleep(1)
            
            row_index += 1
            
        except Exception as e:
            print(f"Error processing row {row_index + 1}: {e}")
            
            try:
                driver.get(url)
                time.sleep(3)
                wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
            except:
                print("Could not return to main page. Exiting.")
                break
            
            row_index += 1
            continue


print("\nStarting MTC Bonfire Hub scraper...")
scrape_opportunities_table()

driver.quit()

output_file = "Metropolitan_bonfire_opportunities.json"
with open(output_file, "w", encoding='utf-8') as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"Total opportunities scraped: {len(results)}")
print(f"Data saved to: {output_file}")