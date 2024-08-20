import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re

# region configuration
load_dotenv(r"..\secrets.env")

# Environment Variables
UIR = os.getenv("UPGRADE_INSECURE_REQUESTS")
CSRFTOKEN = os.getenv("CSRFTOKEN")
SESSION_ID = os.getenv("SESSIONID")

# Request Parameters
headers = {
    "upgrade-insecure-requests":UIR,
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}

cookies = {
    "csrftoken":CSRFTOKEN,
    "sessionid": SESSION_ID
}

# endregion

def parse_company_data(href_tag):
    """
    Parses the company data and returns an object that holds important parameters for free puffs calculation
    """
    res = requests.get(f"https://www.screener.in/{href_tag}", cookies=cookies, headers=headers)
    soup = BeautifulSoup(res.content, features='html.parser')
    rows = soup.find(id='balance-sheet').find('table').find_all("tr")[1:]
    
    data = { }

    for row in rows:
        cells = row.find_all('td')
        print(cells[0])
        
        # Select the last cell in the row
        if cells:  # Check if there are any <td> elements in the row
            first_cell = re.findall(r'[a-zA-Z]+', cells[0].text)
            first_cell = " ".join(first_cell)
            last_cell = cells[-1].text  # Get the last <td> element
            data[first_cell.strip()] = last_cell.strip()
    return data


def compute_free_puff_valuation(company_data):
    """
    Given a data object, computes liquidation value based on Warren Buffet's Free Puffs method
    """
    debt = 0
    if "Borrowings" in company_data: debt += max(float(company_data["Borrowings"]),0)
    if "Other Liabilities" in company_data: debt += max(float(company_data['Other Liabilities']), 0)

    assets = 0
    if "Fixed Assets" in company_data: assets += max(0.25 * float(company_data['Fixed Assets']), 0)
    if "Investments" in company_data: assets += max(company_data["Investments"], 0)

def parse_screen(screen_url):
    """
    Parses a query screen 
    """
    response = requests.get(f"{screen_url}", cookies=cookies, headers=headers)

    soup = BeautifulSoup(response.content, features='html.parser')
    table = soup.find('table')
    # Iterate over each row in the table, skipping the header
    for row in table.find_all('tr')[1:]:
        # Extract the cells in the row
        a_tag = row.find('a')
        href_val = a_tag['href']
        obj = parse_company_data(href_tag=href_val)
    

def main():
    screen_url = input("Enter screen URL: ")
    parse_screen(screen_url=screen_url)

if __name__ == "__main__":
    main()