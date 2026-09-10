import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langgraph_workflow.graph import run_rag_pipeline  # noqa: E402


async def main():
    result = await run_rag_pipeline("What is the company leave policy?")
    print("Workflow result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
