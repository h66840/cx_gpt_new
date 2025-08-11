import os
from typing import Dict, Any, List
from server.services.visual_reasoning.ai_client import ai_client
import base64
import re

# System prompt for hierarchical scene understanding
SYSTEM_PROMPT = """你是一位图像分析专家，请将图片内容转换为层次化的知识图谱，遵循“场景→分区→大物→小物”的层次化思维。

**输出要求：**
返回JSON格式：`{"nodes": [...], "edges": [], "hidden_attributes": [...]}`

**nodes格式：**
- `id`：实体的中文名称（纯粹的实体名称，不包含任何属性）
- `type`：实体类型（英文）
- `level`：层级（1-4）

**edges格式：**
- `source`：起始节点id
- `target`：目标节点id
- `relationship`：关系描述

**hidden_attributes格式：**
- `entity_id`：实体id
- `attribute_type`：属性类型（如：color, material, size, age, gender等）
- `attribute_value`：属性值

**层次化结构 - 场景分区+大物->小物原则：**
1. **全局层(level=1)**：场景（如：室内家庭储物场景）
2. **分区层(level=2)**：主体区、背景区（Zone）
   - 主体区：画面主要焦点区域
   - 背景区：画面背景区域
3. **大物体层(level=3)**：主体区/背景区中的大型支撑物体（如桌子、书架、柜子等）
4. **小物体/部件层(level=4)**：放置于大物体上的中小型物体或部件（如电热水壶、耳机、手柄等）

**层次链：**
场景(level=1) → 主体区/背景区(level=2) → 大物体(level=3) → 小物体/部件(level=4)

**大物->小物层次化思维：**
- 先划分主体区/背景区，再在主体区/背景区内找出大型支撑物体，最后将小物体/部件归属于大物体之下。
- 小物体通常位于大物体之上、之内或旁边。
- 关系链应尽量体现这种容器-内容的层次。

**重要规则 - 属性分离：**
1. **节点ID必须是纯粹的实体名称**：
   - 正确：`泰迪熊`, `T恤`, `汽车`, `小孩`
   - 错误：`棕色泰迪熊`, `红色T恤`, `蓝色汽车`, `可爱的小孩`
2. **所有属性存储在hidden_attributes中：**
   - 颜色：`{"entity_id": "泰迪熊", "attribute_type": "color", "attribute_value": "棕色"}`
   - 材质：`{"entity_id": "桌子", "attribute_type": "material", "attribute_value": "木质"}`
   - 大小：`{"entity_id": "包", "attribute_type": "size", "attribute_value": "小"}`
   - 年龄：`{"entity_id": "小孩", "attribute_type": "age", "attribute_value": "幼儿"}`
   - 性别：`{"entity_id": "小孩", "attribute_type": "gender", "attribute_value": "男性"}`
3. **建立层级关系**：下级节点通过"contains"或"has_part"关系连接到上级节点
4. **关系类型定义：**
   - **层级关系**："contains"（包含）、"has_part"（部件）
   - **功能关系**："interacts_with"（交互）、"wears"（穿戴）、"uses"（使用）
   - **位置关系**："在...旁边"（相邻）、"在...上方"（上下）、"在...下方"（下上）、"在...左侧"（左右）、"在...右侧"（右左）、"在...前面"（前后）、"在...后面"（后前）
   - **空间关系**："near"（附近）、"beside"（旁边）、"above"（上方）、"below"（下方）、"left_of"（左侧）、"right_of"（右侧）、"in_front_of"（前面）、"behind"（后面）

**实体类型：**
- `Scene`：场景（level=1）
- `Zone`：区域（level=2）
- `Object`：物体（level=3/4）
- `Part`：部件（level=4）
- `Person`：人物（level=4）
- `Animal`：动物（level=4）
"""

async def miscellaneous_analysis(image_bytes: bytes, prompt: str = None) -> Dict[str, Any]:
    """
    Analyzes image content to extract a hierarchical knowledge graph.
    """
    final_prompt = prompt if prompt else SYSTEM_PROMPT
    try:
        raw_graph_data = await ai_client.analyze_image(image_bytes, final_prompt)
        return validate_and_fix_graph_data(raw_graph_data)
    except Exception as e:
        return {"error": str(e)}

def optimize_graph_layout(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    if not graph_data or "nodes" not in graph_data or "edges" not in graph_data:
        return graph_data
    
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]
    hidden_attributes = graph_data.get("hidden_attributes", [])
    
    forbidden_names = ["背景人物", "模糊物体", "某个人", "某个物体", "背景物体", "未知对象"]
    forbidden_exact_names = ["场景"]
    
    nodes_to_remove = set()
    for node in nodes:
        node_id = node.get("id", "")
        if any(forbidden in node_id for forbidden in forbidden_names) or node_id in forbidden_exact_names:
            nodes_to_remove.add(node_id)
    
    nodes = [node for node in nodes if node.get("id") not in nodes_to_remove]
    edges = [edge for edge in edges if edge.get("source") not in nodes_to_remove and edge.get("target") not in nodes_to_remove]
    hidden_attributes = [attr for attr in hidden_attributes if attr.get("entity_id") not in nodes_to_remove]
    
    return {
        "nodes": nodes,
        "edges": edges,
        "hidden_attributes": hidden_attributes
    }

def validate_and_fix_graph_data(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    if not graph_data or "nodes" not in graph_data or "edges" not in graph_data:
        return graph_data
    
    graph_data = optimize_graph_layout(graph_data)
    
    nodes = graph_data["nodes"]
    hidden_attributes = graph_data.get("hidden_attributes", [])
    
    if not nodes:
        return graph_data
    
    node_ids = {node["id"] for node in nodes}
    valid_hidden_attributes = [attr for attr in hidden_attributes if attr.get("entity_id") in node_ids]
    
    graph_data["hidden_attributes"] = valid_hidden_attributes
    return graph_data

def query_hidden_attributes(graph_data: Dict[str, Any], entity_id: str = None, attribute_type: str = None) -> List[Dict[str, Any]]:
    if not graph_data or "hidden_attributes" not in graph_data:
        return []
    
    hidden_attributes = graph_data["hidden_attributes"]
    results = [
        attr for attr in hidden_attributes
        if (not entity_id or attr.get("entity_id") == entity_id)
        and (not attribute_type or attr.get("attribute_type") == attribute_type)
    ]
    return results

def get_entity_attributes(graph_data: Dict[str, Any], entity_id: str) -> Dict[str, List[str]]:
    attributes = query_hidden_attributes(graph_data, entity_id=entity_id)
    grouped_attributes = {}
    for attr in attributes:
        attr_type = attr.get("attribute_type", "unknown")
        attr_value = attr.get("attribute_value", "")
        grouped_attributes.setdefault(attr_type, []).append(attr_value)
    return grouped_attributes

def search_entities_by_attribute(graph_data: Dict[str, Any], attribute_type: str, attribute_value: str) -> List[str]:
    hidden_attributes = graph_data.get("hidden_attributes", [])
    return [
        attr.get("entity_id")
        for attr in hidden_attributes
        if attr.get("attribute_type") == attribute_type and attr.get("attribute_value") == attribute_value
    ]
