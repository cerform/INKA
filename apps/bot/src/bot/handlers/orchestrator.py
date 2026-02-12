from telegram import Update
from telegram.ext import ContextTypes, Router
from langchain_core.messages import HumanMessage, AIMessage
from libs.orchestrator.src.graph import create_orchestrator_graph

orchestrator_router = Router()

# Initialize the graph once
graph = create_orchestrator_graph()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for the Orchestrator.
    """
    user_text = update.message.text
    user_id = str(update.effective_user.id)
    
    # Retrieve history from context (or DB in production)
    if "messages" not in context.user_data:
        context.user_data["messages"] = []
    
    # Add user message
    context.user_data["messages"].append(HumanMessage(content=user_text))
    
    # Prepare state
    initial_state = {
        "messages": context.user_data["messages"],
        "user_id": user_id,
        "user_profile": {} # Mock
    }
    
    # Run Graph
    # We use invoke for synchronous-like behavior in this async handler
    # For a real async graph, we'd use ajoin/astream
    result = await graph.ainvoke(initial_state)
    
    # Get last message from result
    last_message = result["messages"][-1]
    
    # Update history
    context.user_data["messages"] = result["messages"]
    
    # Send response back to Telegram
    if isinstance(last_message, AIMessage):
        await update.message.reply_text(last_message.content)
    else:
        # Fallback
        await update.message.reply_text("I'm not sure what to do next.")

# Register the handler
from telegram.ext import MessageHandler, filters
orchestrator_router.message.filter(filters.TEXT & ~filters.COMMAND)(handle_message)
