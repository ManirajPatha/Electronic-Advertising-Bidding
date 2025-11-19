from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

class PlacerBidsScraper:
    def __init__(self, headless=True):
        self.base_url = "https://placer.bidsandtenders.net"
        self.main_url = f"{self.base_url}/Module/Tenders/en"
        
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
    
    def parse_categories(self, soup):
        """Parse categories from the detail page"""
        categories = []
        cat_div = soup.find('div', {'id': 'divCat'})
        
        if cat_div:
            tree = cat_div.find('ul', class_='tree')
            if tree:
                for main_li in tree.find_all('li', recursive=False):
                    
                    category_text = ""
                    for content in main_li.contents:
                        if isinstance(content, str):
                            category_text = content.strip()
                            break
                    
                    if not category_text:
                        category_text = main_li.get_text(strip=True).split('\n')[0]
                    
                    
                    sub_ul = main_li.find('ul')
                    if sub_ul:
                        subcategories = [sub_li.get_text(strip=True) for sub_li in sub_ul.find_all('li')]
                        if subcategories:
                            categories.append({
                                "category": category_text,
                                "subcategories": subcategories
                            })
                        else:
                            categories.append({"category": category_text})
                    else:
                        categories.append({"category": category_text})
        
        return categories
    
    def parse_contact_info(self, soup):
        """Parse contact information from the detail page"""
        contact_name = ""
        contact_email = ""
        
        
        
        name_cell = soup.find('div', class_='x-grid3-col-FullName')
        email_cell = soup.find('div', class_='x-grid3-col-Email')
        
        if name_cell:
            contact_name = name_cell.get_text(strip=True)
        if email_cell:
            email_link = email_cell.find('a')
            if email_link:
                contact_email = email_link.get_text(strip=True)
        
        
        if not contact_name:
            contact_tbody = soup.find_all('tbody')
            for tbody in contact_tbody:
                if 'x-grid3-body' in str(tbody.get('class', [])):
                    contact_row = tbody.find('tr')
                    if contact_row:
                        cells = contact_row.find_all('td')
                        if len(cells) >= 2:
                            contact_name = cells[0].get_text(strip=True)
                            email_link = cells[1].find('a')
                            if email_link:
                                contact_email = email_link.get_text(strip=True)
                            break
        
        return contact_name, contact_email
    
    def scrape_opportunity_details(self, detail_url):
        """Scrape details from an opportunity detail page"""
        
        try:
            self.driver.get(detail_url)
            time.sleep(3)  
            
            
            try:
                cat_link = self.driver.find_element(By.ID, 'lnkCat')
                if cat_link:
                    self.driver.execute_script("arguments[0].click();", cat_link)
                    time.sleep(1)
            except:
                pass
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            details = {}
            
            
            detail_tbody = soup.find('tbody')
            
            if detail_tbody:
                rows = detail_tbody.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    
                    if th and td:
                        key = th.get_text(strip=True).replace(':', '').replace('\xa0', ' ').strip()
                        
                        
                        if 'Categories' in key:
                            continue
                        
                        
                        if 'Description' in key:
                            value = td.get_text(separator=' ', strip=True)
                        else:
                            
                            strong = td.find('strong')
                            if strong:
                                value = strong.get_text(strip=True)
                            else:
                                value = td.get_text(strip=True)
                        
                        if value:
                            details[key] = value
            
            
            categories = self.parse_categories(soup)
            if categories:
                details['Categories'] = categories
            
            
            contact_name, contact_email = self.parse_contact_info(soup)
            if contact_name:
                details['Contact Name'] = contact_name
            if contact_email:
                details['Contact Email'] = contact_email
            
            return details
            
        except Exception as e:
            print(f"  Error scraping details: {e}")
            return None
    
    def scrape_opportunities(self):
        """Scrape all opportunities from the main page"""
        print("Fetching main page...")
        
        try:
            self.driver.get(self.main_url)
            
            
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody[data-container="true"]')))
            time.sleep(3)  
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            
            tbody = soup.find('tbody', {'data-container': 'true'})
            
            if not tbody:
                print("Could not find opportunities table")
                return {"opportunities": []}
            
            opportunities = []
            rows = tbody.find_all('tr', recursive=False)
            
            print(f"Found {len(rows)} rows in the table")
            
            i = 0
            while i < len(rows):
                row = rows[i]
                
                
                cells = row.find_all('td', recursive=False)
                
                if len(cells) == 4:
                    
                    title_cell = cells[0].find('strong')
                    title = title_cell.get_text(strip=True) if title_cell else cells[0].get_text(strip=True)
                    status = cells[1].get_text(strip=True)
                    closing_date = cells[2].get_text(strip=True)
                    days_left = cells[3].get_text(strip=True)
                    
                    
                    detail_url = None
                    if i + 1 < len(rows):
                        next_row = rows[i + 1]
                        detail_link = next_row.find('a', href=lambda x: x and '/Tender/Detail/' in x)
                        if detail_link:
                            detail_url = self.base_url + detail_link['href']
                    
                    opportunity = {
                        "summary": {
                            "title": title,
                            "status": status,
                            "closing_date": closing_date,
                            "days_left": days_left,
                            "details_url": detail_url
                        }
                    }
                    
                    
                    if detail_url:
                        details = self.scrape_opportunity_details(detail_url)
                        if details:
                            opportunity["details"] = details
                        
                        time.sleep(2)  
                    opportunities.append(opportunity)
                    
                    
                    i += 2
                else:
                    i += 1
            
            return {"opportunities": opportunities}
            
        except Exception as e:
            print(f"Error scraping opportunities: {e}")
            import traceback
            traceback.print_exc()
            return {"opportunities": []}
    
    def save_to_json(self, data, filename='placer_bids.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        scraper = PlacerBidsScraper(headless=False)  
        print("Starting Placer County Bids Scraper...")
        print("=" * 60)
        
        
        data = scraper.scrape_opportunities()
        
        
        scraper.save_to_json(data)
        
        print("=" * 60)
        print(f"Total opportunities scraped: {len(data['opportunities'])}")
        print("Scraping completed!")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()