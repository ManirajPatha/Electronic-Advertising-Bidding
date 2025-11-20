from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import re
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
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
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
            inquiry_blocks = inquiries_div.find_all('div', recursive=True)
            
            for block in inquiry_blocks:
                if block.get('ng-repeat') and 'item in c.data.list' in str(block.get('ng-repeat')):
                    inquiry_text = block.find('p')
                    if inquiry_text:
                        strong_tag = inquiry_text.find('strong')
                        inquiry_title = strong_tag.get_text(strip=True) if strong_tag else ""
                        
                        question = inquiry_text.get_text(strip=True)
                        
                        em_tag = inquiry_text.find('em')
                        submitted_date = em_tag.get_text(strip=True) if em_tag else ""
                        
                        responses = []
                        response_divs = block.find_all('div')
                        for resp_div in response_divs:
                            if resp_div.get('ng-repeat') and 'response in item.responses' in str(resp_div.get('ng-repeat')):
                                resp_text = resp_div.get_text(strip=True)
                                if resp_text:
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
            optin_blocks = optins_div.find_all('div', recursive=True)
            
            for block in optin_blocks:
                if block.get('ng-repeat') and 'item in c.data.list' in str(block.get('ng-repeat')):
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
            prime_blocks = prime_div.find_all('div', recursive=True)
            
            for block in prime_blocks:
                if block.get('ng-repeat') and 'item in c.data.list' in str(block.get('ng-repeat')):
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
            holder_blocks = holders_div.find_all('div', recursive=True)
            
            for block in holder_blocks:
                if block.get('ng-repeat') and 'item in c.data.list' in str(block.get('ng-repeat')):
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
            value = text[start:end].strip()
            for next_field in ['Contractor:', 'Contact:', 'Address:', 'Phone:', 'Fax:', 'Email:', 
                              'Disadvantaged status:', 'Services:', 'Services needed:', 
                              'Requirements:', 'Date posted:', 'Date Downloaded:']:
                if next_field in value:
                    value = value[:value.find(next_field)].strip()
            return value
        return "N/A"
    
    def scrape_opportunity_details(self, opportunity_url):
        """Scrape details from a single opportunity page"""
        try:
            self.driver.get(opportunity_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            name_div = soup.find('div', {'class': 'col-md-11'})
            name = name_div.find('h3').get_text(strip=True) if name_div and name_div.find('h3') else "N/A"
            
            date_advertised = "N/A"
            bids_open = "N/A"
            estimate = "N/A"
            description = "N/A"
            
            ng_paragraphs = soup.find_all('p', {'class': 'ng-binding'})
            
            for p in ng_paragraphs:
                text = p.get_text()
                
                date_adv_match = re.search(r'Date Advertised\s+(\d{4}-\d{2}-\d{2})', text)
                if date_adv_match:
                    date_advertised = date_adv_match.group(1)

                bids_open_match = re.search(r'Bids Open\s+(\d{4}-\d{2}-\d{2})', text)
                if bids_open_match:
                    bids_open = bids_open_match.group(1)

                estimate_match = re.search(r'Estimate:\s*\$?([\d,]+\.?\d*)', text)
                if estimate_match:
                    estimate = estimate_match.group(1)

                if 'Date Advertised' in text:
                    desc_part = text.split('Date Advertised')[0].strip()
                    if desc_part and len(desc_part) > 10:
                        description = desc_part

            license_info = "N/A"
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text()
                if 'Class A license' in text or 'Class C license' in text or 'Class B license' in text:
                    license_info = text.strip()
                    break

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
            import traceback
            traceback.print_exc()
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
            
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                span = link.find('span', {'class': 'h4'})
                if span and link.get('href'):
                    full_url = self.base_url + link['href']
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
            import traceback
            traceback.print_exc()
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
        print(f"\nSuccessfully scraped {len(opportunities)} opportunities")
        
        scraper.save_to_json(opportunities)
        print("\nScraping completed successfully!")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()