import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

class YoloCountyScraper:
    def __init__(self):
        self.base_url = "https://www.beaconbid.com/solicitations/yolo-county/open"
        self.opportunities = []

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=options)
        
    def scrape_opportunities_list(self):
        """Scrape the main list of opportunities"""
        print("Loading opportunities page...")
        self.driver.get(self.base_url)
        
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "border-b")))
        time.sleep(3)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        opportunity_rows = soup.find_all('div', class_='border-b last:border-b-0 grid w-full hover:bg-zinc-50')
        
        print(f"Found {len(opportunity_rows)} opportunities")
        
        opportunities_list = []
        for row in opportunity_rows:
            try:
                title_div = row.find('div', class_='overflow-hidden text-ellipsis')
                title = title_div.text.strip() if title_div else "N/A"

                date_divs = row.find_all('div', class_='flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis skeleton-off')
                due_date = date_divs[1].text.strip() if len(date_divs) > 1 else "N/A"

                days_left_div = row.find('div', class_='inline-flex items-center justify-center text-center rounded truncate')
                days_left = days_left_div.find('span').text.strip() if days_left_div else "N/A"

                ebid_badge = row.find('span', class_='whitespace-nowrap cursor-default text-white relative bg-blue')
                is_ebid = ebid_badge is not None
                
                opportunities_list.append({
                    'title': title,
                    'due_date': due_date,
                    'days_left': days_left,
                    'is_ebid': is_ebid
                })
                
            except Exception as e:
                print(f"Error parsing opportunity row: {e}")
                continue
        
        return opportunities_list
    
    def scrape_opportunity_details(self, title, index):
        """Click on a specific opportunity and scrape its details"""
        
        try:
            self.driver.get(self.base_url)
            time.sleep(3)

            wait = WebDriverWait(self.driver, 10)

            rows = self.driver.find_elements(By.CSS_SELECTOR, 'div.border-b.last\\:border-b-0.grid.w-full.hover\\:bg-zinc-50')
            
            if index >= len(rows):
                print(f"Index {index} out of range, only {len(rows)} opportunities found")
                return None
            
            rows[index].click()
            
            time.sleep(4)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {}
            
            status_badges = soup.find_all('div', class_='uppercase font-medium rounded px-4 items-center justify-center select-none gap-1 inline-flex')
            details['status'] = "N/A"
            for badge in status_badges:
                span = badge.find('span')
                if span and span.text.strip() in ['Open', 'Closed', 'Cancelled', 'Awarded']:
                    details['status'] = span.text.strip()
                    break

            info_container = soup.find('div', class_='flex flex-wrap gap-10 py-20px')
            
            if info_container:
                info_sections = info_container.find_all('div', class_='inline-flex', recursive=False)
                
                for section in info_sections:
                    label_div = section.find('div', class_='text-12 text-label flex items-center')
                    value_div = section.find('div', class_='text-16 text-black')
                    
                    if label_div and value_div:
                        label = label_div.text.strip()
                        value_span = value_div.find('span', class_='font-medium')
                        value = value_span.text.strip() if value_span else value_div.text.strip()
                        
                        if 'Reference No.' in label:
                            details['reference_no'] = value
                        elif 'Due Date' in label:
                            details['due_date_detailed'] = value
                        elif 'Questions Due' in label:
                            date_text = value_div.get_text(strip=True)
                            details['questions_due'] = date_text.split()[0] if date_text else "N/A"
                        elif 'Time Remaining' in label:
                            font_div = value_div.find('div', class_='font-medium')
                            details['time_remaining'] = font_div.text.strip() if font_div else value
            
            
            basic_info_container = soup.find('div', class_='flex flex-wrap gap-10')
            
            if basic_info_container:
                basic_sections = basic_info_container.find_all('div', class_='inline-flex', recursive=False)
                
                for section in basic_sections:
                    label_div = section.find('div', class_='text-12 text-label flex items-center')
                    value_div = section.find('div', class_='text-16 text-black')
                    
                    if label_div and value_div:
                        label = label_div.text.strip()
                        
                        if 'Release Date' in label:
                            date_div = value_div.find('div', class_='inline-flex items-center')
                            details['release_date'] = date_div.text.strip() if date_div else value_div.text.strip()
                        elif 'Type' in label:
                            details['type'] = value_div.text.strip()
                        elif 'Categories' in label:
                            
                            category_divs = value_div.find_all('div', class_='overflow-hidden text-ellipsis text-nowrap')
                            categories = [cat.text.strip() for cat in category_divs if cat.text.strip()]
                            details['categories'] = categories if categories else ["N/A"]
            
            
            contact_info_containers = soup.find_all('div', class_='flex flex-col gap-5')
            
            for container in contact_info_containers:
                contact_items = container.find_all('div', class_='inline-flex', recursive=False)
                
                for item in contact_items:
                    
                    label_div = item.find('div', class_='text-12 text-label flex items-center')
                    value_div = item.find('div', class_='text-16 text-black')
                    
                    if label_div and value_div:
                        label = label_div.text.strip()
                        value = value_div.text.strip()
                        
                        if 'Contact Name' in label:
                            details['contact_name'] = value
                        elif 'Email Address' in label:
                            details['contact_email'] = value
                        elif 'Phone No.' in label or 'Phone' in label:
                            details['contact_phone'] = value
            
            description_section = soup.find('h3', string='Description')
            if description_section:
                desc_parent = description_section.find_parent('div')
                if desc_parent:
                    desc_content = desc_parent.find_next_sibling('div')
                    if desc_content:
                        
                        paragraphs = desc_content.find_all('p')
                        description_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        details['description'] = description_text[:500] + "..." if len(description_text) > 500 else description_text
            
            return details
            
        except TimeoutException:
            print(f"Timeout waiting for opportunity: {title}")
            return None
        except Exception as e:
            print(f"Error scraping details for {title}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_all(self):
        """Main method to scrape all opportunities"""
        try:
            
            opportunities_list = self.scrape_opportunities_list()
            
            
            for index, opp in enumerate(opportunities_list):
                details = self.scrape_opportunity_details(opp['title'], index)
                
                if details:
                    
                    complete_data = {**opp, **details}
                    self.opportunities.append(complete_data)
                else:
                    
                    self.opportunities.append(opp)
                
                
                time.sleep(2)
            
            return self.opportunities
            
        finally:
            self.driver.quit()
    
    def save_to_json(self, filename='yolo_opportunities.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.opportunities, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")


def main():
    scraper = YoloCountyScraper()
    
    print("Starting Yolo County Opportunities Scraper...")
    print("=" * 60)
    
    
    opportunities = scraper.scrape_all()
    
    
    scraper.save_to_json()
    
    print("\n" + "=" * 60)
    print(f"Scraping completed! Total opportunities scraped: {len(opportunities)}")


if __name__ == "__main__":
    main()