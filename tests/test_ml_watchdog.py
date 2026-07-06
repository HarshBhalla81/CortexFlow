import sys
import os
# Ensure we can import the services correctly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.orchestrator.watchdog.semantic_analyzer import SemanticAnalyzer
from services.orchestrator.watchdog.graph_analyzer import GraphAnalyzer

def test_exact_tool_loop():
    sa = SemanticAnalyzer()
    
    # 1st time
    res1 = sa.ingest_tool("task_1", "process_refund", {"ticket_id": "123", "amount": 50})
    assert not res1
    
    # 2nd time
    res2 = sa.ingest_tool("task_1", "process_refund", {"ticket_id": "123", "amount": 50})
    assert not res2
    
    # 3rd time (should flag)
    res3 = sa.ingest_tool("task_1", "process_refund", {"ticket_id": "123", "amount": 50})
    assert res3
    print("PASS: Exact Tool Loop detected.")

def test_semantic_loop():
    sa = SemanticAnalyzer()
    
    # Thought 1
    t1 = "I need to refund ticket 123 for $50 because the user requested it."
    res1 = sa.ingest_thought("task_2", t1)
    assert not res1
    
    # Thought 2
    t2 = "The user asked for a refund on ticket 123 in the amount of $50, I will do that."
    res2 = sa.ingest_thought("task_2", t2)
    assert not res2
    
    # Thought 3
    t3 = "Processing a $50 refund for ticket number 123 as per user request."
    res3 = sa.ingest_thought("task_2", t3)
    assert res3
    print("PASS: Semantic Loop detected.")
    
def test_markov_drift():
    ga = GraphAnalyzer()
    # Train the transition graph: Planner -> Research normally happens
    for i in range(10):
        ga.ingest({"task_id": f"t_{i}", "component": "PlannerAgent"})
        ga.ingest({"task_id": f"t_{i}", "component": "ResearchAgent"})
        ga.clear_task(f"t_{i}")
        
    # Now an anomalous transition: Planner -> Critic
    ga.ingest({"task_id": "anom", "component": "PlannerAgent"})
    ga.ingest({"task_id": "anom", "component": "CriticAgent"})
    
    abnormal = ga.detect_abnormal_transition("anom")
    assert abnormal
    print("PASS: Markov Drift detected.")

if __name__ == "__main__":
    test_exact_tool_loop()
    test_semantic_loop()
    test_markov_drift()
