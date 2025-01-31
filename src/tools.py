from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import (
    AgentStream,
    AgentWorkflow,
    ReActAgent,
    FunctionAgent,
    AgentInput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import asyncio
import dotenv


dotenv.load_dotenv()


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
    # if not os.path.exists("job_postings"):
    #     os.makedirs("job_postings")

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

            job_postings += f"Job Title: {job_title}\n"
            job_postings += f"Company: {company_name}\n"
            job_postings += f"Location: {job_location}\n"
            job_postings += f"Job Link: {job_link}\n"
            job_postings += "Job Description:\n"
            job_postings += job_description
            job_postings += "\n\n\n"
            # Create a unique filename based on job title and company name
            # filename = f"{job_title}_{company_name}.txt".replace(" ", "_").replace(
            #     "/", "_"
            # )

            # Save the job details to a text file
            # with open(
            #     os.path.join("job_postings", filename), "w", encoding="utf-8"
            # ) as file:
            #     job_postings += f"Job Title: {job_title}\n")
            #     job_postings += f"Company: {company_name}\n")
            #     job_postings += f"Location: {job_location}\n")
            #     job_postings += f"Job Link: {job_link}\n")
            #     job_postings += "Job Description:\n")
            #     job_postings += job_description)

        except Exception as e:
            print(f"Error processing job: {e}")
            return f"Error processing job: {e}"
    state = await ctx.get("state")
    state["job_postings"] = job_postings
    await ctx.set("state", state)
    return job_postings


async def main():
    tool_spec = DuckDuckGoSearchToolSpec()
    linkedin_scraping_tool = FunctionTool.from_defaults(async_fn=scrape_linkedin_jobs)

    research_agent = FunctionAgent(
        name="JobResearcher",
        description="Useful for searching for job postings about certain job names.",
        system_prompt="You are a world-class job researcher who can search the internet or scrape linkedin jobs for information.",
        tools=([linkedin_scraping_tool] + tool_spec.to_tool_list()),
        llm=OpenAI(model="gpt-4o-mini"),
    )
    workflow = AgentWorkflow(
        agents=[research_agent], root_agent=research_agent.name, verbose=True
    )

    handler = workflow.run(
        "Get all the AI related jobs in Riyadh Saudi Arabia for senior level",
    )

    await stream_agent_output(handler)


if __name__ == "__main__":
    asyncio.run(main())
