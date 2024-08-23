from app import *
from selenium import webdriver
# Take 2-3 companies and compute the valuation on your own. See if the valuation matches or at least is
# close to what you got with the code.

def test_valuation_of_baroda_rayon():
    driver = webdriver.Chrome()
    manually_computed_debt = 309
    manually_computed_assets = 415
    manual_valuation = manually_computed_assets - manually_computed_debt
    html_content = expand_hidden_rows(driver=driver, href_tag="company/500270/")
    data = parse_company_data(html_content=html_content, href_tag="company/500270/")
    auto_computed_assets, auto_computed_debt =  compute_free_puff_valuation(company_data=data)
    auto_computed_valuation = auto_computed_assets - auto_computed_debt

    print(data, manual_valuation, auto_computed_valuation)
    # Check whether auto computation is within 10% of what you computed naturally
    assert abs(auto_computed_valuation - manual_valuation) <= manual_valuation * 0.1

    driver.quit()

def test_valuation_of_family_care_hospitals():
    driver = webdriver.Chrome()
    manually_computed_debt = 12
    manually_computed_assets = 52
    manual_valuation = manually_computed_assets - manually_computed_debt
    html_content = expand_hidden_rows(driver=driver, href_tag="company/516110/")
    data = parse_company_data(html_content=html_content, href_tag="company/516110/")
    auto_computed_assets, auto_computed_debt =  compute_free_puff_valuation(company_data=data)
    auto_computed_valuation = auto_computed_assets - auto_computed_debt

    # Check whether auto computation is within 10% of what you computed naturally
    assert abs(auto_computed_valuation - manual_valuation) <= manual_valuation * 0.1

    driver.quit()