from libs.orchestrator.src.state import AgentState
from langchain_core.messages import AIMessage

def booking_node(state: AgentState):
    """
    Handles booking logic. 
    """
    # Simulate processing
    # In reality, this would check the database or call the Availability Service
    
    response = AIMessage(content="I see you want to book an appointment. What date and time works best for you?")
    
    return {
        "messages": [response],
        "next_action": "wait_for_user"
    }
