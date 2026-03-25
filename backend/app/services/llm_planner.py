"""
LLM Query Planner
==================
Uses Gemini (or Groq as fallback) to convert natural language into
a structured, constrained JSON query spec.
The LLM is used ONLY for intent classification, not for answering.
"""
import os
import json
import re
import httpx
from typing import Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "groq"

SYSTEM_PROMPT = """You are a query planner for an Order-to-Cash (O2C) business data system.
Your ONLY job is to convert a natural language question into a JSON query spec.
You must respond with ONLY valid JSON and nothing else.

Allowed actions and their required fields:
- trace_billing_flow: {"action": "trace_billing_flow", "billing_document": "<id>"}
- lookup_journal_entry_for_billing: {"action": "lookup_journal_entry_for_billing", "billing_document": "<id>"}
- top_products_by_billing_count: {"action": "top_products_by_billing_count", "limit": 10}
- top_customers_by_billing_value: {"action": "top_customers_by_billing_value", "limit": 10}
- delivered_not_billed: {"action": "delivered_not_billed"}
- billed_without_delivery: {"action": "billed_without_delivery"}
- open_receivables_without_payment: {"action": "open_receivables_without_payment"}
- cancelled_billing_documents: {"action": "cancelled_billing_documents"}
- entity_neighbors: {"action": "entity_neighbors", "node_id": "<node_id>"}
- lookup_document: {"action": "lookup_document", "entity_type": "<Customer|SalesOrder|BillingDocument|Delivery|JournalEntry|Payment|Product|Plant>", "entity_id": "<id>"}
- reject: {"action": "reject", "reason": "out_of_domain"}

Rules:
1. If the question is about something outside the O2C domain, return {"action": "reject", "reason": "out_of_domain"}
2. Extract document IDs exactly as mentioned in the question
3. Return ONLY JSON, no explanation, no markdown fences
4. Use "reject" for general knowledge, poems, code help, or anything not about orders/deliveries/billing/payments/customers/products/plants
"""


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from LLM response, handling markdown fences."""
    text = text.strip()
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


async def call_gemini(prompt: str) -> Optional[dict]:
    """Call Gemini API."""
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\nUser question: " + prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 256,
        }
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)


async def call_groq(prompt: str) -> Optional[dict]:
    """Call Groq API (llama3-8b-8192)."""
    if not GROQ_API_KEY:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 256,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return _extract_json(text)


def rule_based_fallback(prompt: str) -> Optional[dict]:
    """
    Simple keyword-based fallback when no LLM key is configured.
    Handles common query patterns via regex/keywords.
    """
    lower = prompt.lower()

    # Trace billing flow
    import re
    bil_match = re.search(r'\b(\d{7,12})\b', prompt)
    bid = bil_match.group(1) if bil_match else None

    if any(k in lower for k in ["trace", "flow", "full flow"]) and bid:
        return {"action": "trace_billing_flow", "billing_document": bid}

    if "journal entry" in lower and bid:
        return {"action": "lookup_journal_entry_for_billing", "billing_document": bid}

    if "cancelled" in lower or "cancell" in lower:
        return {"action": "cancelled_billing_documents"}

    if "delivered" in lower and "not billed" in lower:
        return {"action": "delivered_not_billed"}

    if "billed" in lower and ("without delivery" in lower or "no delivery" in lower):
        return {"action": "billed_without_delivery"}

    if ("receivable" in lower or "payment" in lower) and ("open" in lower or "without" in lower or "no payment" in lower):
        return {"action": "open_receivables_without_payment"}

    if "product" in lower and ("billing" in lower or "most" in lower or "top" in lower or "highest" in lower):
        limit = 10
        lm = re.search(r'\btop\s+(\d+)\b', lower)
        if lm:
            limit = int(lm.group(1))
        return {"action": "top_products_by_billing_count", "limit": limit}

    if "customer" in lower and ("billing" in lower or "volume" in lower or "most" in lower or "top" in lower):
        limit = 10
        lm = re.search(r'\btop\s+(\d+)\b', lower)
        if lm:
            limit = int(lm.group(1))
        return {"action": "top_customers_by_billing_value", "limit": limit}

    if bid:
        return {"action": "lookup_document", "entity_type": "BillingDocument", "entity_id": bid}

    return {"action": "reject", "reason": "out_of_domain"}


async def plan_query(prompt: str) -> dict:
    """Main entry point: convert prompt to query spec."""
    spec = None

    try:
        if LLM_PROVIDER == "groq" and GROQ_API_KEY:
            spec = await call_groq(prompt)
        elif GEMINI_API_KEY:
            spec = await call_gemini(prompt)
    except Exception as e:
        print(f"[LLM] Error calling {LLM_PROVIDER}: {e}")

    if spec is None:
        spec = rule_based_fallback(prompt)

    return spec or {"action": "reject", "reason": "planning_failed"}
