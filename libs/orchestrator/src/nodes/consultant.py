from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from packages.orchestrator.state import AgentState
from packages.core.config import settings

def consultant_node(state: AgentState):
    """
    Answers general user questions using the salon's knowledge base (tenant_config).
    """
    llm = ChatOpenAI(model="gpt-4-turbo-preview", openai_api_key=settings.OPENAI_API_KEY)
    
    tenant_info = state.get("tenant_config", {}).get("knowledge_base", "No specific information available.")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful salon consultant. Use the following information to answer the user's question. If the information isn't there, be polite and say you don't know, or offer to connect them to support.\n\nSalon Info:\n{salon_repo}"),
        ("user", "{input}")
    ])
    
    chain = prompt | llm
    
    last_message = state['messages'][-1].content
    
    response = chain.invoke({
        "salon_repo": tenant_info,
        "input": last_message
    })
    
    return {
        "messages": [response],
        "next_action": "wait_for_user"
    }
