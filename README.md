# 📊 Screener Scraper

Welcome to **Screener Scraper**! 🚀

**Screener Scraper** is a Python tool designed to scrape and analyze data from the popular equity information website [Screener](https://www.screener.in/). 📈

## ✨ Features
- **Automated Data Extraction:** Seamlessly scrape stock data from Screener. To avoid making too many requests, it's better that you ensure that your screen doesn't have too many results.
- **Valuation Calculation:** Computes valuation based on the **Warren Buffett's Free Puffs** method, inspired by the book "Warren Buffett's Ground Rules."
- **Easy Output:** Generates a `.csv` file with all the essential data, as well as the Free Puff valuation.

## 🛠️ How to Use
1. **Set Up:** 
   - Ensure you have provided your cookies and CSRF tokens from Screener in a file named `secrets.env`. 🔑
   
2. **Run the Scraper:** 
   - When prompted, input the URL of your custom screen from Screener. 🌐

3. **Get Results:** 
   - The scraper will go through each of the companies in your screen, annd computes the liquidation valuation for each company. 🎯
   
4. **Output:** 
   - A `.csv` file will be generated containing all the crucial data you need for your analysis, along with the liquidation valuation. 📂


**Happy analyzing!** 