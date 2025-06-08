import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

CHROME_DRIVER_PATH = r"C:\Users\Kibret\Desktop\chromedriver-win64\chromedriver.exe"
BASE_URL = "https://www.example.com"
WAIT_TIME = 60
OUTPUT_FILE = "contract_research_map_all_vendors.xlsx"

# === SETUP DRIVER ===
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
service = Service(executable_path=CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, WAIT_TIME)

# === STORAGE ===
all_data = []

def load_all_vendors():
    """Click all 'Load More' buttons to reveal all vendors"""
    while True:
        try:
            load_more = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vendor-list__load-more")))
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(2)
        except:
            break

# === START SCRAPING ===
print("Starting scrape...")
driver.get(BASE_URL)
wait.until(EC.presence_of_element_located((By.ID, "locations")))

# Get countries
countries = driver.find_elements(By.CSS_SELECTOR, "#locations .item")
country_info = [(c.find_element(By.CLASS_NAME, "item__title").text.strip(),
                 c.get_attribute("data-url")) for c in countries]

print(f"\n{len(country_info)} countries found.")

for name, relative_url in country_info:
    if not name or not relative_url:
        continue

    print(f"\nScraping country: {name} ({relative_url})")
    full_url = BASE_URL.rstrip("/") + relative_url
    driver.get(full_url)

    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item__title")))
        load_all_vendors()
        time.sleep(3)
    except TimeoutException:
        print(f"Timeout: Vendor list did not load for {name}. Skipping...")
        continue

    items = driver.find_elements(By.CSS_SELECTOR, "div.item")
    print(f"Found {len(items)} vendors in {name}")

    if not items:
        continue

    for item in items:
        try:
            company_name = item.find_element(By.CLASS_NAME, "item__title").text.strip()
        except:
            company_name = ""

        try:
            address = item.find_element(By.CLASS_NAME, "item__subtitle").text.strip()
        except:
            address = ""

        try:
            description = item.find_element(By.CLASS_NAME, "item__snippet").text.strip()
        except:
            description = ""

        all_data.append({
            "Company Name": company_name,
            "Country": name,
            "Address": address,
            "Description": description
        })

# === SAVE FINAL COMBINED FILE ===
if all_data:
    df = pd.DataFrame(all_data)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(all_data)} total vendors to '{OUTPUT_FILE}'")
else:
    print("\nNo vendor data found.")

# === DONE ===
driver.quit()
print("All countries scraped.")
