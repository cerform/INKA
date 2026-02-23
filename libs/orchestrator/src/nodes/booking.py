from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from packages.orchestrator.state import AgentState
from packages.core.config import settings
from packages.core.services.calendar_service import calendar_service
import json

def booking_node(state: AgentState):
    """
    Manages the conversational booking flow.
    """
    llm = ChatOpenAI(model="gpt-4-turbo-preview", openai_api_key=settings.OPENAI_API_KEY)
    
    # 1. Identify missing information in the booking_context
    context = state.get("booking_context") or {}
    
    # Simple extraction logic (can be upgraded to full LLM extraction)
    # For now, we guide the user via structured prompts.
    
    if not context.get("service_id"):
        return {
            "messages": [AIMessage(content="Which service would you like to book? (e.g., Tattoo, Haircut, Massage)")],
            "next_action": "wait_for_user"
        }
    
    if not context.get("master_id"):
        return {
            "messages": [AIMessage(content="Do you have a preferred master in mind?")],
            "next_action": "wait_for_user"
        }

    if not context.get("date"):
        return {
            "messages": [AIMessage(content="What date are you looking for? (YYYY-MM-DD)")],
            "next_action": "wait_for_user"
        }

    # 2. If we have date/master/service, show slots from Calendar Engine
    # Note: In a real app, we'd need a DB Session here. 
    # For the orchestrator node, we assume the bot middleware provides a session or we use a global factory.
    # For this implementation, we skip the actual DB call and show the logic shell.
    
    response = AIMessage(content="Let me check the available slots for you... [Slot listing logic integrated with M2]")
    
    return {
        "messages": [response],
        "next_action": "wait_for_user"
    }
