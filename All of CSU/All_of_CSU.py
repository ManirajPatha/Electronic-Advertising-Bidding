import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_calstate_bids(url):
    """
    Scrape bid opportunities from CalState bids website
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open('debug_calstate.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("HTML saved to debug_calstate.html for inspection")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        opportunities = []
        
        table = soup.find('table', {'aria-label': 'Search Results'})
        
        if not table:
            table = soup.find('table', class_='table phx table-hover no-column-borders')
        
        if not table:
            print("Could not find the search results table")
            all_tables = soup.find_all('table')
            print(f"Found {len(all_tables)} total tables on the page")
            for i, t in enumerate(all_tables[:3]):
                print(f"  Table {i+1}: {t.get('class', 'no class')} - {t.get('aria-label', 'no aria-label')}")
            return []
        
        print(f"Found search results table")
        
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            thead = table.find('thead')
            all_rows = table.find_all('tr')
            if thead:
                header_rows = thead.find_all('tr')
                rows = [r for r in all_rows if r not in header_rows]
            else:
                rows = all_rows[1:] if all_rows and all_rows[0].find('th') else all_rows
        
        print(f"Found {len(rows)} opportunity rows")
        
        for idx, row in enumerate(rows, 1):
            print(f"\nProcessing opportunity {idx}...")
            opportunity = {}
            
            cells = row.find_all('td')
            
            if not cells or row.find('th'):
                print(f"  Skipping header row")
                continue
            
            if len(cells) < 2:
                print(f"  Skipping row with only {len(cells)} cells")
                continue
            
            status_span = cells[0].find('span')
            if status_span:
                opportunity['status'] = status_span.get_text(strip=True)
            
            details_cell = cells[1]
            
            title_link = details_cell.find('a', class_='btn-link-header')
            if title_link:
                opportunity['title'] = title_link.get_text(strip=True)
                opportunity['title_link'] = title_link.get('href', '')
            
            desc_div = details_cell.find('div', class_='phx display-block phxText label-mini')
            if desc_div:
                opportunity['description'] = desc_div.get_text(strip=True)
            
            data_groups = details_cell.find_all('div', class_='phx table-row-layout')
            
            contacts = []
            
            for data_row in data_groups:
                cells_layout = data_row.find_all('div', class_='phx table-cell-layout')
                
                if len(cells_layout) >= 2:
                    label_div = cells_layout[0].find('div', class_='phx data-row-name')
                    value_div = cells_layout[1].find('div', class_='phx data-row-content')
                    
                    if label_div and value_div:
                        label = label_div.get_text(strip=True)
                        value = value_div.get_text(strip=True)
                        
                        if label == 'Open':
                            opportunity['open_date'] = value
                        elif label == 'Close':
                            opportunity['close_date'] = value
                        elif label == 'Type':
                            opportunity['type'] = value
                        elif label == 'Number':
                            opportunity['number'] = value
                        elif label == 'Contact':
                            email_link = value_div.find('a')
                            contact_info = {
                                'name': value.split('<')[0].strip() if '<' in value else value.split('mailto:')[0].strip(),
                                'email': email_link.get('href', '').replace('mailto:', '').split('?')[0] if email_link else ''
                            }
                            contacts.append(contact_info)
                        elif label == 'Details':
                            pdf_link = value_div.find('a', id=re.compile('BUTTON_PDF_VIEW'))
                            if pdf_link:
                                opportunity['pdf_link'] = pdf_link.get('href', '')
            
            if contacts:
                opportunity['contacts'] = contacts
            
            if len(cells) >= 3:
                respond_btn = cells[2].find('button')
                if respond_btn:
                    onclick = respond_btn.get('onclick', '')
                    match = re.search(r"navigatePage\('([^']+)'", onclick)
                    if match:
                        opportunity['respond_link'] = match.group(1)
            
            if len(opportunity) > 2:
                opportunities.append(opportunity)
                print(f"Added: {opportunity.get('title', 'Unknown')}")
        
        return opportunities
    
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing the data: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    url = "https://bids.sciquest.com/apps/Router/PublicEvent?CustomerOrg=CalState"
    
    print("Scraping bid opportunities from CalState...")
    
    opportunities = scrape_calstate_bids(url)
    
    if opportunities:
        json_output = json.dumps(opportunities, indent=2, ensure_ascii=False)
        
        print("SCRAPED OPPORTUNITIES (JSON):")
        print(json_output)
        
        with open('All_of_CSU_bids.json', 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        print(f"Data saved to 'calstate_bids.json'")
        print(f"Total opportunities scraped: {len(opportunities)}")
    else:
        print("No opportunities found.")
        print("Please check 'debug_calstate.html' to see the actual page structure.")

if __name__ == "__main__":
    main()