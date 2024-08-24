# region imports
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
import time
import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
# endregion

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
    "csrftoken" :CSRFTOKEN,
    "sessionid": SESSION_ID
}

# endregion

def expand_hidden_rows(driver:webdriver.Chrome, href_tag:str):
    driver.get(f"https://www.screener.in/{href_tag}/")

    buttons = driver.find_elements(By.CSS_SELECTOR, '#balance-sheet button.button-plain')

    for button in buttons:
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
            button.click()
        except Exception as e:
            print(e)

    time.sleep(2) # To avoid getting too many requests errors

    # Get the page source after the content has been expanded
    html_content = driver.page_source
    return html_content

def parse_market_cap(html_content, data):
    soup = BeautifulSoup(html_content, features='html.parser')
    ratios = soup.find(class_='company-ratios')
    if not ratios: return data

    ratios = ratios.find(id="top-ratios")
    if not ratios: return data

    ratio_spans = ratios.find_all('span')
    for i in range(len(ratio_spans)):
        if ratio_spans[i].text and ratio_spans[i].string.strip() == "Market Cap":
            data["Market Cap"] = ratio_spans[i + 2].string.strip().replace(',','')
            break
    return data
    
def parse_promoter_holding(html_content, data):
    soup = BeautifulSoup(html_content, features='html.parser')
    
    shareholding_section = soup.find(id='shareholding')
    if not shareholding_section: return data

    table = shareholding_section.find('table')
    if not table: return data # Handle error case

    rows = table.find_all("tr")[1:]
    if not rows: return data
    row = rows[0]
    cells = row.find_all('td')
    
    # Select the last cell in the row
    if cells:  # Check if there are any <td> elements in the row
        first_cell = re.findall(r'[a-zA-Z]+', cells[0].text)
        first_cell = " ".join(first_cell)
        last_cell = cells[-1].text  # Get the last <td> element
        data[first_cell.strip().upper()] = last_cell.strip()
        

    return data

def parse_company_data(html_content, href_tag):
    """
    Parses the company data and returns an object that holds important parameters for free puffs calculation
    """

    data = { "company" : href_tag }

    soup = BeautifulSoup(html_content, features='html.parser')
    
    balance_sheet_section = soup.find(id='balance-sheet')
    if not balance_sheet_section: return data # Handle error case

    table = balance_sheet_section.find('table')
    if not table: return data # Handle error case

    rows = table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all('td')
        
        # Select the last cell in the row
        if cells:  # Check if there are any <td> elements in the row
            first_cell = re.findall(r'[a-zA-Z]+', cells[0].text)
            first_cell = " ".join(first_cell)
            last_cell = cells[-1].text  # Get the last <td> element
            data[first_cell.strip().upper()] = last_cell.strip()
    return data

def compute_free_puff_valuation(company_data):
    """
    Given a data object, computes liquidation value based on Warren Buffet's Free Puffs method
    """
    debt = 0
    if "BORROWINGS" in company_data: 
        if not company_data["BORROWINGS"].replace(',', ''): debt += 0 # Handle the error case of empty string
        else: debt += max(float(company_data["BORROWINGS"].replace(',', '')),0)
    if "OTHER LIABILITIES" in company_data: 
        if not company_data['OTHER LIABILITIES'].replace(',', ''): debt += 0
        else: debt += max(float(company_data['OTHER LIABILITIES'].replace(',', '')), 0)

    assets = 0
    if "FIXED ASSETS" in company_data: 
        if not company_data['FIXED ASSETS'].replace(',', ''): 
            assets += 0
        else: assets += max(0.25 * float(company_data['FIXED ASSETS'].replace(',', '')), 0)
    if "INVESTMENTS" in company_data: 
        if not company_data["INVESTMENTS"].replace(',', ''): assets += 0
        else: assets += max(float(company_data["INVESTMENTS"].replace(',', '')), 0)
    if "CASH EQUIVALENTS" in company_data: 
        if not company_data['CASH EQUIVALENTS'].replace(',', ''): assets += 0 
        else: assets += max(float(company_data['CASH EQUIVALENTS'].replace(',', '')), 0)
    if "TRADE RECEIVABLES" in company_data: 
        if not company_data["TRADE RECEIVABLES"].replace(',', ''): assets += 0
        else: assets += max(0.85 * float(company_data["TRADE RECEIVABLES"].replace(',', '')), 0)
    if "INVENTORIES" in company_data: 
        if not company_data['INVENTORIES'].replace(",", ''): assets += 0
        else: assets += max(0.65 * float(company_data['INVENTORIES'].replace(",", '')), 0)
    if "OTHER ASSET ITEMS" in company_data: 
        if not company_data["OTHER ASSET ITEMS"].replace(",",''): assets += 0
        else: assets += max(0.25*float(company_data["OTHER ASSET ITEMS"].replace(",",'')), 0)
    if "CWIP" in company_data: 
        if not company_data['CWIP'].replace(',',''): assets += 0
        else: assets += max(float(company_data['CWIP'].replace(',','')), 0)
    return (assets, debt)

def parse_screen(screen_url:str, driver:webdriver.Chrome) -> pd.DataFrame:
    """
    Parses a query screen and returns dataframe of valuations
    """

    # If the parameter for page is not give, add the page=1
    screen_url = urlparse(screen_url)
    query_params = parse_qs(screen_url.query)
    if "page" not in query_params:
        query_params["page"] = ["1"]

    new_query = urlencode(query_params, doseq=True)
    screen_url = urlunparse(screen_url._replace(query=new_query))

    # The output
    df = [ ]

    # Request the webpage and handle error cases
    response = requests.get(f"{screen_url}", cookies=cookies, headers=headers)
    if response.status_code == 404:
        sys.exit("Please update the cookies or check the URL")
    if response.status_code != 200:
        sys.exit("Something went wrong. Retry!")


    # You need this to break out of the while loop
    # Because Screener does not return any error if you put excess page number. It just returns the last page
    previous_company = None 

    while True:
        soup = BeautifulSoup(response.content, features='html.parser')
        
        table = soup.find('table')
        if not table: return pd.DataFrame() # Handle error case

        # The first company in the table. This will be checked with previous_company to make sure
        # that we are still within the avaiable results
        first_company = None

        # Iterate over each row in the table, skipping the header
        for row in table.find_all('tr')[1:]:
            # Extract the cells in the row
            a_tag = row.find('a')
            href_val = a_tag['href']
            
            if not href_val: continue # Handle error case

            html_content = expand_hidden_rows(driver=driver, href_tag=href_val)
            data = parse_company_data(html_content=html_content, href_tag=href_val)
            data = parse_promoter_holding(html_content=html_content, data=data)
            data = parse_market_cap(html_content=html_content, data=data)
            assets, debt =  compute_free_puff_valuation(company_data=data)
            data['Assets'] = assets
            data['Debt'] = debt
            data['Difference'] = assets - debt
            df.append(data)
            # If the company is the first company of the page, update the variable
            if not first_company:
                first_company = a_tag
        break
        # Break out of the while loop if you have reached the last page
        if first_company == previous_company:
            break

        # Increment the page number by 1
        if "page" in query_params:
            query_params["page"] = [str(int(query_params["page"][0]) + 1)]
        else:
            query_params["page"] = ["1"]
        
        # Recreate the URL
        new_query = urlencode(query_params, doseq=True)
        parsed_url = urlparse(screen_url)
        screen_url = urlunparse(parsed_url._replace(query=new_query))

        # Request the next page and update the previous_company
        response = requests.get(f"{screen_url}", cookies=cookies, headers=headers)
        previous_company = first_company
    df = pd.DataFrame(df)
    return df

def process_output_dataframe(df:pd.DataFrame)-> pd.DataFrame:
    df['Difference'] = df['Difference'].astype(float)
    df['Market Cap'] = df['Market Cap'].astype(float)
    
    df = df[(df["Difference"] > 0) & (df['Market Cap'] > 0)]
    df["Profit Margin"] = (df['Difference'] / df['Market Cap'] )* 100
    df.sort_values(by=['Profit Margin'], ascending=False, inplace=True)
    return df

def main():
    screen_url = input("Enter screen URL: ")
    driver = webdriver.Chrome()
    driver.fullscreen_window()
    df = parse_screen(screen_url=screen_url, driver=driver)
    df = process_output_dataframe(df=df)
    df.to_csv("output.csv")
    driver.quit()

if __name__ == "__main__":
    main()