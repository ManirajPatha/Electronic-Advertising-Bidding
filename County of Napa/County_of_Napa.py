import requests
from bs4 import BeautifulSoup
import json
import time
import re

class NapaCountyScraper:
    def __init__(self):
        """Initialize the scraper with session"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        self.base_url = "https://www.napacounty.gov/Bids.aspx"
       
    def extract_bid_details(self, detail_url):
        """Extract detailed information from a bid detail page"""
        try:
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            time.sleep(1)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            bid_details = {}
           
            detail_table = soup.find('table', {'summary': 'Bid details'})
            if detail_table:
                rows = detail_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label_span = cells[0].find('span', {'class': 'BidDetail'})
                        if label_span:
                            label = label_span.get_text(strip=True).replace(':', '').replace('*', '').strip()
                           
                            value_span = cells[1].find('span', {'class': 'BidDetailSpec'})
                            value = value_span.get_text(strip=True) if value_span else cells[1].get_text(strip=True)
                           
                            key = label.lower().replace(' ', '_').replace(',', '').replace('/', '_').replace('(', '').replace(')', '')
                            if value:
                                bid_details[key] = value
            
            bid_details_table = soup.find('table', {'summary': 'Bid Details'})
            if bid_details_table:
                rows = bid_details_table.find_all('tr')
                i = 0
                while i < len(rows):
                    row = rows[i]
                    header_span = row.find('span', {'class': 'BidListHeader'})
                    if header_span:
                        header_text = header_span.get_text(strip=True).replace(':', '').strip()
                        
                        if i + 1 < len(rows):
                            detail_row = rows[i + 1]
                            detail_span = detail_row.find('span', {'class': 'BidDetail'})
                            
                            if detail_span:
                                if 'description' in header_text.lower():
                                    paragraphs = detail_span.find_all('p')
                                    if paragraphs:
                                        detail_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                                    else:
                                        detail_text = detail_span.get_text(separator='\n', strip=True)
                                else:
                                    detail_text = detail_span.get_text(strip=True)
                                
                                key = header_text.lower().replace(' ', '_').replace('/', '_').replace(',', '').replace('(', '').replace(')', '')
                                if detail_text:
                                    bid_details[key] = detail_text
                            
                            i += 2
                            continue
                    i += 1
           
            all_tables = soup.find_all('table')
            for table in all_tables:
                tbody = table.find('tbody')
                if not tbody:
                    continue
                   
                rows = tbody.find_all('tr')
                i = 0
                while i < len(rows):
                    row = rows[i]
                    header_span = row.find('span', {'class': 'BidListHeader'})
                    if header_span:
                        header_text = header_span.get_text(strip=True).replace(':', '').strip()
                        
                        if i + 1 < len(rows):
                            detail_row = rows[i + 1]
                            detail_span = detail_row.find('span', {'class': 'BidDetail'})
                           
                            if detail_span:
                                if 'description' in header_text.lower():
                                    paragraphs = detail_span.find_all('p')
                                    if paragraphs:
                                        detail_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                                    else:
                                        detail_text = detail_span.get_text(separator='\n', strip=True)
                                else:
                                    detail_text = detail_span.get_text(strip=True)
                               
                                key = header_text.lower().replace(' ', '_').replace('/', '_').replace(',', '').replace('(', '').replace(')', '')
                                if detail_text:
                                    bid_details[key] = detail_text
                           
                            i += 2
                            continue
                    i += 1
           
            attachments = []
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip']):
                    if not href.startswith('http'):
                        href = f"https://www.napacounty.gov/{href.lstrip('/')}"
                   
                    link_text = link.get_text(strip=True)
                    if link_text and href not in [a['url'] for a in attachments]:
                        attachments.append({
                            'name': link_text,
                            'url': href
                        })
           
            if attachments:
                bid_details['attachments'] = attachments
           
            opengov_links = soup.find_all('a', href=re.compile(r'opengov\.com', re.I))
            if opengov_links:
                for link in opengov_links:
                    href = link.get('href', '')
                    if href and 'portal' in href:
                        bid_details['opengov_portal'] = href
           
            return bid_details
           
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {}
   
    def scrape_category_bids(self, category_div):
        """Scrape all bids from a category section"""
        try:
            bids = []
           
            header = category_div.find('div', {'class': 'bidsHeader'})
            category_name = "Unknown"
            bid_count = 0
           
            if header:
                spans = header.find_all('span')
                if len(spans) >= 1:
                    category_name = spans[0].get_text(strip=True)
                if len(spans) >= 2:
                    count_text = spans[1].get_text(strip=True)
                    match = re.search(r'(\d+)', count_text)
                    if match:
                        bid_count = int(match.group(1))
           
            bid_rows = category_div.find_all('div', {'class': 'listItemsRow'})
           
            for bid_row in bid_rows:
                try:
                    bid_info = {
                        'category': category_name
                    }
                   
                    title_div = bid_row.find('div', {'class': 'bidTitle'})
                    if title_div:
                        title_link = title_div.find('a')
                        if title_link:
                            bid_info['detail_link'] = title_link.get('href', '')
                           
                            if bid_info['detail_link'] and not bid_info['detail_link'].startswith('http'):
                                bid_info['detail_link'] = f"https://www.napacounty.gov/{bid_info['detail_link']}"
                       
                        small_spans = title_div.find_all('span', style=re.compile(r'font-size.*0\.75em', re.I))
                        for span in small_spans:
                            text = span.get_text(strip=True)
                            if 'Bid No.' in text:
                                match = re.search(r'Bid No\.\s*(.+)', text)
                                if match:
                                    bid_info['bid_number'] = match.group(1).strip()
                       
                        all_spans = title_div.find_all('span', recursive=False)
                        for span in all_spans:
                            text = span.get_text(strip=True)
                            if text and 'Read on' not in text and 'Bid No.' not in text:
                                if 'preview' not in bid_info:
                                    bid_info['preview'] = text
                   
                    status_div = bid_row.find('div', {'class': 'bidStatus'})
                    if status_div:
                        status_divs = status_div.find_all('div', recursive=False)
                        if len(status_divs) >= 2:
                            value_spans = status_divs[1].find_all('span')
                            if len(value_spans) >= 1:
                                bid_info['status'] = value_spans[0].get_text(strip=True)
                   
                    bids.append(bid_info)
                   
                except Exception as e:
                    continue
           
            return bids
           
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []
   
    def scrape_all_bids(self):
        """Main method to scrape all bids from the Napa County portal"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            time.sleep(2)
           
            soup = BeautifulSoup(response.content, 'html.parser')
           
            category_divs = soup.find_all('div', {'class': 'bidItems'})
           
            all_bids = []
           
            for category_div in category_divs:
                category_bids = self.scrape_category_bids(category_div)
                all_bids.extend(category_bids)
           
            detailed_bids = []
            for bid in all_bids:
                try:
                    detail_link = bid.get('detail_link')
                    if detail_link:
                        details = self.extract_bid_details(detail_link)
                       
                        bid.update(details)
                        detailed_bids.append(bid)
                   
                    time.sleep(1)
                   
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    detailed_bids.append(bid)
                    continue
           
            return detailed_bids
           
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []
   
    def save_to_json(self, data, filename='napa_county_bids.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def close(self):
        """Close the session"""
        self.session.close()

def main():
    """Main execution function"""
    scraper = NapaCountyScraper()
   
    try:
        print("Starting to scrape Napa County bids...")
        bids = scraper.scrape_all_bids()
        print(f"Scraped {len(bids)} bids")
       
        scraper.save_to_json(bids)
        print(f"Data saved to napa_county_bids.json")
       
    except Exception as e:
        import traceback
        traceback.print_exc()
   
    finally:
        scraper.close()

if __name__ == "__main__":
    main()