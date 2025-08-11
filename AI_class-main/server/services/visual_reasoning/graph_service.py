import time
import networkx as nx
from typing import Dict, Any, List

from server.services.visual_reasoning.state import (
    get_graph,
    set_graph,
    get_hidden_attributes,
    set_hidden_attributes,
)

def get_type_colors() -> Dict[str, str]:
    """Returns a mapping of node types to colors for visualization."""
    return {
        "Person": "#fcc02a", "Animal": "#4caf50", "Clothing": "#187bac",
        "Food": "#f16b91", "Toy": "#34a853", "Accessory": "#e91e63",
        "Object": "#9c27b0", "Color": "#ff9800", "Location": "#795548",
        "Action": "#f44336", "Information": "#607d8b", "Other": "#aaaaaa",
    }

def build_graph_data(session_id: str) -> Dict[str, Any]:
    """Builds the output graph structure for frontend visualization from Redis."""
    graph = get_graph(session_id)
    type_colors = get_type_colors()
    current_time = time.time()
    recent_threshold = 30
    
    nodes = []
    for n, d in graph.nodes(data=True):
        node_data = {"id": n, "name": n}
        added_time = d.get("added_time")
        is_recent = added_time and (current_time - added_time) < recent_threshold
        node_data["color"] = "#10b981" if is_recent or d.get("is_new") else type_colors.get(d.get("type", "Other"), "#aaaaaa")
        node_data["isNew"] = is_recent or d.get("is_new", False)
        nodes.append(node_data)
        
    edges = []
    for u, v, d in graph.edges(data=True):
        edge_data = {"source": u, "target": v, "relationship": d.get("relation", "UNKNOWN")}
        added_time = d.get("added_time")
        is_recent = added_time and (current_time - added_time) < recent_threshold
        edge_data["isNew"] = is_recent or d.get("is_new", False)
        edges.append(edge_data)
        
    hidden_attributes = get_hidden_attributes(session_id)
    
    return {"nodes": nodes, "edges": edges, "hidden_attributes": hidden_attributes, "session_id": session_id}

def add_new_entity(session_id: str, source: str, relationship: str, target: str) -> Dict[str, Any]:
    """Adds a new entity (node and edge) to the graph for a session."""
    graph = get_graph(session_id)
    current_time = time.time()
    
    for name, is_new in [(source, source not in graph), (target, target not in graph)]:
        graph.add_node(name, type="Unknown", added_time=current_time if is_new else None, is_new=is_new)
        
    graph.add_edge(source, target, relation=relationship, added_time=current_time, is_new=True)
    set_graph(session_id, graph)
    return build_graph_data(session_id)

def update_existing_node(session_id: str, old_node_id: str, new_node_id: str, node_type: str, node_level: int) -> Dict[str, Any]:
    """Updates an existing node's properties or ID."""
    graph = get_graph(session_id)
    
    if old_node_id not in graph:
        raise ValueError("Node does not exist.")
    
    if new_node_id != old_node_id:
        if new_node_id in graph:
            raise ValueError("New node ID already exists.")
        
        nx.relabel_nodes(graph, {old_node_id: new_node_id}, copy=False)
        
        hidden_attributes = get_hidden_attributes(session_id)
        for attr in hidden_attributes:
            if attr.get("entity_id") == old_node_id:
                attr["entity_id"] = new_node_id
        set_hidden_attributes(session_id, hidden_attributes)

    set_graph(session_id, graph)
    return build_graph_data(session_id)

def add_new_node(session_id: str, node_id: str, node_type: str, node_level: int) -> Dict[str, Any]:
    """Adds a single new node to the graph."""
    graph = get_graph(session_id)
    if node_id in graph:
        raise ValueError("Node already exists.")
    graph.add_node(node_id, type=node_type, level=node_level)
    set_graph(session_id, graph)
    return build_graph_data(session_id)

def add_new_relation(session_id: str, source: str, target: str, relationship: str) -> Dict[str, Any]:
    """Adds a new relationship (edge) between existing nodes."""
    graph = get_graph(session_id)
    if source not in graph or target not in graph:
        raise ValueError("Source or target node does not exist.")
    if graph.has_edge(source, target):
        raise ValueError("Relation already exists.")
    graph.add_edge(source, target, relation=relationship)
    set_graph(session_id, graph)
    return build_graph_data(session_id)

def update_existing_relation(session_id: str, index: int, source: str, target: str, relationship: str) -> Dict[str, Any]:
    """Updates an existing relationship."""
    graph = get_graph(session_id)
    edges = list(graph.edges(data=True))
    if index >= len(edges):
        raise IndexError("Relation index out of range.")
    
    old_source, old_target, _ = edges[index]
    graph.remove_edge(old_source, old_target)
    graph.add_edge(source, target, relation=relationship)
    set_graph(session_id, graph)
    return build_graph_data(session_id)

def add_new_attribute(session_id: str, entity_id: str, attr_type: str, attr_value: str) -> Dict[str, Any]:
    """Adds a hidden attribute to a node."""
    graph = get_graph(session_id)
    if entity_id not in graph:
        raise ValueError("Entity does not exist in the graph.")
    
    attributes = get_hidden_attributes(session_id)
    attributes.append({
        "entity_id": entity_id,
        "attribute_type": attr_type,
        "attribute_value": attr_value
    })
    set_hidden_attributes(session_id, attributes)
    return build_graph_data(session_id)

def update_existing_attribute(session_id: str, index: int, entity_id: str, attr_type: str, attr_value: str) -> Dict[str, Any]:
    """Updates an existing hidden attribute."""
    attributes = get_hidden_attributes(session_id)
    if index >= len(attributes):
        raise IndexError("Attribute index out of range.")
    
    attributes[index] = {
        "entity_id": entity_id,
        "attribute_type": attr_type,
        "attribute_value": attr_value
    }
    set_hidden_attributes(session_id, attributes)
    return build_graph_data(session_id)

def delete_existing_node(session_id: str, node_id: str) -> Dict[str, Any]:
    """Deletes a node from the graph."""
    graph = get_graph(session_id)
    if node_id not in graph:
        raise ValueError("Node does not exist.")
    graph.remove_node(node_id)
    set_graph(session_id, graph)
    # Also remove any hidden attributes associated with the deleted node
    attributes = get_hidden_attributes(session_id)
    updated_attributes = [attr for attr in attributes if attr.get("entity_id") != node_id]
    set_hidden_attributes(session_id, updated_attributes)
    return build_graph_data(session_id)

def delete_existing_relation(session_id: str, index: int) -> Dict[str, Any]:
    """Deletes a relation from the graph by its index."""
    graph = get_graph(session_id)
    edges = list(graph.edges(data=True))
    if index >= len(edges):
        raise IndexError("Relation index out of range.")
    
    source, target, _ = edges[index]
    graph.remove_edge(source, target)
    set_graph(session_id, graph)
    return build_graph_data(session_id)

def delete_existing_attribute(session_id: str, index: int) -> Dict[str, Any]:
    """Deletes a hidden attribute by its index."""
    attributes = get_hidden_attributes(session_id)
    if index >= len(attributes):
        raise IndexError("Attribute index out of range.")
    
    del attributes[index]
    set_hidden_attributes(session_id, attributes)
    return build_graph_data(session_id)

