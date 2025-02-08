from llama_index.core.workflow import Context
from llama_index.core import PromptTemplate, Settings
from bs4 import BeautifulSoup
from typing import Optional

import requests
import os
import dotenv
import asyncio

dotenv.load_dotenv()


async def read_job(job_url: str) -> str:
    """
    Useful for scraping job details from a LinkedIn job posting URL.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    # Set up Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        driver.get(job_url)
        wait = WebDriverWait(driver, 10)

        # Extract Job Details
        job_details = {}

        # Get Job Title
        job_details["title"] = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        ).text

        # Get Company Name
        job_details["company"] = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a.topcard__org-name-link")
            )
        ).text

        # Get Location
        job_details["location"] = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.topcard__flavor--bullet")
            )
        ).text

        # Click "See more" button to expand job description if it exists
        try:
            see_more_button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.show-more-less-html__button")
                )
            )
            see_more_button.click()
            # time.sleep(2)  # Allow time for expansion
            await asyncio.sleep(2)  # Allow time for expansion
        except Exception:
            print("No 'See more' button found, continuing...")

        # Extract Job Description
        job_details["description"] = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.show-more-less-html__markup")
            )
        ).text

        return str(job_details)

    except Exception as e:
        print(f"Error: {e}")
        return "An error occured."

    finally:
        driver.quit()


async def read_cv(cv_path: str) -> tuple[str, str]:  # ctx: Context,
    """
    Useful for reading the applicant's CV
    """
    import os

    if cv_path is None or not os.path.exists(cv_path):
        return ("Error loading cv. File path received:", f"{cv_path}")

    with open(os.path.join(cv_path), "r") as file:
        resume_content = file.read()
    # state = await ctx.get("state")
    # state["original_latex_cv"] = resume_content
    # await ctx.set("state", state)
    print(f"Read resume file: {cv_path}")
    tex_to_markdown_prompt_raw = (
        "You are an experienced latex files reader. "
        "Convert the cv below written in latex to markdown. "
        "Respond with the markdown directly. "
        f"CV:\n\n{resume_content}\n\n"
        "Markdown:"
    )
    llm = Settings.llm
    distilled_cv = llm.complete(tex_to_markdown_prompt_raw, formatted=True)
    return resume_content, distilled_cv.text


async def assess_cv(cv_content: str, job_posting: str) -> str:
    """Useful for evaluating the match between a cv and a job posting"""
    from llama_index.core.bridge.pydantic import BaseModel, Field

    class CVAssessment(BaseModel):
        match_score: int = Field(
            description="how much the cv matches the job posting", gt=0, lt=11
        )
        justification: str = Field(
            description="justification for the match score given"
        )
        enhancements: str = Field(
            description="what can be done to make the cv a better match"
        )

    assess_cv_prompt_raw = (
        "You are an experienced cv analyzer. "
        "Your job is to look at the below cv written in markdown and "
        "the job posting after it and evaluate the cv. "
        "Your output should be a match score from 1 to 10, "
        "a justification for the score, and "
        "what can be changed in the cv to make it look like a better fit."
        "\nCV Content:\n\n"
        "{cv_content}\n\n"
        "Job Posting:\n\n"
        "{job_posting}\n\n"
        "Your output:"
    )
    llm = Settings.llm
    assessment = await llm.astructured_predict(
        CVAssessment,
        PromptTemplate(assess_cv_prompt_raw),
        cv_content=cv_content,
        job_posting=job_posting,
    )
    return str(assessment)


async def rewrite_cv(latex_cv: str, job_posting: str, cv_assessment: str) -> str:
    """Useful for professionally rewriting a cv based on match assessment with a job posting"""
    rewrite_cv_prompt_raw = (
        "You are an experienced cv writer. "
        "Your job is to look at the below cv written in latex, "
        "a job posting and a matching assessment made by an expert then "
        "Rewrite the cv in latex adding the enhancements mentioned in the assessment "
        "to make it a better match. "
        "\nCV Content:\n\n"
        f"{latex_cv}\n\n"
        "Job Posting:\n\n"
        f"{job_posting}\n\n"
        "CV Assessment\n\n"
        f"{cv_assessment}\n\n"
        "Your output:"
    )
    llm = Settings.llm
    new_cv = await llm.acomplete(rewrite_cv_prompt_raw)
    with open("new_cv.tex", "w") as f:
        f.write(new_cv.text)
    return new_cv.text


async def scrape_linkedin_jobs(
    ctx: Context,
    job_name: str = "Artificial Intelligence",
    location: str = "Riyadh, Riyadh Region, Saudi Arabia",
) -> str:
    """Useful for scraping LinkedIn jobs related to a certain job name `job_name` in a specific location `location`."""
    # Define the search parameters
    keywords = job_name
    location = location
    url = (
        f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}"
    )

    # Send a GET request to the LinkedIn job search page
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve jobs: {response.status_code}")
        return f"Failed to retrieve jobs: {response.status_code}"

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all job postings
    job_cards = soup.find_all("div", class_="base-card")

    # Create a directory to save job postings
    job_postings = ""

    # Extract and save job details
    for job in job_cards:
        job_posting = ""
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
            job_description_div = job_soup.find(
                "div", class_="show-more-less-html__markup"
            )
            if job_description_div:
                job_description = job_description_div.get_text(strip=True)
            else:
                job_description = "Not Found"

            job_posting += f"Job Title: {job_title}\n"
            job_posting += f"Company: {company_name}\n"
            job_posting += f"Location: {job_location}\n"
            job_posting += f"Job Link: {job_link}\n"
            job_posting += "Job Description:\n"
            job_posting += job_description
            job_posting += "\n\n\n"
            print(job_posting)
            job_postings += job_posting

        except Exception as e:
            print(f"Error processing job: {e}")
            return f"Error processing job: {e}"
    state = await ctx.get("state")
    state["job_postings"] = job_postings
    await ctx.set("state", state)
    return job_postings


async def record_notes(ctx: Context, notes: str, notes_title: str) -> str:
    """Useful for recording notes on a given topic. Your input should be notes with a title to save the notes under."""
    current_state = await ctx.get("state")
    if "research_notes" not in current_state:
        current_state["research_notes"] = {}
    current_state["research_notes"][notes_title] = notes
    await ctx.set("state", current_state)
    return "Notes recorded."


async def review_resume(ctx: Context, review: str) -> str:
    """Useful for reviewing a resume and providing feedback. Your input should be a review of the resume."""
    current_state = await ctx.get("state")
    current_state["review"] = review
    await ctx.set("state", current_state)
    return "Resume reviewed."


async def job_match_review(ctx: Context, job_name: str, review: str) -> str:
    """Useful for scoring the match of a resume and a job posting. Your input should be the match report."""
    current_state = await ctx.get("state")
    current_state[f"job_match_{job_name}"] = review
    await ctx.set("state", current_state)
    return "Job match review done."


async def save_resume(ctx: Context, resume_content: str, filename: str) -> str:
    """Useful for saving the final applicant's resume/CV. filename should be <COMPANY_NAME>_<APPLICANT_NAME>."""

    with open(os.path.join("generated_resumes", f"{filename}.tex"), "w") as file:
        nbytes = file.write(resume_content)
        if nbytes > 0:
            return "Resume was successfully saved."
    return "Couldn't save the resume."


async def main():
    # job_url = "https://www.linkedin.com/jobs/view/3736668354/?alternateChannel=search&refId=%2FLoMFmPfs87o82Sj8yJaOA%3D%3D&trackingId=QXIMymmM9os%2BQaw5lFML%2BA%3D%3D"
    # job_url = "https://www.linkedin.com/jobs/view/4129476404/?alternateChannel=search"
    job_url = "https://www.linkedin.com/jobs/view/4143955732/?alternateChannel=search"
    j = await read_job(job_url)
    print(j)

    cv_tex, cv_md = await read_cv(cv_path="resumes_repo/sample_resume.tex")
    print(cv_md)

    a = await assess_cv(cv_md, j)
    print(a)
    with open("output.md", "w") as f:
        f.write(a)

    cv = await rewrite_cv(cv_tex, j, a)
    print(cv)


if __name__ == "__main__":
    asyncio.run(main())

__all__ = [
    "read_job",
    "read_cv",
    "rewrite_cv",
    "assess_cv",
    "scrape_linkedin_jobs",
    "record_notes",
    "review_resume",
    "job_match_review",
    "save_resume",
]
