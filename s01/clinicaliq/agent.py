"""
clinicaliq/agent.py
-------------------
Graph construction and the terminal loop.

Run the agent from the session folder:
    cd s01/
    python -m clinicaliq.agent

Session 1 graph:
    START --> respond --> END
"""

import sqlite3
from unittest import result
from uuid import uuid4
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, END, StateGraph
from .config import CHECKPOINT_DB

from .nodes import respond,classify,escalate,decline,route_query
from .state import ClinicalIQState


# ---------------------------------------------------------------------------
# TODO 5 of 5 -- build_graph
# ---------------------------------------------------------------------------
# Implement build_graph() so it:
#
#   1. Creates a StateGraph:
#        builder = StateGraph(ClinicalIQState)
#
#   2. Registers the respond node:
#        builder.add_node("respond", respond)
#
#   3. Sets the entry point (first node to run):
#        builder.set_entry_point("respond")
#
#   4. Connects respond → END (the graph exits after one response):
#        builder.add_edge("respond", END)
#
#   5. Compiles and returns the graph:
#        return builder.compile()
#
# ---------------------------------------------------------------------------

def build_graph(checkpointer=None):
    builder = StateGraph(ClinicalIQState)
    builder.add_node("respond", respond)
    builder.add_node("classify", classify)
    builder.add_node("escalate", escalate)
    builder.add_node("decline", decline)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_query, {
        "respond": "respond",
        "escalate": "escalate",
        "decline": "decline"
    })
    builder.add_edge("respond", END)
    builder.add_edge("escalate", END)
    builder.add_edge("decline", END)

    return builder.compile(checkpointer=checkpointer)




# ---------------------------------------------------------------------------
# Terminal loop (provided -- no changes needed)
# ---------------------------------------------------------------------------

def run() -> None:
    conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
    _graph  = build_graph(checkpointer=SqliteSaver(conn)) # terminal app opts into disk persistence explicit
    thread_id = str(uuid4())
    config   = {"configurable": {"thread_id": thread_id}}
    print("=" * 55)
    print("  ClinicalIQ | Apollo Health Clinic")
    print("  Type 'quit' to exit")
    print("=" * 55)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nClinicalIQ: Session ended. Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "bye"}:
            print("\nClinicalIQ: Thank you for choosing Apollo Health Clinic. Goodbye!")
            break

        result = _graph.invoke({"customer_message": user_input, "response": ""}, config=config)
        route = result.get("query_type", "?")
        print(f"\n[Routed: {route}]")
        print(f"\nClinicalIQ: {result['response']}")


if __name__ == "__main__":
    run()
