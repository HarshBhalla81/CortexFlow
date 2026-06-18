import json

def process_refund(ticket_id: str, amount: float):
    print(f"[TOOL MICROSERVICE] Processing refund of ${amount} for ticket {ticket_id}")
    return {"status": "success", "message": f"Refund of ${amount} processed."}

def escalate_to_human(ticket_id: str, reason: str):
    print(f"[TOOL MICROSERVICE] Escalating ticket {ticket_id} to human. Reason: {reason}")
    return {"status": "success", "message": f"Ticket escalated to Tier 2 support."}
