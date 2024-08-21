import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    time.sleep(3) # To avoid getting too many requests errors

    # Get the page source after the content has been expanded
    html_content = driver.page_source
    return html_content

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
            data[first_cell.strip()] = last_cell.strip()
    return data

def compute_free_puff_valuation(company_data):
    """
    Given a data object, computes liquidation value based on Warren Buffet's Free Puffs method
    """
    debt = 0
    if "Borrowings" in company_data: debt += max(float(company_data["Borrowings"].replace(',', '')),0)
    if "Other Liabilities" in company_data: debt += max(float(company_data['Other Liabilities'].replace(',', '')), 0)

    assets = 0
    if "Fixed Assets" in company_data: assets += max(0.25 * float(company_data['Fixed Assets'].replace(',', '')), 0)
    if "Investments" in company_data: assets += max(float(company_data["Investments"].replace(',', '')), 0)

    return assets - debt

def parse_screen(screen_url:str, driver:webdriver.Chrome) -> pd.DataFrame:
    """
    Parses a query screen and returns dataframe of valuations
    """

    df = [ ]
    response = requests.get(f"{screen_url}", cookies=cookies, headers=headers)
    if response.status_code == 404:
        sys.exit("Please update the cookies or check the URL")
    if response.status_code != 200:
        sys.exit("Something went wrong. Retry!")
    soup = BeautifulSoup(response.content, features='html.parser')
    
    table = soup.find('table')
    if not table: return pd.DataFrame() # Handle error case

    # Iterate over each row in the table, skipping the header
    for row in table.find_all('tr')[1:]:
        # Extract the cells in the row
        a_tag = row.find('a')
        href_val = a_tag['href']
        html_content = expand_hidden_rows(driver=driver, href_tag=href_val)
        data = parse_company_data(html_content=html_content, href_tag=href_val)
        valuation =  compute_free_puff_valuation(company_data=data)
        data['valuation'] = valuation
        df.append(data)
        break

    
    df = pd.DataFrame(df)
    return df

def main():
    screen_url = input("Enter screen URL: ")
    driver = webdriver.Chrome()
    driver.fullscreen_window()
    df = parse_screen(screen_url=screen_url, driver=driver)
    df.to_csv("output.csv")
    driver.quit()

if __name__ == "__main__":
    main()