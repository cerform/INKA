from langgraph.graph import StateGraph, END
from libs.orchestrator.src.state import AgentState
from libs.orchestrator.src.nodes.triage import triage_node
from libs.orchestrator.src.nodes.booking import booking_node

def route_decision(state: AgentState):
    """
    conditional edge function to determine where to go after Triage.
    """
    action = state.get("next_action")
    if action == "route_to_booking":
        return "booking"
    elif action == "route_to_consultant":
        return "consultant" # TODO: Implement Consultant
    elif action == "route_to_support":
        return "support"    # TODO: Implement Support
    else:
        return END

def create_orchestrator_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("booking", booking_node)

    # Set Entry Point
    workflow.set_entry_point("triage")

    # Add Edges
    workflow.add_conditional_edges(
        "triage",
        route_decision,
        {
            "booking": "booking",
            "consultant": END, # Placeholder
            "support": END,    # Placeholder
            END: END
        }
    )

    workflow.add_edge("booking", END)

    return workflow.compile()
