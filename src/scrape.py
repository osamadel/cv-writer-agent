import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime


def scrape_linkedin_jobs():
    # Define the search parameters
    keywords = "Artificial Intelligence"
    location = "Riyadh, Riyadh Region, Saudi Arabia"
    url = (
        f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}"
    )

    # Send a GET request to the LinkedIn job search page
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve jobs: {response.status_code}")
        return

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all job postings
    job_cards = soup.find_all("div", class_="base-card")

    # Create a directory to save job postings
    if not os.path.exists("job_postings"):
        os.makedirs("job_postings")

    # Extract and save job details
    for job in job_cards:
        try:
            job_title = job.find("h3", class_="base-search-card__title").get_text(
                strip=True
            )
            company_name = job.find("h4", class_="base-search-card__subtitle").get_text(
                strip=True
            )
            job_location = job.find(
                "span", class_="job-search-card__location"
            ).get_text(strip=True)
            job_link = job.find("a", class_="base-card__full-link")["href"]

            # Fetch the job description
            job_response = requests.get(job_link)
            job_soup = BeautifulSoup(job_response.text, "html.parser")
            job_description = job_soup.find(
                "div", class_="show-more-less-html__markup"
            ).get_text(strip=True)

            # Create a unique filename based on job title and company name
            filename = f"{job_title}_{company_name}.txt".replace(" ", "_").replace(
                "/", "_"
            )

            # Save the job details to a text file
            with open(
                os.path.join("job_postings", filename), "w", encoding="utf-8"
            ) as file:
                file.write(f"Job Title: {job_title}\n")
                file.write(f"Company: {company_name}\n")
                file.write(f"Location: {job_location}\n")
                file.write(f"Job Link: {job_link}\n")
                file.write("Job Description:\n")
                file.write(job_description)

        except Exception as e:
            print(f"Error processing job: {e}")


if __name__ == "__main__":
    scrape_linkedin_jobs()
