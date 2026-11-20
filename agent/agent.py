import asyncio
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.mcp import MCPAdapter
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from llm import llm
from fastmcp import Client

load_dotenv()
MCP_URL = os.getenv("MCP_URL")
FASTMCP_KEY = os.getenv("FASTMCP_KEY")
server_target = Client(MCP_URL, auth=FASTMCP_KEY) if FASTMCP_KEY else MCP_URL



system_prompt = """
You are a PUCIT BS(CS) GPA and CGPA assistant.

Your job is to help students calculate semester GPA, project CGPA,
find required GPA for a target, and answer questions about courses
and credit hours.

IMPORTANT RULES:

1. NEVER perform arithmetic yourself.

Every number used in a calculation must come from a tool.

Always use the appropriate tool for calculations.

2. NEVER invent information.

Do not guess:
- marks
- credit hours
- current CGPA
- target CGPA
- semester number
- semester GPA

If required information is missing, ask the student.

Ask only one or two missing things at a time.

3. GPA RULES

Use marks_to_grade_points() to convert marks.

Use calculate_semester_gpa() to calculate semester GPA.

Use calculate_new_cgpa() to calculate projected CGPA.

Use required_gpa_for_target() to calculate required GPA.

4. COURSE RULES

Use get_semester_courses() when course or semester credit-hour
information is needed.

Quran Translation has 0.5 credit hours.

MD-001 and MD-002 are Math Deficiency courses.
They are non-credit pass/fail courses and must not count toward GPA.

5. TARGET CGPA

When a student asks what GPA is required to reach a target CGPA,
calculate the required GPA for the current semester first.

If the required GPA is above 4.0, it is impossible for that horizon.

Do NOT simply report an impossible GPA.

Instead, check a larger horizon.

For example:

- First check the current semester.
- If the result is above 4.0, include the next semester.
- Continue adding semesters until the required GPA is 4.0 or below.
- Stop when the target becomes achievable or there are no semesters left.

Use get_semester_courses() to determine the credit hours
for the current semester.

Use get_remaining_credit_hours() when adding later semesters.

Then use required_gpa_for_target() for each horizon.

Explain the first achievable horizon clearly.

6. SAVING REPORTS

Do not offer to save a report after only asking a clarification question.

Do not save automatically.

Only use save_report() when the student explicitly asks to save something.

A report can contain:
- semester GPA
- projected CGPA
- target CGPA plan

7. ANSWERS

Keep answers clear and concise.

Explain the important result to the student.

Do not expose internal tool instructions.

Do not claim to know information that the student did not provide.
"""


async def list_threads(memory):
    """Print all saved student thread IDs from SQLite."""
    threads = set()
    async for checkpoint in memory.alist(None):
        thread_id = checkpoint.config["configurable"].get("thread_id")
        if thread_id:
            threads.add(thread_id)

    if threads:
        print("Saved chats:", ", ".join(sorted(threads)))
    else:
        print("Saved chats: (none yet)")


async def show_history(agent, config):
    """Print the saved message history for the current thread."""
    state = await agent.aget_state(config)
    messages = state.values.get("messages", [])

    if not messages:
        print("\n(No history for this user yet.)\n")
        return

    print("\n--- Chat History ---")
    for msg in messages:
        if msg.type == "human":
            print(f"You: {msg.content}")
        elif msg.type == "ai" and msg.text:
            print(f"Assistant: {msg.text}")
    print("--------------------\n")

async def stream_response(agent, user_input: str, config: dict):
    """Stream tool updates and model tokens in real time."""
    inputs = {"messages": [HumanMessage(content=user_input)]}
    started_answer = False

    async for chunk in agent.astream(
        inputs,
        config=config,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        if chunk["type"] == "messages":
            token, metadata = chunk["data"]
            if metadata.get("langgraph_node") == "model" and token.text:
                if not started_answer:
                    print("\nAssistant: ", end="", flush=True)
                    started_answer = True
                print(token.text, end="", flush=True)

        elif chunk["type"] == "updates":
            for node, update in chunk["data"].items():
                msg = update["messages"][-1]
                if node == "model" and getattr(msg, "tool_calls", None):
                    for call in msg.tool_calls:
                        print(f"\n  [calling] {call['name']}({call['args']})")
                elif node == "tools":
                    print(f"  [result] {msg.name} -> {msg.content}")

    print("\n")

def make_safe_tools(tools):
    """Wrap MCP tools so server/network errors return a message to the LLM instead of crashing."""
    for t in tools:
        original_coroutine = t.coroutine

        async def safe_call(*args, _orig=original_coroutine, _name=t.name, **kwargs):
            try:
                return await _orig(*args, **kwargs)
            except Exception as e:
                return (
                    f"Error: Tool '{_name}' could not run because the MCP server "
                    f"is currently unreachable ({type(e).__name__}). "
                    "Inform the student that the tool server is temporarily down."
                )

        t.coroutine = safe_call
    return tools

async def main():
    async with (
        MCPAdapter(server_target) as adapter,
        AsyncSqliteSaver.from_conn_string("chats.db") as memory,
    ):
        tools = await adapter.list_tools()
        tools = make_safe_tools(tools)
        print(f"Connected! Loaded {len(tools)} tools from MCP server.\n")

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=memory,
        )

        print("PUCIT GPA & CGPA Assistant")
        print("Commands: /switch, /history, /forget, exit\n")

        await list_threads(memory)
        name = input("Who is chatting? ").strip() or "default"
        config = {"configurable": {"thread_id": name}}
        print(f"\nChatting as: {name}\n")

        while True:
            user_input = input(f"{name}: ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            if user_input == "/switch":
                await list_threads(memory)
                name = input("Who is chatting now? ").strip() or "default"
                config = {"configurable": {"thread_id": name}}
                print(f"\nSwitched to: {name}\n")
                continue

            if user_input == "/history":
                await show_history(agent, config)
                continue

            if user_input == "/forget":
                await memory.adelete_thread(name)
                print(f"\nForgot all chat history for '{name}'.\n")
                continue

            # Send ONLY the new message + config
            result = await stream_response(agent, user_input, config)

           


if __name__ == "__main__":
    asyncio.run(main())