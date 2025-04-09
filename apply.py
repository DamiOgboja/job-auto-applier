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
#this will either be a link to the page with all the filters applied
#or a test url directly to a job posting
JOBS_URL = os.getenv("JOBS_URL")

#variables
running = False

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
        try:
            wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
            driver.find_element(By.ID, "password").send_keys(PASSWORD)
            driver.find_element(By.XPATH, "//input[@type='submit']").click()
        except:
            print("❌ Could not complete school login. You may need to update the selectors.")
            return
        
        # Step 4: Handle MFA manually if prompted
        print("If prompted for MFA, please complete it manually.")

        # Step 5: Confirm successful login by checking for dashboard elements
        dashboard_element = wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
        # Wait for login to complete (update this to reflect your institution’s redirect URL)
        wait.until(EC.url_contains("joinhandshake.com/explore"))
        print("Login successful!")
    except Exception as e:
        print(f"An error occurred: {e}")

def extract_job_data(url):
    link = url
    driver.get(link)
    
    # Wait for job title to appear
    try:
        title = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text
    except:
        title = "N/A"

    
    # Extract other info
    try:
        company = driver.find_element(By.CLASS_NAME, "job-details__employer-name").text
    except:
        company = "N/A"
    
    try:
        location = driver.find_element(By.CLASS_NAME, "job-details__location").text
    except:
        location = "N/A"
    
    try:
        salary = driver.find_element(By.CLASS_NAME, "job-details__compensation").text
    except:
        salary = "N/A"

    try:
        job_description = driver.find_element(By.CLASS_NAME, "jobs-show__description").text
    except:
        job_description = "N/A"

    # Check for Easy Apply
    try:
        apply_btn = driver.find_element(By.XPATH, "//span[text()='Quick Apply' or text()='Apply']")
        easy_apply = "Yes"
        apply_btn.click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@data-hook, 'apply-modal-content')]")))
    except:
        easy_apply = "No"

    # Extract required documents if Easy Apply modal opened
    required_docs = []
    if easy_apply == "Yes":
        try:
            modal_text = driver.find_element(By.XPATH, "//*[contains(@data-hook, 'apply-modal-content')]").text.lower()
            if "resume" in modal_text:
                required_docs.append("Resume")
            if "cover letter" in modal_text and "optional" not in modal_text:
                required_docs.append("Cover Letter")
            if "transcript" in modal_text:
                required_docs.append("Transcript")
        except:
            required_docs.append("Unknown")
    return {
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "link": link,
            "easy_apply": easy_apply,
            "required_docs": ", ".join(required_docs) if required_docs else "None",
            "job_description": job_description,
            "time": time()
        }



def write_to_csv(data, csv_path="applications.csv"):
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Job Title", "Company", "Location", "Salary", "Link",
                "Easy Apply", "Required Docs", "Job Description",
                "ReadyToApply", "Applied", "Time"
            ])
        writer.writerow([
            data["title"], data["company"], data["location"], data["salary"], data["link"],
            data["easy_apply"], data["required_docs"], data["job_description"],
            "N", "N", data["time"]
        ])

def scrape_multiple_jobs():
    print("Scraping job list page...")
    driver.get(JOBS_URL)
    jobs_scraped = []

    while True:
        try:
            job_cards = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "[data-hook='search-results'] [data-hook='jobs-card']")
            ))

            print(f"🔍 Found {len(job_cards)} jobs on this page...")

            for card in job_cards:
                job_link = card.get_attribute("href")
                if not job_link:
                    continue

                # Open job in new tab
                driver.execute_script("window.open(arguments[0]);", job_link)
                driver.switch_to.window(driver.window_handles[1])
                
                try:
                    data = extract_job_data()
                    write_to_csv(data)
                    jobs_scraped.append(data)
                except Exception as e:
                    print(f"❌ Failed to scrape job: {e}")
                finally:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

            # Try to go to the next page
            try:
                next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-hook='search-pagination-next']")))
                next_button.click()
                time.sleep(2)
            except:
                print("🔚 No more pages.")
                break

        except Exception as e:
            print(f"Error during multi-job scraping: {e}")
            break

    print(f"✅ Scraped {len(jobs_scraped)} jobs.")

def main():
    
    #start running
    running = True
    
    try:
        login()
        if "/jobs/" in JOBS_URL and "/stu/jobs/" in JOBS_URL:
            job_data = extract_job_data(JOBS_URL)
            write_to_csv(job_data)
        else:
            scrape_multiple_jobs()
        print("✅ Job scraped and logged successfully!")
    finally:
        running = False
        driver.quit()

if __name__ == '__main__':
    main()