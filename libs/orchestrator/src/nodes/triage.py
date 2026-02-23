from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from packages.orchestrator.state import AgentState
from packages.core.config import settings

# Placeholder for actual LLM call. 
# In a real implementation, we would inject a ChatOpenAI or similar client.

def triage_node(state: AgentState):
    """
    Analyzes the last message and decides the next step using an LLM.
    """
    llm = ChatOpenAI(model="gpt-4-turbo-preview", openai_api_key=settings.OPENAI_API_KEY)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a triage assistant for a salon bot. Classify the user intent into one of these categories: 'booking', 'info', 'support', or 'general'. Respond ONLY with the category name."),
        ("user", "{input}")
    ])
    
    chain = prompt | llm
    
    # Get last user message
    last_message = state['messages'][-1].content
    
    response = chain.invoke({"input": last_message})
    category = response.content.strip().lower()
    
    mapping = {
        "booking": ("booking", "route_to_booking"),
        "info": ("info", "route_to_consultant"),
        "support": ("support", "route_to_support"),
    }
    
    intent, action = mapping.get(category, ("general", "respond_general"))
    
    return {"current_intent": intent, "next_action": action}

