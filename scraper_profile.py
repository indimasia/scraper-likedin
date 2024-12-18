# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import time
import pandas as pd
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import os

# Initialize Chrome options
chrome_options = Options()
today = datetime.today().strftime('%Y-%m-%d')

# Load environment variables from .env file
load_dotenv()

# Get username and password from environment variables
username = os.getenv("LINKEDIN_USERNAME")
password = os.getenv("LINKEDIN_PASSWORD")

# Set LinkedIn page URL for scraping
page = 'https://www.linkedin.com/in/indimasia/'

# Initialize WebDriver for Chrome
browser = webdriver.Chrome()

# Open LinkedIn login page
browser.get('https://www.linkedin.com/login')

# Enter login credentials and submit
elementID = browser.find_element(By.ID, "username")
elementID.send_keys(username)
elementID = browser.find_element(By.ID, "password")
elementID.send_keys(password)
elementID.submit()

# Navigate to the posts page of the company
# post_page = page + '/posts'
# post_page = post_page.replace('//posts','/recent-activity/all/')
browser.get(page)

# Extract company name from URL
company_name = page.rstrip('/').split('/')[-1].replace('-', ' ').title()
print(company_name)

# Set parameters for scrolling through the page
SCROLL_PAUSE_TIME = 1.5
MAX_SCROLLS = False
last_height = browser.execute_script("return document.body.scrollHeight")
scrolls = 0
no_change_count = 0

# Scroll through the page until no new content is loaded
while True:
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = browser.execute_script("return document.body.scrollHeight")
    no_change_count = no_change_count + 1 if new_height == last_height else 0
    if no_change_count >= 3 or (MAX_SCROLLS and scrolls >= MAX_SCROLLS):
        break
    last_height = new_height
    scrolls += 1

# Parse the page source with BeautifulSoup
company_page = browser.page_source
linkedin_soup = bs(company_page.encode("utf-8"), "html.parser")

# Save the parsed HTML to a file
with open(f"{company_name}_soup.txt", "w+", encoding='utf-8') as t:
    t.write(linkedin_soup.prettify())

# Extract post containers from the HTML
containers = [container for container in linkedin_soup.find_all("div",{"class":"feed-shared-update-v2"}) if 'activity' in container.get('data-urn', '')]


# Define a data structure to hold all the post information
posts_data = []

# Function to extract text from a container
def get_text(container, selector, attributes):
    try:
        element = container.find(selector, attributes)
        if element:
            return element.text.strip()
    except Exception as e:
        print(e)
    return ""


try:
    name_container = linkedin_soup.find("div", {"id": "ember31"})
    if name_container:
        name = name_container.get_text(separator=" ", strip=True)
        # Remove any text within span tags
        for span in name_container.find_all("span"):
            name = name.replace(span.get_text(separator=" ", strip=True), "").strip()
    else:
        name = ""
    print('this is name')
    print(name)
except:
    name = None
    
   

# Convert the data into a DataFrame and perform data cleaning and sorting


 # Extract additional data from the parsed HTML
try:
    # Extracting the headline
    headline_container = linkedin_soup.find("div", {"class": "text-body-medium"})
    headline = headline_container.get_text(separator=" ", strip=True) if headline_container else ""
    print('Headline:', headline)

    # Extracting the location
    location_container = linkedin_soup.find("span", {"class": "text-body-small"})
    location = location_container.get_text(separator=" ", strip=True) if location_container else ""
    print('Location:', location)
    
    # Extract the "about" section
    try:
        about_container = linkedin_soup.find("section", {"id": "about"})
        about = about_container.get_text(separator=" ", strip=True) if about_container else ""
        print('About:', about)
    except Exception as e:
        print(f"Error extracting about section: {e}")
except Exception as e:
    print(f"Error extracting data from linkedin_soup: {e}")

# Extract profile name
try:
    name_container = linkedin_soup.find("div", {"class": "pv-text-details__left-panel"})
    if name_container:
        profile_name = name_container.find("h1").get_text(strip=True)
    else:
        profile_name = ""
    print('Profile Name:', profile_name)
except Exception as e:
    print(f"Error extracting profile name: {e}")
    profile_name = ""

# Extract the "about" section
try:
    about_container = linkedin_soup.find("div", {"class": "display-flex ph5 pv3"})
    if about_container:
        about = about_container.find("span", {"aria-hidden": "true"}).get_text(separator=" ", strip=True)
    else:
        about = ""
    print('About:', about)
except Exception as e:
    print(f"Error extracting about section: {e}")
    about = ""

# Extract the "Service" section
try:
    service_container = linkedin_soup.find_all("span", {"aria-hidden": "true"})
    services = []

    for container in service_container:
        text = container.get_text(separator=" ", strip=True)
        if "✔" in text or "My Service" in text:
            services.append(text)

    services_text = " | ".join(services) if services else ""
    print('Services:', services_text)
except Exception as e:
    print(f"Error extracting services section: {e}")
    services_text = ""

# Extract the "featured" section
try:
    # Find the "Featured" section container
    featured_container = linkedin_soup.find("div", {"class": "artdeco-carousel__content"})
    featured_links = []

    if featured_container:
        # Find all links within the "Featured" section
        links = featured_container.find_all("a", {"class": "optional-action-target-wrapper"})
        for link in links:
            href = link.get("href", "")
            featured_links.append(href)
    else:
        featured_links = []

    featured = " | ".join(featured_links) if featured_links else ""
    print('Featured:', featured)
except Exception as e:
    print(f"Error extracting featured section: {e}")
    featured = ""

# Extract the "experience" section
try:
    # Temukan semua elemen pengalaman di dalam HTML
    experience_containers = linkedin_soup.find_all("li", {"class": "artdeco-list__item"})

    # Filter containers based on the specified class
    experience_containers = [
        container for container in experience_containers
        if container.find("div", {"class": "display-flex align-items-center mr1 t-bold"})
    ]
    experiences = []

    for container in experience_containers:
        # Ambil job title
        job_title_elem = container.find("span", {"aria-hidden": "true"})
        job_title = job_title_elem.get_text(strip=True) if job_title_elem else ""

        # Ambil durasi kerja
        duration_elem = container.find("span", {"class": "pvs-entity__caption-wrapper"})
        duration = duration_elem.get_text(strip=True) if duration_elem else ""

        # Tambahkan data ke daftar pengalaman
        experiences.append({
            "Job Title": job_title,
            "Duration": duration,
        })

    # Tampilkan hasil pengalaman yang ditemukan
    for experience in experiences:
        print(f"Job Title: {experience['Job Title']}")
        print(f"Company: {experience['Company']}")
        print(f"Duration: {experience['Duration']}")
        print(f"Location: {experience['Location']}")
        print("-" * 40)

except Exception as e:
    print(f"Error extracting experiences: {e}")


# Extract education details
try:
    # Temukan semua elemen pendidikan di dalam HTML
    education_containers = linkedin_soup.find_all("li", {"class": "artdeco-list__item"})

    # Filter containers untuk memastikan hanya elemen pendidikan yang diproses
    education_containers = [
        container for container in education_containers
        if container.find("div", {"class": "display-flex align-items-center mr1 hoverable-link-text t-bold"})
        and container.find("span", {"aria-hidden": "true", "class": "pvs-entity__caption-wrapper"})
    ]
    educations = []

    for container in education_containers:
        # Ambil nama institusi pendidikan
        institution_elem = container.find("span", {"aria-hidden": "true"})
        institution = institution_elem.get_text(strip=True) if institution_elem else ""

        # Ambil durasi pendidikan (tahun masuk dan lulus)
        duration_elem = container.find("span", {"class": "pvs-entity__caption-wrapper"})
        duration = duration_elem.get_text(strip=True) if duration_elem else ""

        # Tambahkan data ke daftar pendidikan
        educations.append({
            "Institution": institution,
            "Duration": duration
        })

    # Tampilkan hasil pendidikan yang ditemukan
    for education in educations:
        print(f"Institution: {education['Institution']}")
        print(f"Degree: {education['Degree']}")
        print(f"Duration: {education['Duration']}")
        print("-" * 40)

except Exception as e:
    print(f"Error extracting educations: {e}")


# Add extracted data to posts_data
try:
    # Siapkan data sebagai daftar pasangan kunci dan nilai
    posts_data = [
        {"Attribute": "Username", "Value": company_name},
        {"Attribute": "Profile Name", "Value": profile_name},
        {"Attribute": "Headline", "Value": headline},
        {"Attribute": "Location", "Value": location},
        {"Attribute": "About", "Value": about},
        {"Attribute": "Services", "Value": services_text},
        {"Attribute": "Featured", "Value": featured},
    ]

    posts_data.append({"Attribute": "Experiences and volunteering", "Value": experiences})

    posts_data.append({"Attribute": "Education, interest companies, and interest groups", "Value": educations})

    # Konversi ke DataFrame
    df = pd.DataFrame(posts_data)

    # Ekspor ke file CSV
    csv_file = f"{company_name}_posts_vertical.csv"
    df.to_csv(csv_file, encoding='utf-8', index=False)
    print(f"Data exported to {csv_file}")

except Exception as e:
    print(f"Error processing data: {e}")



