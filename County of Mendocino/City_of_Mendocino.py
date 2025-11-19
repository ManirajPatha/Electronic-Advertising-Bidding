# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import Select
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
# import json
# import time
# import re

# class PlanetBidsScraper:
#     def __init__(self, headless=True):
#         self.base_url = "https://vendors.planetbids.com/portal/45968/bo/bo-search"
        
#         # Setup Chrome options
#         chrome_options = Options()
#         if headless:
#             chrome_options.add_argument('--headless')
#         chrome_options.add_argument('--no-sandbox')
#         chrome_options.add_argument('--disable-dev-shm-usage')
#         chrome_options.add_argument('--disable-gpu')
#         chrome_options.add_argument('--window-size=1920,1080')
#         chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
#         self.driver = webdriver.Chrome(options=chrome_options)
#         self.wait = WebDriverWait(self.driver, 20)
    
#     def extract_text(self, element):
#         """Extract and clean text from element"""
#         if element:
#             return element.get_text(separator=' ', strip=True)
#         return ""
    
#     def parse_bid_detail_row(self, soup, title):
#         """Parse a specific bid detail row by title"""
#         rows = soup.find_all('div', class_='row')
#         for row in rows:
#             title_div = row.find('div', class_='bid-detail-item-title')
#             value_div = row.find('div', class_='bid-detail-item-value')
            
#             if title_div and value_div:
#                 row_title = self.extract_text(title_div)
#                 if title.lower() in row_title.lower():
#                     return self.extract_text(value_div)
#         return ""
    
#     def parse_categories(self, soup):
#         """Parse categories from bid detail page"""
#         categories = []
#         rows = soup.find_all('div', class_='row')
        
#         for row in rows:
#             title_div = row.find('div', class_='bid-detail-item-title')
#             if title_div and 'categories' in title_div.get_text(strip=True).lower():
#                 value_div = row.find('div', class_='bid-detail-item-value')
#                 if value_div:
#                     # Get all text, split by <br> tags
#                     for br in value_div.find_all('br'):
#                         br.replace_with('\n')
#                     text = value_div.get_text()
#                     cat_lines = [line.strip() for line in text.split('\n') if line.strip()]
#                     categories = cat_lines
        
#         return categories
    
#     def parse_contact_info(self, soup):
#         """Parse contact information"""
#         contact_info = {}
        
#         # Find Contact Info section
#         contact_text = self.parse_bid_detail_row(soup, 'Contact Info')
#         if contact_text:
#             contact_info['Contact Info'] = contact_text
        
#         bids_to = self.parse_bid_detail_row(soup, 'Bids to')
#         if bids_to:
#             contact_info['Bids to'] = bids_to
        
#         owners_agent = self.parse_bid_detail_row(soup, "Owner's Agent")
#         if owners_agent:
#             contact_info["Owner's Agent"] = owners_agent
        
#         return contact_info
    
#     def parse_description(self, soup):
#         """Parse description section"""
#         description = {}
        
#         scope = self.parse_bid_detail_row(soup, 'Scope of Services')
#         if scope:
#             description['Scope of Services'] = scope
        
#         other_details = self.parse_bid_detail_row(soup, 'Other Details')
#         if other_details:
#             description['Other Details'] = other_details
        
#         notes = self.parse_bid_detail_row(soup, 'Notes')
#         if notes:
#             description['Notes'] = notes
        
#         special_notices = self.parse_bid_detail_row(soup, 'Special Notices')
#         if special_notices:
#             description['Special Notices'] = special_notices
        
#         local_programs = self.parse_bid_detail_row(soup, 'Local Programs')
#         if local_programs:
#             description['Local Programs & Policies'] = local_programs
        
#         return description
    
#     def scrape_opportunity_details(self, row_element):
#         """Scrape details from a specific opportunity"""
#         try:
#             # Click on the row to open details
#             self.driver.execute_script("arguments[0].click();", row_element)
#             print("  Clicked on opportunity, waiting for details page...")
            
#             # Wait for the bid detail page to load
#             time.sleep(3)
#             self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'bid-detail-heading')))
            
#             html = self.driver.page_source
#             soup = BeautifulSoup(html, 'html.parser')
            
#             details = {}
            
#             # Extract basic bid details
#             details['Project Title'] = self.parse_bid_detail_row(soup, 'Project Title')
#             details['Invitation #'] = self.parse_bid_detail_row(soup, 'Invitation')
#             details['Bid Posting Date'] = self.parse_bid_detail_row(soup, 'Bid Posting Date')
#             details['Project Stage'] = self.parse_bid_detail_row(soup, 'Project Stage')
#             details['Bid Due Date'] = self.parse_bid_detail_row(soup, 'Bid Due Date')
#             details['Response Format'] = self.parse_bid_detail_row(soup, 'Response Format')
#             details['Project Type'] = self.parse_bid_detail_row(soup, 'Project Type')
#             details['Response Types'] = self.parse_bid_detail_row(soup, 'Response Types')
#             details['Type of Award'] = self.parse_bid_detail_row(soup, 'Type of Award')
            
#             # Parse categories
#             categories = self.parse_categories(soup)
#             if categories:
#                 details['Categories'] = categories
            
#             # License Requirements
#             license_req = self.parse_bid_detail_row(soup, 'License Requirements')
#             if license_req:
#                 details['License Requirements'] = license_req
            
#             # Department and Location
#             details['Department'] = self.parse_bid_detail_row(soup, 'Department')
#             details['Address'] = self.parse_bid_detail_row(soup, 'Address')
#             details['County'] = self.parse_bid_detail_row(soup, 'County')
            
#             # Additional details
#             details['Bid Valid'] = self.parse_bid_detail_row(soup, 'Bid Valid')
#             details['Liquidated Damages'] = self.parse_bid_detail_row(soup, 'Liquidated Damages')
#             details['Estimated Bid Value'] = self.parse_bid_detail_row(soup, 'Estimated Bid Value')
#             details['Start/Delivery Date'] = self.parse_bid_detail_row(soup, 'Start/Delivery Date')
#             details['Project Duration'] = self.parse_bid_detail_row(soup, 'Project Duration')
            
#             # Pre-bid meeting
#             details['Pre-Bid Meeting'] = self.parse_bid_detail_row(soup, 'Pre-Bid Meeting')
            
#             # Online Q&A
#             details['Online Q&A'] = self.parse_bid_detail_row(soup, 'Online Q&A')
            
#             # Contact Information
#             contact_info = self.parse_contact_info(soup)
#             if contact_info:
#                 details['Contact Information'] = contact_info
            
#             # Description
#             description = self.parse_description(soup)
#             if description:
#                 details['Description'] = description
            
#             # Remove empty fields
#             details = {k: v for k, v in details.items() if v}
            
#             return details
            
#         except Exception as e:
#             print(f"  Error scraping opportunity details: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def scrape_opportunities_table(self):
#         """Scrape the opportunities table"""
#         try:
#             print("Waiting for opportunities table to load...")
            
#             # Wait for table to load
#             self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.pb-datatable.data tbody')))
#             time.sleep(3)
            
#             html = self.driver.page_source
#             soup = BeautifulSoup(html, 'html.parser')
            
#             # Find the data table
#             table = soup.find('table', class_='pb-datatable data')
#             if not table:
#                 print("Could not find opportunities table")
#                 return []
            
#             tbody = table.find('tbody')
#             if not tbody:
#                 print("Could not find tbody")
#                 return []
            
#             rows = tbody.find_all('tr', role='row')
#             print(f"Found {len(rows)} opportunities")
            
#             opportunities = []
            
#             for idx, row in enumerate(rows):
#                 print(f"\nProcessing opportunity {idx + 1}/{len(rows)}")
                
#                 cells = row.find_all('td')
#                 if len(cells) < 7:
#                     continue
                
#                 # Extract summary data from table
#                 summary = {
#                     'Posted': self.extract_text(cells[0]),
#                     'Project Title': cells[1].get('title', self.extract_text(cells[1])),
#                     'Invitation #': cells[2].get('title', self.extract_text(cells[2])),
#                     'Due Date': cells[3].get('title', self.extract_text(cells[3])),
#                     'Remaining': self.extract_text(cells[4]),
#                     'Stage': self.extract_text(cells[5]),
#                     'Format': self.extract_text(cells[6])
#                 }
                
#                 print(f"  Title: {summary['Project Title']}")
                
#                 # Get the row element in Selenium to click on it
#                 row_attr = row.get('rowattribute')
#                 if row_attr:
#                     try:
#                         # Find the row in Selenium
#                         row_element = self.driver.find_element(By.CSS_SELECTOR, f'tr[rowattribute="{row_attr}"]')
                        
#                         # Scrape detailed information
#                         details = self.scrape_opportunity_details(row_element)
                        
#                         opportunity = {
#                             'summary': summary,
#                             'details': details if details else {}
#                         }
                        
#                         opportunities.append(opportunity)
                        
#                         # Go back to the search results
#                         print("  Navigating back to search results...")
#                         self.driver.back()
#                         time.sleep(3)
                        
#                         # Wait for table to reload
#                         self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.pb-datatable.data tbody')))
                        
#                     except Exception as e:
#                         print(f"  Error processing row: {e}")
#                         # Try to go back if we're on a detail page
#                         try:
#                             self.driver.back()
#                             time.sleep(2)
#                         except:
#                             pass
                
#                 # Add delay between opportunities
#                 time.sleep(2)
            
#             return opportunities
            
#         except Exception as e:
#             print(f"Error scraping opportunities table: {e}")
#             import traceback
#             traceback.print_exc()
#             return []
    
#     def scrape_bidding_stage(self):
#         """Main scraping function"""
#         print("Opening Planet Bids portal...")
        
#         try:
#             # Navigate to the page
#             self.driver.get(self.base_url)
#             time.sleep(3)
            
#             # Wait for the stage dropdown to be present
#             print("Waiting for page to load...")
#             self.wait.until(EC.presence_of_element_located((By.ID, 'stageId-field')))
            
#             # Select "Bidding" from dropdown
#             print("Selecting 'Bidding' stage...")
#             stage_dropdown = Select(self.driver.find_element(By.ID, 'stageId-field'))
#             stage_dropdown.select_by_value('3')  # Value 3 = Bidding
            
#             time.sleep(1)
            
#             # Click search button
#             print("Clicking search button...")
#             search_button = self.driver.find_element(By.CSS_SELECTOR, 'button.search-btn[type="submit"]')
#             search_button.click()
            
#             time.sleep(3)
            
#             # Scrape opportunities
#             opportunities = self.scrape_opportunities_table()
            
#             return {"opportunities": opportunities}
            
#         except Exception as e:
#             print(f"Error in scrape_bidding_stage: {e}")
#             import traceback
#             traceback.print_exc()
#             return {"opportunities": []}
    
#     def save_to_json(self, data, filename='mendocino_bids.json'):
#         """Save scraped data to JSON file"""
#         with open(filename, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)
#         print(f"\nData saved to {filename}")
    
#     def close(self):
#         """Close the browser"""
#         if self.driver:
#             self.driver.quit()

# def main():
#     scraper = None
#     try:
#         print("=" * 60)
#         print("Planet Bids - Mendocino County Scraper")
#         print("=" * 60)
        
#         scraper = PlanetBidsScraper(headless=False)  # Set to True for headless mode
        
#         # Scrape all bidding opportunities
#         data = scraper.scrape_bidding_stage()
        
#         # Save to JSON
#         scraper.save_to_json(data)
        
#         print("=" * 60)
#         print(f"Total opportunities scraped: {len(data['opportunities'])}")
#         print("Scraping completed successfully!")
#         print("=" * 60)
        
#     except Exception as e:
#         print(f"Error in main: {e}")
#         import traceback
#         traceback.print_exc()
#     finally:
#         if scraper:
#             print("\nClosing browser...")
#             scraper.close()

# if __name__ == "__main__":
#     main()


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import re

class PlanetBidsScraper:
    def __init__(self, headless=True):
        self.base_url = "https://vendors.planetbids.com/portal/45968/portal-home"
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
    
    def extract_text(self, element):
        """Extract and clean text from element"""
        if element:
            return element.get_text(separator=' ', strip=True)
        return ""
    
    def parse_bid_detail_row(self, soup, title):
        """Parse a specific bid detail row by title"""
        rows = soup.find_all('div', class_='row')
        for row in rows:
            title_div = row.find('div', class_='bid-detail-item-title')
            value_div = row.find('div', class_='bid-detail-item-value')
            
            if title_div and value_div:
                row_title = self.extract_text(title_div)
                if title.lower() in row_title.lower():
                    return self.extract_text(value_div)
        return ""
    
    def parse_categories(self, soup):
        """Parse categories from bid detail page"""
        categories = []
        rows = soup.find_all('div', class_='row')
        
        for row in rows:
            title_div = row.find('div', class_='bid-detail-item-title')
            if title_div and 'categories' in title_div.get_text(strip=True).lower():
                value_div = row.find('div', class_='bid-detail-item-value')
                if value_div:
                    
                    for br in value_div.find_all('br'):
                        br.replace_with('\n')
                    text = value_div.get_text()
                    cat_lines = [line.strip() for line in text.split('\n') if line.strip()]
                    categories = cat_lines
        
        return categories
    
    def parse_contact_info(self, soup):
        """Parse contact information"""
        contact_info = {}
        
        
        contact_text = self.parse_bid_detail_row(soup, 'Contact Info')
        if contact_text:
            contact_info['Contact Info'] = contact_text
        
        bids_to = self.parse_bid_detail_row(soup, 'Bids to')
        if bids_to:
            contact_info['Bids to'] = bids_to
        
        owners_agent = self.parse_bid_detail_row(soup, "Owner's Agent")
        if owners_agent:
            contact_info["Owner's Agent"] = owners_agent
        
        return contact_info
    
    def parse_description(self, soup):
        """Parse description section"""
        description = {}
        
        scope = self.parse_bid_detail_row(soup, 'Scope of Services')
        if scope:
            description['Scope of Services'] = scope
        
        other_details = self.parse_bid_detail_row(soup, 'Other Details')
        if other_details:
            description['Other Details'] = other_details
        
        notes = self.parse_bid_detail_row(soup, 'Notes')
        if notes:
            description['Notes'] = notes
        
        special_notices = self.parse_bid_detail_row(soup, 'Special Notices')
        if special_notices:
            description['Special Notices'] = special_notices
        
        local_programs = self.parse_bid_detail_row(soup, 'Local Programs')
        if local_programs:
            description['Local Programs & Policies'] = local_programs
        
        return description
    
    def scrape_opportunity_details(self, row_element):
        """Scrape details from a specific opportunity"""
        try:
            
            self.driver.execute_script("arguments[0].click();", row_element)
            
            
            time.sleep(3)
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'bid-detail-heading')))
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            details = {}
            
            
            details['Project Title'] = self.parse_bid_detail_row(soup, 'Project Title')
            details['Invitation #'] = self.parse_bid_detail_row(soup, 'Invitation')
            details['Bid Posting Date'] = self.parse_bid_detail_row(soup, 'Bid Posting Date')
            details['Project Stage'] = self.parse_bid_detail_row(soup, 'Project Stage')
            details['Bid Due Date'] = self.parse_bid_detail_row(soup, 'Bid Due Date')
            details['Response Format'] = self.parse_bid_detail_row(soup, 'Response Format')
            details['Project Type'] = self.parse_bid_detail_row(soup, 'Project Type')
            details['Response Types'] = self.parse_bid_detail_row(soup, 'Response Types')
            details['Type of Award'] = self.parse_bid_detail_row(soup, 'Type of Award')
            
            
            categories = self.parse_categories(soup)
            if categories:
                details['Categories'] = categories
            
            
            license_req = self.parse_bid_detail_row(soup, 'License Requirements')
            if license_req:
                details['License Requirements'] = license_req
            
            
            details['Department'] = self.parse_bid_detail_row(soup, 'Department')
            details['Address'] = self.parse_bid_detail_row(soup, 'Address')
            details['County'] = self.parse_bid_detail_row(soup, 'County')
            
            
            details['Bid Valid'] = self.parse_bid_detail_row(soup, 'Bid Valid')
            details['Liquidated Damages'] = self.parse_bid_detail_row(soup, 'Liquidated Damages')
            details['Estimated Bid Value'] = self.parse_bid_detail_row(soup, 'Estimated Bid Value')
            details['Start/Delivery Date'] = self.parse_bid_detail_row(soup, 'Start/Delivery Date')
            details['Project Duration'] = self.parse_bid_detail_row(soup, 'Project Duration')
            
            
            details['Pre-Bid Meeting'] = self.parse_bid_detail_row(soup, 'Pre-Bid Meeting')
            
            
            details['Online Q&A'] = self.parse_bid_detail_row(soup, 'Online Q&A')
            
            
            contact_info = self.parse_contact_info(soup)
            if contact_info:
                details['Contact Information'] = contact_info
            
            
            description = self.parse_description(soup)
            if description:
                details['Description'] = description
            
            
            details = {k: v for k, v in details.items() if v}
            
            return details
            
        except Exception as e:
            print(f"  Error scraping opportunity details: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_opportunities_table(self):
        """Scrape the opportunities table"""
        try:
            
            
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.pb-datatable.data tbody')))
            time.sleep(3)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
        
            table = soup.find('table', class_='pb-datatable data')
            if not table:
                print("Could not find opportunities table")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                print("Could not find tbody")
                return []
            
            rows = tbody.find_all('tr', role='row')
            print(f"Found {len(rows)} opportunities")
            
            opportunities = []
            
            for idx, row in enumerate(rows):
                
                cells = row.find_all('td')
                if len(cells) < 7:
                    continue
                
                
                summary = {
                    'Posted': self.extract_text(cells[0]),
                    'Project Title': cells[1].get('title', self.extract_text(cells[1])),
                    'Invitation #': cells[2].get('title', self.extract_text(cells[2])),
                    'Due Date': cells[3].get('title', self.extract_text(cells[3])),
                    'Remaining': self.extract_text(cells[4]),
                    'Stage': self.extract_text(cells[5]),
                    'Format': self.extract_text(cells[6])
                }
                
                
                row_attr = row.get('rowattribute')
                if row_attr:
                    try:
                        
                        row_element = self.driver.find_element(By.CSS_SELECTOR, f'tr[rowattribute="{row_attr}"]')
                        
                        
                        details = self.scrape_opportunity_details(row_element)
                        
                        opportunity = {
                            'summary': summary,
                            'details': details if details else {}
                        }
                        
                        opportunities.append(opportunity)
                        
                        
                        self.driver.back()
                        time.sleep(3)
                        
                        
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.pb-datatable.data tbody')))
                        
                    except Exception as e:
                        
                        try:
                            self.driver.back()
                            time.sleep(2)
                        except:
                            pass
                
                time.sleep(2)
            
            return opportunities
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []
    
    def navigate_to_bid_opportunities(self):
        """Navigate from portal home to bid opportunities search page"""
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/portal/45968/bo/bo-search"]')))
            
            
            bid_opp_button = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/portal/45968/bo/bo-search"]')
            bid_opp_button.click()
            
            time.sleep(3)
            
            
            self.wait.until(EC.presence_of_element_located((By.ID, 'stageId-field')))
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def scrape_bidding_stage(self):
        """Main scraping function"""
        try:
            if not self.navigate_to_bid_opportunities():
                return {"opportunities": []}
            
            
            
            stage_dropdown = Select(self.driver.find_element(By.ID, 'stageId-field'))
            stage_dropdown.select_by_value('3')  # Value 3 = Bidding
            
            time.sleep(1)
            
            
            search_button = self.driver.find_element(By.CSS_SELECTOR, 'button.search-btn[type="submit"]')
            search_button.click()
            
            time.sleep(3)
            
            
            opportunities = self.scrape_opportunities_table()
            
            return {"opportunities": opportunities}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"opportunities": []}
    
    def save_to_json(self, data, filename='mendocino_bids.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    print("=" * 60)
    print("Planet Bids - Mendocino County Scraper")
    print("=" * 60)
    
    try:
        import selenium    
    except ImportError as e:
        return
    
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        return
    
    
    try:
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.service import utils
    except ImportError as e:
        print(f"✗ Chrome WebDriver issue: {e}")
    
    print("\nStarting scraper...")
    scraper = None
    try:
        scraper = PlanetBidsScraper(headless=False)  
        
        data = scraper.scrape_bidding_stage()
        
        scraper.save_to_json(data)
        
        print("=" * 60)
        print(f"Total opportunities scraped: {len(data['opportunities'])}")
        print("Scraping completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            print("\nClosing browser...")
            scraper.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()