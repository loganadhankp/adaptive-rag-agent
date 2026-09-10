import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langgraph_workflow.nodes.grader import grade_documents  # noqa: E402
from langgraph_workflow.nodes.retriever import retrieve_documents  # noqa: E402


def main():
    state = {"question": "What is the company leave policy?", "documents": []}
    res = retrieve_documents(state)
    print("Retrieved:", len(res.get("documents", [])))
    state.update(res)
    res2 = grade_documents(state)
    print("Graded, filtered docs:", len(res2.get("documents", [])))
    print("Relevance scores sample:", res2.get("relevance_scores"))


if __name__ == "__main__":
    main()
