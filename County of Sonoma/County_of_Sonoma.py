from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime


class SonomaCountyScraper:
    def __init__(self):
        """Initialize the scraper with Chrome webdriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        self.base_url = "https://esupplier.sonomacounty.ca.gov/psc/FN92PRD/SUPPLIER/ERP/c/SCP_PUBLIC_MENU_FL.SCP_PUB_BID_CMP_FL.GBL"
        
    def extract_table_data(self):
        """Extract bid items table data"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            table = soup.find('table', {'class': 'ps_grid-flex'})
            if not table:
                return []
            
            items = []
            tbody = table.find('tbody', {'class': 'ps_grid-body'})
            if tbody:
                rows = tbody.find_all('tr', {'class': 'ps_grid-row'})
                
                for row in rows:
                    cells = row.find_all('td', {'class': 'ps_grid-cell'})
                    if len(cells) >= 4:
                        line_num_div = cells[0].find('span', {'class': 'ps_box-value'})
                        line_number = line_num_div.get_text(strip=True) if line_num_div else "N/A"
                        
                        mandatory_div = cells[1].find('span', {'class': 'ps_box-value'})
                        bid_mandatory = mandatory_div.get_text(strip=True) if mandatory_div else "N/A"
                        
                        desc_div = cells[2].find('span', {'class': 'ps_box-value'})
                        description = desc_div.get_text(strip=True) if desc_div else "N/A"
                        
                        qty_cell = cells[3]
                        qty_spans = qty_cell.find_all('span', {'class': 'ps_box-value'})
                        quantity = qty_spans[0].get_text(strip=True) if len(qty_spans) > 0 else "N/A"
                        uom = qty_spans[1].get_text(strip=True) if len(qty_spans) > 1 else "N/A"
                        
                        item = {
                            'line_number': line_number,
                            'bid_mandatory': bid_mandatory,
                            'item_description': description,
                            'requested_quantity': quantity,
                            'unit_of_measure': uom
                        }
                        items.append(item)
            
            return items
            
        except Exception as e:
            print(f"Error extracting table data: {e}")
            return []
    
    def get_contact_information(self):
        """Click on contact information icon and extract details"""
        try:
            contact_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "SCP_COSP_WK_FL_IMAGE_1$0"))
            )
            contact_btn.click()
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            phone_span = soup.find('span', {'id': 'SCP_P_AUCDTL_VW_PHONE'})
            telephone = phone_span.get_text(strip=True) if phone_span else "N/A"
            
            email_span = soup.find('span', {'id': 'SCP_P_AUCDTL_VW_EMAILID'})
            email = email_span.get_text(strip=True) if email_span else "N/A"
            
            contact_info = {
                'telephone': telephone,
                'email': email
            }
            
            try:
                close_btn = self.driver.find_element(By.ID, "#ICCancel")
                close_btn.click()
                time.sleep(1)
            except:
                pass
            
            return contact_info
            
        except Exception as e:
            print(f"Error getting contact information: {e}")
            return {'telephone': 'N/A', 'email': 'N/A'}
    
    def extract_field_value(self, soup, field_id):
        """Helper method to extract field values by ID"""
        try:
            span = soup.find('span', {'id': field_id})
            return span.get_text(strip=True) if span else "N/A"
        except:
            return "N/A"
    
    def scrape_event_details(self):
        """Scrape details from a single event page"""
        try:
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            event_name = self.extract_field_value(soup, 'SCP_P_AUCDTL_VW_AUC_NAME$0')
            business_unit = self.extract_field_value(soup, 'BUS_UNIT_AUC_VW_DESCR$0')
            event_id = self.extract_field_value(soup, 'SCP_P_AUCDTL_VW_AUC_ID$0')
            event_status = self.extract_field_value(soup, 'SCP_P_AUCDTL_VW_AUC_STATUS$0')
            buyer_name = self.extract_field_value(soup, 'PO_OPRDEFN_VW_OPRDEFNDESC$0')
            multiple_bids = self.extract_field_value(soup, 'SCP_P_AUCDTL_VW_MULTIPLE_BIDS_FLG$0')
            
            desc_span = soup.find('span', {'id': 'SCP_P_AUCDTL_VW_DESCRLONG$0'})
            description = ""
            if desc_span:
                description = desc_span.decode_contents().strip()
                description = description.replace('<br>', '\n').replace('<br/>', '\n')
                from html import unescape
                description = unescape(description)
            
            contact_info = self.get_contact_information()
            
            bid_items = self.extract_table_data()
            
            event_data = {
                'event_name': event_name,
                'business_unit': business_unit,
                'event_id': event_id,
                'event_status': event_status,
                'buyer_name': buyer_name,
                'multiple_bids': multiple_bids,
                'contact_telephone': contact_info['telephone'],
                'contact_email': contact_info['email'],
                'description': description,
                'bid_items': bid_items,
                'url': self.driver.current_url,
            }
            
            return event_data
            
        except Exception as e:
            print(f"Error scraping event details: {e}")
            return None
    
    def scrape_all_events(self):
        """Main method to scrape all bidding events"""
        try:
            print("Loading Sonoma County e-Supplier Portal...")
            self.driver.get(self.base_url)
            time.sleep(5)
            
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "ps_grid-body"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            tbody = soup.find('tbody', {'class': 'ps_grid-body'})
            if not tbody:
                print("Could not find event table")
                return []
            
            rows = tbody.find_all('tr', {'class': 'ps_grid-row'})
            print(f"Found {len(rows)} bidding events")
            
            events_list = []
            for idx, row in enumerate(rows):
                try:
                    cells = row.find_all('td', {'class': 'ps_grid-cell'})
                    if len(cells) >= 8:
                        event_info = {
                            'row_index': idx,
                            'event_name': self._get_cell_value(cells[0]),
                            'business_unit': self._get_cell_value(cells[1]),
                            'event_id': self._get_cell_value(cells[2]),
                            'event_format': self._get_cell_value(cells[3]),
                            'event_type': self._get_cell_value(cells[4]),
                            'ends_in': self._get_cell_value(cells[5], is_html=True),
                            'start_date': self._get_cell_value(cells[6]),
                            'end_date': self._get_cell_value(cells[7])
                        }
                        events_list.append(event_info)
                except Exception as e:
                    print(f"Error extracting row {idx}: {e}")
            
            all_events_data = []
            for idx, event in enumerate(events_list):
                try:
                    print(f"\nProcessing event {idx + 1}/{len(events_list)}: {event['event_name']}")
                    
                    self.driver.get(self.base_url)
                    time.sleep(3)
                    
                    self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "ps_grid-body"))
                    )
                    
                    detail_btn_id = f"SCP_COSP_WK_FL_DESCR${idx}"
                    detail_btn = self.wait.until(
                        EC.element_to_be_clickable((By.ID, detail_btn_id))
                    )
                    detail_btn.click()
                    
                    event_details = self.scrape_event_details()
                    
                    if event_details:
                        event_details.update(event)
                        all_events_data.append(event_details)
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error processing event {idx}: {e}")
                    continue
            
            return all_events_data
            
        except Exception as e:
            print(f"Error scraping events list: {e}")
            return []
    
    def _get_cell_value(self, cell, is_html=False):
        """Helper to extract value from table cell"""
        try:
            if is_html:
                html_div = cell.find('div', {'class': 'ps-htmlarea'})
                if html_div:
                    return html_div.get_text(strip=True)
            
            span = cell.find('span', {'class': 'ps_box-value'})
            return span.get_text(strip=True) if span else "N/A"
        except:
            return "N/A"
    
    def save_to_json(self, data, filename='sonoma_county_events.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()


def main():
    """Main execution function"""
    scraper = SonomaCountyScraper()
    
    try:
        print("Starting Sonoma County e-Supplier Portal scraper...")
        events = scraper.scrape_all_events()
        
        print(f"Successfully scraped {len(events)} events")
        
        scraper.save_to_json(events)
        
        print("\nEvents Summary:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event.get('event_name', 'N/A')} (ID: {event.get('event_id', 'N/A')})")
        
        print("\nScraping completed successfully")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()