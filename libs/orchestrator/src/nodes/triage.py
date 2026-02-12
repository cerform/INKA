from langchain_core.messages import SystemMessage, HumanMessage
from libs.orchestrator.src.state import AgentState

# Placeholder for actual LLM call. 
# In a real implementation, we would inject a ChatOpenAI or similar client.

def triage_node(state: AgentState):
    """
    Analyzes the last message and decides the next step.
    For MVP, we use simple keyword matching or a simulated LLM classification.
    """
    last_message = state['messages'][-1]
    content = last_message.content.lower()

    if "book" in content or "appointment" in content:
        return {"current_intent": "booking", "next_action": "route_to_booking"}
    elif "price" in content or "style" in content or "info" in content:
        return {"current_intent": "info", "next_action": "route_to_consultant"}
    elif "help" in content or "support" in content:
        return {"current_intent": "support", "next_action": "route_to_support"}
    else:
        # Default fallthrough
        return {"current_intent": "general", "next_action": "respond_general"}

