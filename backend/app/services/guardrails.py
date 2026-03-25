"""
Guardrails Module
==================
Validates natural language prompts and structured query specs.
Ensures all queries are domain-scoped and actions are whitelisted.
"""
from typing import Optional

ALLOWED_ACTIONS = {
    "trace_billing_flow",
    "lookup_journal_entry_for_billing",
    "top_products_by_billing_count",
    "top_customers_by_billing_value",
    "delivered_not_billed",
    "billed_without_delivery",
    "open_receivables_without_payment",
    "cancelled_billing_documents",
    "entity_neighbors",
    "lookup_document",
    "reject",
}

DOMAIN_KEYWORDS = [
    "billing", "bill", "invoice",
    "sales order", "order",
    "delivery", "shipment", "ship",
    "journal entry", "journal", "accounting",
    "payment", "receivable", "ar",
    "customer", "client",
    "product", "material",
    "plant", "warehouse",
    "cancelled", "cancel",
    "open", "outstanding",
    "flow", "trace", "track",
    "o2c", "order-to-cash", "order to cash",
]

OFF_TOPIC_SIGNALS = [
    "poem", "joke", "weather", "stock", "news",
    "write code", "write a function", "python",
    "javascript", "html", "explain", "what is",
    "history of", "who invented", "wikipedia",
    "recipe", "movie", "song",
]


def is_in_domain(prompt: str) -> bool:
    """Check if a prompt appears to be within O2C domain."""
    lower = prompt.lower()

    # Explicit off-topic signals
    for signal in OFF_TOPIC_SIGNALS:
        if signal in lower:
            return False

    # Must contain at least one domain keyword
    for kw in DOMAIN_KEYWORDS:
        if kw in lower:
            return True

    return False


def validate_query_spec(spec: dict) -> tuple[bool, Optional[str]]:
    """
    Validate an LLM-generated query spec.
    Returns (is_valid, error_message).
    """
    if not isinstance(spec, dict):
        return False, "Query spec must be a JSON object."

    action = spec.get("action")
    if not action:
        return False, "Missing 'action' in query spec."

    if action not in ALLOWED_ACTIONS:
        return False, f"Unknown action '{action}'. Allowed: {sorted(ALLOWED_ACTIONS)}"

    if action == "reject":
        return True, None  # Valid reject

    # Per-action required field validation
    required_fields = {
        "trace_billing_flow": ["billing_document"],
        "lookup_journal_entry_for_billing": ["billing_document"],
        "entity_neighbors": ["node_id"],
        "lookup_document": ["entity_type", "entity_id"],
    }

    if action in required_fields:
        for field in required_fields[action]:
            if not spec.get(field):
                return False, f"Action '{action}' requires field '{field}'."

    return True, None
