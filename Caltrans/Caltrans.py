from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime


class CalTransScraper:
    def __init__(self):
        """Initialize the scraper with Chrome webdriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "https://ppmoe.dot.ca.gov"
        
    def scrape_bid_items_table(self):
        """Scrape the bid items table"""
        try:
            bid_items_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "bidItemsContainer"))
            )
            bid_items_btn.click()
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'table table-bordered'})
            
            if not table:
                return []
            
            items = []
            rows = table.find('tbody').find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    item = {
                        'item_no': cols[0].get_text(strip=True),
                        'item_code': cols[1].get_text(strip=True),
                        'description': cols[2].get_text(strip=True),
                        'unit_of_measure': cols[3].get_text(strip=True),
                        'estimated_quantity': cols[4].get_text(strip=True)
                    }
                    items.append(item)
            
            return items
        except Exception as e:
            print(f"Error scraping bid items: {e}")
            return []
    
    def scrape_bidder_inquiries(self):
        """Scrape bidder inquiries section"""
        try:
            inquiries_btn = self.driver.find_element(By.ID, "bidInquiriesContainer")
            inquiries_btn.click()
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            inquiries_div = soup.find('div', {'id': 'bidInquiries'})
            
            if not inquiries_div:
                return []
            
            inquiries = []
            inquiry_blocks = inquiries_div.find_all('div', {'ng-repeat': 'item in c.data.list track by item.sys_id'})
            
            for block in inquiry_blocks:
                inquiry_text = block.find('p')
                if inquiry_text:
                    strong_tag = inquiry_text.find('strong')
                    inquiry_title = strong_tag.get_text(strip=True) if strong_tag else ""
                    
                    question = inquiry_text.get_text(strip=True)
                    
                    em_tag = inquiry_text.find('em')
                    submitted_date = em_tag.get_text(strip=True) if em_tag else ""
                    
                    responses = []
                    response_divs = block.find_all('div', {'ng-repeat': 'response in item.responses'})
                    for resp_div in response_divs:
                        resp_text = resp_div.get_text(strip=True)
                        responses.append(resp_text)
                    
                    inquiries.append({
                        'inquiry_title': inquiry_title,
                        'question': question,
                        'submitted_date': submitted_date,
                        'responses': responses
                    })
            
            return inquiries
        except Exception as e:
            print(f"Error scraping bidder inquiries: {e}")
            return []
    
    def scrape_subcontractor_optins(self):
        """Scrape subcontractor opt-ins"""
        try:
            optins_btn = self.driver.find_element(By.ID, "subOptInsContainer")
            optins_btn.click()
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            optins_div = soup.find('div', {'id': 'subOptIns'})
            
            if not optins_div:
                return []
            
            optins = []
            optin_blocks = optins_div.find_all('div', {'ng-repeat': 'item in c.data.list track by item.sys_id'})
            
            for block in optin_blocks:
                contractor = self._extract_field(block, 'Contractor:')
                contact = self._extract_field(block, 'Contact:')
                address = self._extract_field(block, 'Address:')
                phone = self._extract_field(block, 'Phone:')
                fax = self._extract_field(block, 'Fax:')
                email_tag = block.find('a', href=lambda x: x and 'mailto:' in x)
                email = email_tag.get_text(strip=True) if email_tag else "N/A"
                disadvantaged = self._extract_field(block, 'Disadvantaged status:')
                services = self._extract_field(block, 'Services:')
                
                optins.append({
                    'contractor': contractor,
                    'contact': contact,
                    'address': address,
                    'phone': phone,
                    'fax': fax,
                    'email': email,
                    'disadvantaged_status': disadvantaged,
                    'services': services
                })
            
            return optins
        except Exception as e:
            print(f"Error scraping subcontractor opt-ins: {e}")
            return []
    
    def scrape_prime_advertising(self):
        """Scrape Prime: Advertising for Help section"""
        try:
            prime_btn = self.driver.find_element(By.ID, "primeAdsContainer")
            prime_btn.click()
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            prime_div = soup.find('div', {'id': 'primeAds'})
            
            if not prime_div:
                return []
            
            primes = []
            prime_blocks = prime_div.find_all('div', {'ng-repeat': 'item in c.data.list track by item.sys_id'})
            
            for block in prime_blocks:
                contractor = self._extract_field(block, 'Contractor:')
                contact = self._extract_field(block, 'Contact:')
                address = self._extract_field(block, 'Address:')
                phone = self._extract_field(block, 'Phone:')
                fax = self._extract_field(block, 'Fax:')
                email_tag = block.find('a', href=lambda x: x and 'mailto:' in x)
                email = email_tag.get_text(strip=True) if email_tag else "N/A"
                services = self._extract_field(block, 'Services needed:')
                requirements = self._extract_field(block, 'Requirements:')
                date_posted = self._extract_field(block, 'Date posted:')
                
                primes.append({
                    'contractor': contractor,
                    'contact': contact,
                    'address': address,
                    'phone': phone,
                    'fax': fax,
                    'email': email,
                    'services_needed': services,
                    'requirements': requirements,
                    'date_posted': date_posted
                })
            
            return primes
        except Exception as e:
            print(f"Error scraping prime advertising: {e}")
            return []
    
    def scrape_plan_holders(self):
        """Scrape plan holders section"""
        try:
            holders_btn = self.driver.find_element(By.ID, "planHoldersContainer")
            holders_btn.click()
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            holders_div = soup.find('div', {'id': 'planHolders'})
            
            if not holders_div:
                return []
            
            holders = []
            holder_blocks = holders_div.find_all('div', {'ng-repeat': 'item in c.data.list track by item.sys_id'})
            
            for block in holder_blocks:
                contractor = self._extract_field(block, 'Contractor:')
                contact = self._extract_field(block, 'Contact:')
                address = self._extract_field(block, 'Address:')
                phone = self._extract_field(block, 'Phone:')
                fax = self._extract_field(block, 'Fax:')
                email_tag = block.find('a', href=lambda x: x and 'mailto:' in x)
                email = email_tag.get_text(strip=True) if email_tag else "N/A"
                date_downloaded = self._extract_field(block, 'Date Downloaded:')
                
                holders.append({
                    'contractor': contractor,
                    'contact': contact,
                    'address': address,
                    'phone': phone,
                    'fax': fax,
                    'email': email,
                    'date_downloaded': date_downloaded
                })
            
            return holders
        except Exception as e:
            print(f"Error scraping plan holders: {e}")
            return []
    
    def _extract_field(self, block, field_name):
        """Helper method to extract field values"""
        text = block.get_text()
        if field_name in text:
            start = text.find(field_name) + len(field_name)
            end = text.find('\n', start) if '\n' in text[start:] else len(text)
            return text[start:end].strip()
        return "N/A"
    
    def scrape_opportunity_details(self, opportunity_url):
        """Scrape details from a single opportunity page"""
        try:
            self.driver.get(opportunity_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            name_div = soup.find('div', {'class': 'col-md-11'})
            name = name_div.find('h3').get_text(strip=True) if name_div and name_div.find('h3') else "N/A"
            
            details_p = soup.find('p', text=lambda t: t and 'Date Advertised' in str(t))
            date_advertised = ""
            bids_open = ""
            estimate = ""
            
            if details_p:
                text = details_p.get_text()
                if 'Date Advertised' in text:
                    date_advertised = text.split('Date Advertised')[1].split('Bids')[0].strip()
                if 'Bids Open' in text:
                    bids_open = text.split('Bids Open')[1].split('Estimate')[0].strip()
                if 'Estimate:' in text:
                    estimate = text.split('Estimate:')[1].strip()
            
            description_p = soup.find('p', text=lambda t: t and 'COUNTY' in str(t))
            description = description_p.get_text(strip=True) if description_p else "N/A"
            
            license_p = soup.find('p', text=lambda t: t and 'Class A license' in str(t) or t and 'Class C license' in str(t))
            license_info = license_p.get_text(strip=True) if license_p else "N/A"
            
            bid_items = self.scrape_bid_items_table()
            bidder_inquiries = self.scrape_bidder_inquiries()
            subcontractor_optins = self.scrape_subcontractor_optins()
            prime_advertising = self.scrape_prime_advertising()
            plan_holders = self.scrape_plan_holders()
            
            opportunity_data = {
                'url': opportunity_url,
                'name': name,
                'date_advertised': date_advertised,
                'bids_open': bids_open,
                'estimate': estimate,
                'description': description,
                'license_requirements': license_info,
                'bid_items': bid_items,
                'bidder_inquiries': bidder_inquiries,
                'subcontractor_optins': subcontractor_optins,
                'prime_advertising': prime_advertising,
                'plan_holders': plan_holders,
            }
            
            return opportunity_data
            
        except Exception as e:
            print(f"Error scraping opportunity details: {e}")
            return None
    
    def scrape_all_opportunities(self):
        """Main method to scrape all opportunities from the listing page"""
        try:
            url = "https://ppmoe.dot.ca.gov/cc?id=cc_advertisement"
            self.driver.get(url)
            time.sleep(3)
            
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "h4"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            opportunity_links = []
            opportunities_divs = soup.find_all('div', {'ng-switch-default': ''})
            
            for div in opportunities_divs:
                span = div.find('span', {'class': 'h4'})
                if span:
                    parent = div.find_parent('a')
                    if parent and parent.get('href'):
                        full_url = self.base_url + parent['href']
                        opportunity_links.append({
                            'title': span.get_text(strip=True),
                            'url': full_url
                        })
            
            print(f"Found {len(opportunity_links)} opportunities")
            
            all_opportunities = []
            for i, opp in enumerate(opportunity_links, 1):
                print(f"Scraping opportunity {i}/{len(opportunity_links)}: {opp['title']}")
                details = self.scrape_opportunity_details(opp['url'])
                if details:
                    all_opportunities.append(details)
                time.sleep(2)
            
            return all_opportunities
            
        except Exception as e:
            print(f"Error scraping opportunities list: {e}")
            return []
    
    def save_to_json(self, data, filename='caltrans_opportunities.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()


def main():
    """Main execution function"""
    scraper = CalTransScraper()
    
    try:
        print("Starting CalTrans Contractor's Corner scraper...")
        opportunities = scraper.scrape_all_opportunities()
        
        scraper.save_to_json(opportunities)
        print("\nScraping completed successfully!")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()