from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import (
    AgentStream,
    AgentWorkflow,
    FunctionAgent,
    AgentInput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
from llama_index.llms.openai import OpenAI
import asyncio
import dotenv
from .tools import (
    read_job,
    read_cv,
    assess_cv,
    rewrite_cv,
    save_resume,
    # scrape_linkedin_jobs,
    # record_notes,
    # review_resume,
    # job_match_review,
)
from colorama import Fore, Back, Style
from tkinter.constants import YES

dotenv.load_dotenv()

with open("job_postings/sample_job_posting.txt", "r") as f:
    sample_job_posting = f.read()


async def stream_agent_output(handler) -> None:
    current_agent = None
    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            print(f"\n{'='*50}")
            print(f"🤖 {Fore.GREEN}Agent: {current_agent}")
            print(Style.RESET_ALL, end="")
            print(f"{'='*50}\n")

        if isinstance(event, AgentStream):
            if event.delta:
                print(Fore.CYAN + event.delta, end="", flush=True)
        elif isinstance(event, AgentInput):
            print(f"📥 {Fore.CYAN}Input:", event.input)

        elif isinstance(event, AgentOutput):
            if event.response.content:
                print("📤 Output:", event.response.content)
            if event.tool_calls:
                print(
                    f"🛠️  {Fore.GREEN}Planning to use tools:",
                    [call.tool_name for call in event.tool_calls],
                )
        elif isinstance(event, ToolCallResult):
            print(f"🔧 {Style.NORMAL}Tool Result ({event.tool_name}):")
            print(f"  {Style.NORMAL}Arguments: {event.tool_kwargs}")
            print(f"  {Style.NORMAL}Output: {event.tool_output}")

        elif isinstance(event, ToolCall):
            print(f"🔨 {Fore.GREEN}Calling Tool: {event.tool_name}")
            print(f"  {Fore.GREEN}With arguments: {event.tool_kwargs}")
        print(Style.RESET_ALL, end="")


async def main():
    default_llm = OpenAI(model="gpt-4o-mini")
    # advanced_llm = OpenAI(model="gpt-4o")
    # reasoning_llm = OpenAI(model="o1-mini")

    # tool_spec = DuckDuckGoSearchToolSpec()
    job_read_tool = FunctionTool.from_defaults(async_fn=assess_cv)
    cv_read_tool = FunctionTool.from_defaults(async_fn=read_cv)
    cv_assess_tool = FunctionTool.from_defaults(async_fn=read_cv)
    cv_rewrite_tool = FunctionTool.from_defaults(async_fn=rewrite_cv)
    save_cv_tool = FunctionTool.from_defaults(async_fn=save_resume)

    # linkedin_scraping_tool = FunctionTool.from_defaults(async_fn=scrape_linkedin_jobs)
    # load_resume_tool = FunctionTool.from_defaults(async_fn=load_resume)
    # record_notes_tool = FunctionTool.from_defaults(async_fn=record_notes)
    # resume_review_tool = FunctionTool.from_defaults(async_fn=review_resume)
    # job_match_review_tool = FunctionTool.from_defaults(async_fn=job_match_review)

    # research_agent = FunctionAgent(
    #     name="JobResearcher",
    #     description="Useful for searching for job postings about certain job names.",
    #     system_prompt="You are a world-class job researcher who can search the internet or scrape linkedin jobs for information.",
    #     tools=[linkedin_scraping_tool, record_notes_tool],
    #     llm=default_llm,
    # )

    # job_posting_analysis_agent = FunctionAgent(
    #     name="JobDescriptionAnalyzer",
    #     description=(
    #         "Useful for analyzing job posting description including extracting keywords, "
    #         "skills, roll expectations, responsibilities, and required qualifications."
    #     ),
    #     system_prompt=(
    #         "You are a sharp and experienced job description analyzer. Your job is to analyze job descriptions and extract "
    #         "keywords, skills, roll expectations, responsibilities, and required qualifications. You need to "
    #         "use the JobResearcher agent first to get job descriptions."
    #     ),
    #     tools=[record_notes_tool],
    #     llm=default_llm,
    # )

    # resume_analysis_agent = FunctionAgent(
    #     name="ResumeAnalyzer",
    #     description=(
    #         "Useful for analyzing resumes and CVs by extracting key information."
    #     ),
    #     system_prompt=(
    #         "You are a sharp and experienced resume/CV analyzer. Your job is to analyze the resume/CV and extract "
    #         "keywords, skills, past experiences, qualifications, past projects and the applicant's personal information. "
    #     ),
    #     tools=[load_resume_tool, record_notes_tool],
    #     llm=default_llm,
    #     can_handoff_to=["JobMatcher"],
    # )

    # job_matching_agent = FunctionAgent(
    #     name="JobMatcher",
    #     description=(
    #         "Useful for matching possible job postings to the applicant's resume/CV."
    #     ),
    #     system_prompt=(
    #         "You are a job matching assistant capable of looking at job postings and applicant's resume/CV "
    #         "and accurately selecting the best matching job postings to the applicant's resume/CV. "
    #         "You have to select more than one job postings and provide a justification for your selection. "
    #         "You must use the ResumeAnalyzer and JobDescriptionAnalyzer agents first to generate your output."
    #     ),
    #     tools=[job_match_review_tool],
    #     llm=default_llm,
    # )

    # resume_review_agent = FunctionAgent(
    #     name="ResumeReviewer",
    #     description=(
    #         "Useful for reviewing an applicant's resume/CV against a job description."
    #     ),
    #     system_prompt=(
    #         "You are an expoert resume/CV reviewer. Your job is to read the job description, and review the "
    #         "applicant's resume/CV and pinpoint strong and weak areas "
    #         "of the candidate and recommend modifications and/or rejection of the resume/CV."
    #     ),
    #     tools=[resume_review_tool],
    #     llm=default_llm,
    # )

    # resume_writer_agent = FunctionAgent(
    #     name="ResumeWriter",
    #     description=("Useful for writing resumes in LaTeX."),
    #     system_prompt=(
    #         "You are a creative resume/CV writer with an experienced eye which knows how to convince "
    #         "the job's HR manager with the applicant's qualifications. "
    #         "Given a current resume/CV and a list of "
    #         "recommendations for enhancements made specifically for a certain job posting, "
    #         "this agent will rewrite the resume/CV to target that particular job in the best possible way. "
    #         "Before you save the file, make sure that the new resume meets the job posting's requirements."
    #     ),
    #     tools=[save_resume_tool],
    #     llm=default_llm,
    # )
    agent = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[
            cv_read_tool,
            job_read_tool,
            cv_assess_tool,
            cv_rewrite_tool,
            save_cv_tool,
        ],
        llm=default_llm,
        system_prompt=(
            "You are a professional HR Consultant. "
            "Your job is to evaluate CVs provided by the user against job postings and "
            "Give advice on what to improve on the CV and even rewrite the CV to add "
            "the recommended changes. "
            "You should always verify from the user if he wants to save the final written CV."
        ),
    )

    # workflow = AgentWorkflow(
    #     agents=[
    #         research_agent,
    #         job_posting_analysis_agent,
    #         resume_analysis_agent,
    #         job_matching_agent,
    #         resume_review_agent,
    #         resume_writer_agent,
    #     ],
    #     root_agent=research_agent.name,
    #     initial_state={"resume_file_name": "sample_resume.tex"},
    #     timeout=30 * 360,
    # )

    prompt = input("🖊️ User: ")
    handler = agent.run(prompt)
    await stream_agent_output(handler)


if __name__ == "__main__":
    asyncio.run(main())
