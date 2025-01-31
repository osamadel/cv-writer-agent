# IMPORTS
# from __future__ import annotations
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import (
    AgentWorkflow,
    AgentInput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
    AgentStream,
)
from llama_index.core.workflow import (
    Context,
    JsonSerializer,
    InputRequiredEvent,
    HumanResponseEvent,
)
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
import os
import asyncio


# FUNCTIONS DEFINITONS
async def search_web(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return str(await client.search(query))


async def dangerous_task(ctx: Context) -> str:
    """A dangerous task that requires human confirmation."""
    ctx.write_event_to_stream(
        InputRequiredEvent(
            prefix="Are you sure you want to proceed?",
            user_name="Logan",
        )
    )
    response = await ctx.wait_for_event(
        HumanResponseEvent, requirements={"user_name": "Logan"}
    )
    if response.response == "yes":
        return "Dangerous task completed successfully."
    else:
        return "Dangerous task aborted."


async def set_name(ctx: Context, name: str) -> str:
    """Useful for setting names"""
    state = await ctx.get("state")
    state["name"] = name
    await ctx.set("state", state)
    return f"Name set to {name}"


async def stream_agent_output(handler):
    async for event in handler.stream_events():
        if isinstance(event, AgentStream):
            print(event.delta, end="", flush=True)


async def main():
    load_dotenv()

    llm = OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    workflow = AgentWorkflow.from_tools_or_functions(
        # [search_web, set_name],
        [dangerous_task],
        llm=llm,
        # system_prompt="You are a helpful assistant who search the internet for information and can set names.",
        system_prompt="You are a helpful assistant that can perform dangerous tasks.",
        initial_state={"name": "unset"},
    )
    ctx = Context(workflow)
    dangerous_task.model_rebuild()
    handler = workflow.run(user_msg="My name is Osama Adel", verbose=True, ctx=ctx)

    await stream_agent_output(handler)

    ctx_dict = ctx.to_dict(serializer=JsonSerializer())
    print(f"ctx_dict: {ctx_dict}\n")

    restored_ctx = Context.from_dict(workflow, ctx_dict, serializer=JsonSerializer())

    handler = workflow.run(
        user_msg="What about Mekkah?", verbose=True, ctx=restored_ctx
    )
    await stream_agent_output(handler)
    response = await workflow.run(
        user_msg="My name is Osama Adel", verbose=True, ctx=ctx
    )
    print(str(response))
    state = await ctx.get("state")
    print(f"{state["name"]}")

    handler = workflow.run(user_msg="I want to proceed with the dangerous task.")

    async for event in handler.stream_events():
        if isinstance(event, InputRequiredEvent):
            response = input(event.prefix).strip().lower()
            handler.ctx.send_event(
                HumanResponseEvent(
                    response=response,
                    user_name=event.user_name,
                )
            )

    response = await handler
    print(str(response))


if __name__ == "__main__":
    asyncio.run(main())
