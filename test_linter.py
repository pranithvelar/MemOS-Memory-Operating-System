import asyncio
from datetime import datetime
from src.agent.loop import AgentLoop

async def main():
    agent = AgentLoop(workspace_dir="workspace", session_id="test_linter")
    
    print("\n--- Test 1: No Conflict ---")
    question1 = "I have an important exam on Thursday."
    print(f"User: {question1}")
    res1 = await agent.run(question1)
    print(f"Agent: {res1}")

    print("\n--- Test 2: Overlapping Conflict ---")
    question2 = "I'm travelling to Kerala from Monday to Friday."
    print(f"User: {question2}")
    res2 = await agent.run(question2)
    print(f"Agent: {res2}")
    
if __name__ == "__main__":
    asyncio.run(main())
