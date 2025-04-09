from datetime import time
import os
import csv
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables from .env file
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SCHOOL = os.getenv("SCHOOL")

#variables
running = False

# Job URL to test
JOB_URL = ""

# Set up driver
driver = webdriver.Chrome()  # or use Service + webdriver_manager if needed
wait = WebDriverWait(driver, 15)

def login():
    try:
        #step 1 Navigate to my schools Handshake login page
        driver.get(os.getenv("LOGIN_URL"))


        # Step 2: Click on schools SSO prompt to initiate SSO
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{SCHOOL}')]")))
        login_button.click()

        #input("Press Enter when logged in...")

        # Step 3: Enter schools credentials on Microsoft's login page
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//input[@type='submit']").click()

        # Step 4: Handle MFA manually if prompted
        print("If prompted for MFA, please complete it manually.")

        # Step 5: Confirm successful login by checking for dashboard elements
        dashboard_element = wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
        # Wait for login to complete (update this to reflect your institution’s redirect URL)
        wait.until(EC.url_contains("joinhandshake.com/explore"))
        print("Login successful!")
    except Exception as e:
        print(f"An error occurred: {e}")



def main():
    

    

    #start running
    running = True
    
    try:
        login()

        print("✅ Job scraped and logged successfully!")
    finally:
        running = False
        driver.quit()

if __name__ == '__main__':
    main()