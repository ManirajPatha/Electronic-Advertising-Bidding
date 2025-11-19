import requests
from bs4 import BeautifulSoup
import json
import re
import os
from urllib.parse import urljoin

def scrape_projects():
    base_url = "https://www.cccplanroom.com"
    list_url = f"{base_url}/projects/public?status=bidding"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(list_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching list URL: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    projects = []
    rows = soup.find_all('a', class_='row')
    
    for row in rows:
        project_data = {}
        
        relative_link = row.get('href', '')
        details_link = urljoin(base_url, relative_link) if relative_link else ''
        project_data['link'] = details_link
        
        plan_holders_link = details_link.replace('/details/', '/plan-holders/') if details_link else ''
        
        name_elem = row.find('div', class_='name')
        project_data['name'] = name_elem.get_text(strip=True) if name_elem else ''
        
        company_elem = row.find('div', class_='company')
        if company_elem:
            company_text = company_elem.get_text(strip=True)
            project_data['company'] = re.sub(r'^.*?\s+', '', company_text)
        
        location_elem = row.find('div', class_='location')
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            project_data['location'] = re.sub(r'^.*?\s+', '', location_text)
        
        desc_elem = row.find('div', class_='description')
        project_data['description'] = desc_elem.get_text(strip=True) if desc_elem else ''
        
        status_dates_elem = row.find('div', class_='status-dates')
        project_data['dates_info'] = status_dates_elem.get('title', '') if status_dates_elem else ''
        
        if status_dates_elem:
            status_elem = status_dates_elem.find('div', class_='status')
            if status_elem:
                status_text = status_elem.get_text(strip=True)
                project_data['bid_due_status'] = re.sub(r'<svg.*?</svg>\s*', '', status_text, flags=re.DOTALL).strip()
        
        if status_dates_elem:
            bid_date_elem = status_dates_elem.find('div', class_='bid-date')
            project_data['bid_date'] = bid_date_elem.get_text(strip=True) if bid_date_elem else ''
        
        notification_elem = row.find('div', class_='notification bidding')
        if notification_elem:
            project_data['notification_status'] = notification_elem.get_text(strip=True)
        
        status_secondary_elem = row.find('div', class_='status-secondary')
        if status_secondary_elem:
            mobile_status = status_secondary_elem.get_text(strip=True)
            project_data['mobile_status'] = re.sub(r'<svg.*?</svg>\s*', '', mobile_status, flags=re.DOTALL).strip()
        
        project_data['notes'] = {}
        project_data['planholders'] = []
        
        if details_link:
            try:
                detail_response = requests.get(details_link, headers=headers)
                detail_response.raise_for_status()
                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                
                notes_section = detail_soup.find('div', class_='notes')
                if notes_section:
                    note_div = notes_section.find('div', class_='note')
                    if note_div:
                        notes_text = note_div.get_text(separator='\n', strip=True)
                        project_data['notes']['full_text'] = notes_text
                        
                        emails = re.findall(r'[\w\.-]+@[\w\.-]+', notes_text)
                        project_data['notes']['emails'] = list(set(emails))
                        
                        phones = re.findall(r'\(\d{3}\) \d{3}-\d{4}', notes_text)
                        project_data['notes']['phones'] = phones
                        
                        if 'Pre-Proposal Conference' in notes_text:
                            conf_match = re.search(r'Virtual Pre-Proposal Conference: (.*)', notes_text, re.DOTALL | re.IGNORECASE)
                            if conf_match:
                                project_data['notes']['pre_proposal_conference'] = conf_match.group(1).strip()
                
            except requests.RequestException as e:
                print(f"Error fetching details page {details_link}: {e}")
        
        if plan_holders_link:
            try:
                plan_response = requests.get(plan_holders_link, headers=headers)
                plan_response.raise_for_status()
                plan_soup = BeautifulSoup(plan_response.content, 'html.parser')
                
                table = plan_soup.find('table', {'class': lambda x: x and 'planholders' in x})
                if table:
                    project_data['planholders'] = []
                    
                    tbody = table.find('tbody')
                    if tbody:
                        for tr in tbody.find_all('tr'):
                            row_data = {}
                            
                            date_td = tr.find('td', class_='date')
                            if date_td:
                                strong = date_td.find('strong')
                                row_data['date'] = strong.get_text(strip=True) if strong else ''
                            
                            company_td = tr.find('td', class_='company')
                            if company_td:
                                strong = company_td.find('strong')
                                company_name = strong.get_text(strip=True) if strong else ''
                                address_div = company_td.find('div')
                                company_address = address_div.get_text(separator='\n', strip=True) if address_div else ''
                                row_data['company'] = {
                                    'name': company_name,
                                    'address': company_address.strip()
                                }
                            
                            contact_td = tr.find('td', class_='contact')
                            if contact_td:
                                strong = contact_td.find('strong')
                                contact_name = strong.get_text(strip=True) if strong else ''
                                title_div = contact_td.find('div', class_=lambda x: x and 'op-7' in x and 'font-weight-bold' in x)
                                title = title_div.get_text(strip=True) if title_div else ''
                                phone_container = contact_td.find('div', class_='tw-mt-1')
                                phones = []
                                if phone_container:
                                    for div in phone_container.find_all('div'):
                                        text = div.get_text(strip=True)
                                        if 'Tel:' in text or 'Fax:' in text:
                                            phones.append(text)
                                row_data['contact'] = {
                                    'name': contact_name,
                                    'title': title,
                                    'phones': phones
                                }
                            
                            if any(row_data.values()):
                                project_data['planholders'].append(row_data)
                
            except requests.RequestException as e:
                print(f"Error fetching plan-holders page {plan_holders_link}: {e}")
        
        projects.append(project_data)
    
    return projects

if __name__ == "__main__":
    data = scrape_projects()
    filename = 'Contra_Costa.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4, default=str)
    
    if os.path.exists(filename):
        print(f" Data saved to {filename}.")
    else:
        print("Error: File was not created. Check permissions or path.")