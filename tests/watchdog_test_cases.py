from services.orchestrator.watchdog.graph_analyzer import GraphAnalyzer

from test_events import (NORMAL_WORKFLOW, REASONING_LOOP)

def test_normal_workflow():

    graph = GraphAnalyzer()

    for event in NORMAL_WORKFLOW:

        graph.ingest(event)

    assert (
        graph.detect_cycle("task_1")
        is False
    )

    print(
        "PASS: normal workflow"
    )

def test_reasoning_loop():

    graph = GraphAnalyzer()

    for event in REASONING_LOOP:

        graph.ingest(event)

    assert (
        graph.detect_cycle("task_2")
        is True
    )

    print(
        "PASS: reasoning loop"
    )