from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    """
    The state of the agent in the LangGraph.
    """
    messages: Annotated[List[AnyMessage], add_messages]
    user_id: str
    user_profile: Optional[dict]
    current_intent: Optional[str]  # 'booking', 'info', 'support', 'general'
    next_action: Optional[str]
    booking_context: Optional[dict] # partial booking data
    tenant_config: Optional[dict]  # Salon-specific rules, price list, etc.
    session_metadata: Optional[dict] # e.g., thread_id, start_time
