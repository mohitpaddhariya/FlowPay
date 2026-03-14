from datetime import datetime
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.contact import ContactUpdate
from app.models.razorpay import CreatePaymentLinkRequest

# use the global instances since main.py initializes them first.
# We will import them inside the tools to prevent circular imports on startup.


class AgentState(TypedDict):
    """The state that gets passed around between nodes."""
    messages: Annotated[list[BaseMessage], add_messages]


# ------------------------------------------------------------------ #
#  Tools
# ------------------------------------------------------------------ #

@tool
def lookup_contact_tool(name: str) -> list[dict]:
    """
    Search for a customer by their name in the CRM (Google Sheets).
    Returns a list of matching contacts (name and email).
    Use this when you need an email address to create a payment link.
    If it returns multiple results, ask the user to clarify which one they meant.
    """
    from app.main import sheets_service
    
    # Our sheet service find_contact returns the *first* match.
    # We should alter it to find *all* matches if possible, but for now we
    # will do a manual filter of all contacts.
    all_contacts = sheets_service.get_all_contacts()
    
    matches = []
    for c in all_contacts:
        if name.lower() in c.name.lower():
            matches.append({"name": c.name, "email": c.email})
            
    return matches


@tool
def update_contact_email_tool(name: str, new_email: str) -> str:
    """
    Updates or inserts a customer's email address in the CRM under their name.
    Use this if the customer's email is missing or incorrect and the user provides a new one.
    """
    from app.main import sheets_service
    from app.models.contact import ContactCreate
    
    # Try to update an existing contact first
    result = sheets_service.update_contact_by_name(name, ContactUpdate(email=new_email))
    if result is None:
        # Contact doesn't exist yet — insert a new one
        sheets_service.add_contact(ContactCreate(name=name, email=new_email))
        return f"New contact added to CRM: {name} ({new_email})."
    return f"Successfully updated CRM. {name}'s email is now {new_email}."


@tool
def create_payment_link_tool(
    name: str, 
    email: str, 
    amount: float, 
    description: str, 
    due_date: str | None = None,
    min_partial_amount: float | None = None
) -> str:
    """
    Creates a Razorpay payment link for the customer.
    IMPORTANT: You MUST have the exact Name, Email, Amount, and Description before calling this!
    If 'due_date' (YYYY-MM-DD strict format) or 'min_partial_amount' are provided by the user, pass them here.
    If the user asks for partial payments or installments, you MUST ask them what the min_partial_amount should be.
    If the user does not specify a due date, leave it as None.
    """
    from app.routers.razorpay import create_payment_link as create_payment_link_router
    
    try:
        data = CreatePaymentLinkRequest(
            name=name,
            email=email,
            amount=amount,
            description=description,
            due_date=due_date,
            min_partial_amount=min_partial_amount
        )
        
        # This router internally creates the Razorpay link, saves to Google Sheets, and sends the Email!
        result = create_payment_link_router(data)
        
        return f"Payment link created successfully and emailed to {name}. URL: {result.short_url}"
    except Exception as e:
        return f"Failed to create payment link: {str(e)}"


@tool
def get_all_contacts_tool() -> list[dict]:
    """Retrieve a list of all contacts in the CRM."""
    from app.main import sheets_service
    contacts = sheets_service.get_all_contacts()
    return [{"name": c.name, "email": c.email} for c in contacts]


@tool
def add_contact_tool(name: str, email: str) -> str:
    """Add a new contact to the CRM with their name and email."""
    from app.main import sheets_service
    from app.models.contact import ContactCreate
    sheets_service.add_contact(ContactCreate(name=name, email=email))
    return f"Successfully added {name} ({email}) to the CRM."


@tool
def get_all_payments_tool() -> list[dict]:
    """Retrieve all payment records from the CRM."""
    from app.main import sheets_service
    payments = sheets_service.get_all_payments()
    return [p.model_dump() for p in payments]


@tool
def find_payments_by_email_tool(email: str) -> list[dict]:
    """Retrieve all payment records for a specific email address from the CRM."""
    from app.main import sheets_service
    payments = sheets_service.find_payments_by_email(email)
    return [p.model_dump() for p in payments]


@tool
def cancel_payment_link_tool(link_id: str) -> str:
    """
    Cancel an active Razorpay payment link.
    Requires the exact Razorpay Link ID (e.g. 'plink_XYZ123').
    """
    from app.routers.razorpay import cancel_payment_link
    try:
        cancel_payment_link(link_id)
        return f"Successfully cancelled payment link {link_id}"
    except Exception as e:
        return f"Failed to cancel link {link_id}: {str(e)}"


@tool
def sync_payment_link_tool(link_id: str) -> str:
    """
    Check the latest status of a payment link (e.g. to see if it was paid) and update the Google Sheet CRM.
    Requires the exact Razorpay Link ID.
    """
    from app.routers.razorpay import sync_payment_link
    try:
        response = sync_payment_link(link_id)
        return f"Payment link {link_id} synced. Current status: {response.status}, Amount Paid: {response.amount_paid}"
    except Exception as e:
        return f"Failed to sync link {link_id}: {str(e)}"


@tool
def send_reminder_email_tool(email: str, reminder_level: int = 1) -> str:
    """
    Send a reminder email for any pending payment links associated with this email address.
    Level 1 is polite, Level 2 is firm, Level 3 is final notice.
    """
    from app.routers.email import send_reminder
    from app.models.email import SendReminderRequest
    try:
        response = send_reminder(SendReminderRequest(customer_email=email, reminder_level=reminder_level))
        return f"Successfully sent {response['reminders_sent']} level-{reminder_level} reminder(s) to {email}."
    except Exception as e:
        return f"Failed to send reminder to {email}: {str(e)}"


tools = [
    lookup_contact_tool, 
    update_contact_email_tool, 
    create_payment_link_tool,
    get_all_contacts_tool,
    add_contact_tool,
    get_all_payments_tool,
    find_payments_by_email_tool,
    cancel_payment_link_tool,
    sync_payment_link_tool,
    send_reminder_email_tool
]
tool_node = ToolNode(tools)

# ------------------------------------------------------------------ #
#  LLM Node
# ------------------------------------------------------------------ #

from dotenv import load_dotenv
load_dotenv()

import time as _time
import logging as _logging
_agent_logger = _logging.getLogger(__name__)

# Initialize the LLM (requires GEMINI_API_KEY in environment)
# Using gemini-2.0-flash for higher RPM limits (vs 2.5-flash preview)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    max_retries=3,            # langchain built-in retry on transient errors
    request_timeout=30,       # don't hang forever
)
# Bind the tools to the LLM so it knows what it can call
llm_with_tools = llm.bind_tools(tools)


def chatbot_node(state: AgentState):
    """The brain of the operation — with retry/backoff for rate limits."""
    # Inject current date into a dynamic system prompt
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sys_prompt = f"""You are FlowPay, an elite AI Agent for processing payments.
Your job is to generate payment invoices/links for customers.

Current System Date/Time: {current_date}

CRITICAL RULES:
1. To create a payment link, you MUST have: Name, Email, Amount, and Description.
2. BEFORE creating any payment link, you MUST ALWAYS call `lookup_contact_tool` to check if the customer already exists in the CRM.
   - If the contact exists with the correct email, proceed to create the link.
   - If the contact exists but with a different email than provided, call `update_contact_email_tool` to update it.
   - If the contact does NOT exist at all, call `update_contact_email_tool` to add them to the CRM first.
3. If the CRM returns multiple people with similar names, PAUSE and ask the user to disambiguate.
4. If the email is completely missing (user didn't provide it AND CRM lookup returned nothing), PAUSE and ask the user for it.
5. ONCE THE USER PROVIDES A MISSING EMAIL, you MUST immediately call `update_contact_email_tool` to save it to the CRM so we remember it for the future. You can call the payment generation tool right after in the same run.
6. If the user provides an ambiguous date (e.g. "tomorrow", "next Friday"), calculate it using the Current System Date above, and pass it strictly in YYYY-MM-DD format to due_date.
7. If the user asks for "partial payments" or "installments" but doesn't specify an amount, PAUSE and ask what the minimum partial amount should be.
8. You have a full suite of tools available to read from the CRM, synchronize payment statuses, cancel links, and manually trigger reminder emails. Use them proactively if the user asks.

Communicate concisely and professionally."""

    # Prepend the system prompt if it's the very first message sequence
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    
    # Retry with exponential backoff on rate limit (429) errors
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str
            if is_rate_limit and attempt < max_retries:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                _agent_logger.warning("Rate limit hit (attempt %d/%d). Retrying in %ds...", attempt + 1, max_retries, wait)
                _time.sleep(wait)
            else:
                raise


# ------------------------------------------------------------------ #
#  Graph Construction
# ------------------------------------------------------------------ #

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Determine if we should route to tools or end the conversation."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM makes a tool call, route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise, it means the LLM responded with text to the user
    return "__end__"


workflow = StateGraph(AgentState)

# Define nodes
workflow.add_node("chatbot", chatbot_node)
workflow.add_node("tools", tool_node)

# We start at the chatbot
workflow.add_edge(START, "chatbot")

# The chatbot dynamically decides whether to call a tool or reply to user
workflow.add_conditional_edges(
    "chatbot",
    should_continue,
)

# After a tool runs, it ALWAYS goes back to the chatbot to evaluate the result
workflow.add_edge("tools", "chatbot")

# NOTE: We do not compile the graph here because we need to inject the 
# checkpointer per-request, or universally in the FastAPI lifespan.
# We will expose a `get_compiled_graph(checkpointer)` function instead.

def get_compiled_graph(checkpointer):
    """Returns the executable graph using the provided SqliteSaver Checkpointer."""
    return workflow.compile(checkpointer=checkpointer)
