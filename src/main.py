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
from .tools import scrape_linkedin_jobs

dotenv.load_dotenv()


async def stream_agent_output(handler) -> None:
    current_agent = None
    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            print(f"\n{'='*50}")
            print(f"🤖 Agent: {current_agent}")
            print(f"{'='*50}\n")

        if isinstance(event, AgentStream):
            if event.delta:
                print(event.delta, end="", flush=True)
        elif isinstance(event, AgentInput):
            print("📥 Input:", event.input)

        elif isinstance(event, AgentOutput):
            if event.response.content:
                print("📤 Output:", event.response.content)
            if event.tool_calls:
                print(
                    "🛠️  Planning to use tools:",
                    [call.tool_name for call in event.tool_calls],
                )
        elif isinstance(event, ToolCallResult):
            print(f"🔧 Tool Result ({event.tool_name}):")
            print(f"  Arguments: {event.tool_kwargs}")
            print(f"  Output: {event.tool_output}")

        elif isinstance(event, ToolCall):
            print(f"🔨 Calling Tool: {event.tool_name}")
            print(f"  With arguments: {event.tool_kwargs}")


async def main():
    default_llm = OpenAI(model="gpt-4o-mini")
    # advanced_llm = OpenAI(model="gpt-4o")
    # reasoning_llm = OpenAI(model="o1-mini")

    tool_spec = DuckDuckGoSearchToolSpec()
    linkedin_scraping_tool = FunctionTool.from_defaults(async_fn=scrape_linkedin_jobs)

    research_agent = FunctionAgent(
        name="JobResearcher",
        description="Useful for searching for job postings about certain job names.",
        system_prompt="You are a world-class job researcher who can search the internet or scrape linkedin jobs for information.",
        tools=([linkedin_scraping_tool] + tool_spec.to_tool_list()),
        llm=default_llm,
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
