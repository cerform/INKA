from aiogram import Router, types
from packages.orchestrator.graph import create_orchestrator_graph

from langchain_core.messages import HumanMessage

router = Router()
orchestrator_graph = create_orchestrator_graph()

@router.message()
async def handle_orchestrator_message(message: types.Message):
    """
    Passes the user message to the LangGraph orchestrator 
    and returns the agent's response.
    """
    # 1. Prepare initial state
    # In a real app, we'd load these from Redis/DB
    state = {
        "messages": [HumanMessage(content=message.text)],
        "user_id": str(message.from_user.id),
        "tenant_config": {
            "knowledge_base": "Our salon is open 10-19. Prices start from $50."
        },
        "booking_context": {}
    }
    
    # 2. Run the Graph
    final_state = orchestrator_graph.invoke(state)
    
    # 3. Get the last AI message
    last_ai_message = final_state["messages"][-1]
    
    await message.answer(last_ai_message.content)

orchestrator_router = router
