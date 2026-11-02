from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    analyze_alert,
    analyze_service,
    analyze_dependency,
    analyze_infrastructure,
    analyze_os,
    correlate,
    generate_diagnosis)
from app.schemas.diagnosis import DiagnosisState


def build_diagnosis_graph():
    graph = StateGraph(DiagnosisState)

    # Build block node
    graph.add_node("analyze_alert",analyze_alert)
    graph.add_node("analyze_service",analyze_service)
    graph.add_node("analyze_dependency", analyze_dependency)
    graph.add_node("analyze_infrastructure", analyze_infrastructure)
    graph.add_node("correlate", correlate)
    graph.add_node("analyze_os",analyze_os)
    graph.add_node("generate_diagnosis", generate_diagnosis)
    # Build neuron thinking
    graph.add_edge(START,"analyze_alert")
    graph.add_edge("analyze_alert","analyze_service")
    graph.add_edge("analyze_service","analyze_dependency")
    graph.add_edge("analyze_dependency","analyze_infrastructure")
    graph.add_edge("analyze_infrastructure","analyze_os")
    graph.add_edge("analyze_os", "correlate")
    graph.add_edge("correlate", "generate_diagnosis")
    graph.add_edge("generate_diagnosis", END)

    return graph.compile()


diagnosis_graph = build_diagnosis_graph()