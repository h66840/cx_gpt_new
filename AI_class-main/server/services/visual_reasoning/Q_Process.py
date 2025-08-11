import json
import re
import requests
import os
from typing import Dict, List, Any, Optional
import networkx as nx
from collections import defaultdict

# 全局变量用于存储隐含属性
app_state = {
    'hidden_attributes': []
}

def get_hidden_attributes():
    """获取隐含属性"""
    return app_state.get('hidden_attributes', [])

def set_hidden_attributes(attributes):
    """设置隐含属性"""
    app_state['hidden_attributes'] = attributes

class QuestionProcessor:
    def __init__(self, graph=None, hidden_attributes=None):
        """
        初始化问题处理器
        
        Args:
            graph: 可选的图对象，用于查询关系信息
            hidden_attributes: 隐含属性列表
        """
        self.graph = graph
        self.hidden_attributes = hidden_attributes or get_hidden_attributes()
        print(f"📋 传入的隐含属性数量: {len(self.hidden_attributes)}")
        if self.hidden_attributes:
            print("📋 隐含属性详情:")
            for attr in self.hidden_attributes:
                print(f"  - {attr['entity_id']}: {attr['attribute_type']} = {attr['attribute_value']}")

    def extract_entities_and_subquestions(self, question: str, scene_graph_nodes: List[str] = None) -> Dict[str, Any]:
        """
        提取实体并生成子问题的主要方法
        
        Args:
            question: 用户问题
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            包含实体和子问题的结果字典
        """
        print(f"=== 开始处理问题 ===")
        print(f"接收到的问题: {question}")
        print(f"当前场景图节点: {scene_graph_nodes}")
        print(f"场景图节点数量: {len(scene_graph_nodes) if scene_graph_nodes else 0}")
        print("正在调用process_question函数...")
        
        try:
            result = self._process_question_with_scene_graph(question, scene_graph_nodes or [])
            return result
        except Exception as e:
            print(f"=== 处理问题时发生错误 ===")
            print(f"错误类型: {type(e)}")
            print(f"错误信息: {e}")
            import traceback
            print(f"错误堆叠: {traceback.format_exc()}")
            
            # 回退到基本处理
            return self._fallback_processing(question, scene_graph_nodes or [])

    def _process_question_with_scene_graph(self, question: str, scene_graph_nodes: List[str]) -> Dict[str, Any]:
        """
        使用场景图处理问题的核心逻辑
        
        Args:
            question: 用户问题
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            处理结果
        """
        print(f"=== 智能推理流程开始 ===")
        
        try:
            # 1. 智能决策 - 判断是否需要查询实体
            smart_decision = self._smart_decision_workflow(question, scene_graph_nodes)
            
            # 检查查询策略
            query_strategy = smart_decision.get('query_strategy', {})
            needs_query = query_strategy.get('needs_query', False)
            
            print(f"=== 查询策略分析 ===")
            print(f"需要查询: {needs_query}")
            print(f"查询策略: {query_strategy}")
            
            if needs_query:
                # 需要查询实体
                entities_to_query = query_strategy.get('entities_to_query', [])
                print(f"=== 开始查询实体信息 ===")
                print(f"要查询的实体: {entities_to_query}")
                
                # 从智能决策结果中获取匹配的实体名称
                found_entities = smart_decision.get('found_entities', [])
                entity_mapping = {}
                for entity_info in found_entities:
                    question_entity = entity_info.get('question_entity', '')
                    scene_graph_entity = entity_info.get('scene_graph_entity', '')
                    if question_entity and scene_graph_entity:
                        entity_mapping[question_entity] = scene_graph_entity
                
                # 查询实体信息
                query_results = {}
                for entity in entities_to_query:
                    # 使用匹配后的实体名称进行查询
                    matched_entity = entity_mapping.get(entity, entity)
                    print(f"查询实体: {entity} -> 匹配到: {matched_entity}")
                    try:
                        result = self._query_entity_information(matched_entity)
                        # result是一个字符串，直接存储
                        query_results[entity] = result
                    except Exception as e:
                        print(f"❌ 查询实体 {matched_entity} 失败: {e}")
                        query_results[entity] = f"查询失败: {str(e)}"
                
                print(f"查询结果: {query_results}")
                
                # 基于查询结果生成最终答案
                final_result = self._final_answer_with_query_results(question, query_results, smart_decision)
                return final_result
            else:
                # 不需要查询，直接返回结果
                print(f"=== 无需查询，直接返回结果 ===")
                return self._enhance_result_with_evidence(smart_decision, scene_graph_nodes)
                
        except Exception as e:
            print(f"智能决策失败: {e}")
            return self._fallback_processing(question, scene_graph_nodes)

    def _smart_decision_workflow(self, question: str, scene_graph_nodes: List[str]) -> Dict[str, Any]:
        """
        智能决策工作流程
        
        Args:
            question: 用户问题
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            决策结果
        """
        print(f"=== 智能决策工作流程 ===")
        
        # 调用LLM进行智能决策
        system_prompt = """
你是一个专业的视觉问答系统决策专家。基于用户问题和场景图信息，进行智能实体匹配和决策。

你的任务：
1. 分析问题中提到的实体，智能匹配到场景图中的节点
2. 考虑同义词、近义词、上下位词等关系进行匹配
3. 判断是否需要查询特定实体的详细信息来回答问题
4. 判断是否能直接基于现有信息回答问题

实体匹配规则：
- 考虑同义词：如"小男孩"对应"小孩"，"头发"对应"头部"
- 考虑上下位词：如"衣服"可能对应具体的"上衣"、"裤子"等
- 考虑描述性词汇：如"红色的"可能对应带颜色属性的实体
- 考虑语境相关性：根据问题上下文判断最相关的实体
- 优先选择最精确的匹配，避免模糊匹配

重要提示：
- 必须从提供的场景图节点列表中选择匹配的实体
- 如果找不到精确匹配，考虑同义词和语义相似性
- 对于颜色相关问题，优先匹配有颜色属性的实体
- 对于位置相关问题，优先匹配位置相关的实体

返回JSON格式：
{
    "found_entities": [
        {
            "question_entity": "问题中的实体",
            "scene_graph_entity": "场景图中对应的实体",
            "entity_type": "实体类型",
            "confidence": 0.9,
            "reasoning": "详细的匹配原因和推理过程"
        }
    ],
    "not_found_entities": [
        {
            "entity": "未找到的实体",
            "reason": "为什么没找到"
        }
    ],
    "query_strategy": {
        "needs_query": true/false,
        "entities_to_query": ["需要查询的实体列表"],
        "reasoning": "为什么需要查询"
    },
    "has_direct_answer": true/false,
    "direct_answer": "如果能直接回答，写答案；否则为null",
    "answer_reasoning": "答案推理过程",
    "subquestions": []
}
"""

        user_prompt = f"""
问题：{question}

场景图节点：{scene_graph_nodes}

隐含属性：
{chr(10).join([f"- {attr['entity_id']}: {attr['attribute_type']} = {attr['attribute_value']}" for attr in self.hidden_attributes])}

请仔细分析：
1. 问题中提到的实体，智能匹配到场景图中的节点
2. 考虑同义词、近义词、上下位词关系
3. 根据问题类型（如颜色、位置、关系等）判断需要查询哪些实体
4. 基于隐含属性判断是否能直接回答问题

重要提示：
- 必须从提供的场景图节点列表中选择匹配的实体
- 对于颜色相关问题，优先匹配有颜色属性的实体
- 对于身体部位问题，考虑与人物实体的关联
- 确保匹配的实体名称与场景图节点完全一致

请进行智能实体匹配和决策。
"""

        try:
            response = self._call_llm_api(system_prompt + "\n\n" + user_prompt, "smart_decision")
            print(f"=== 智能决策LLM响应 ===")
            print(f"原始响应: {response}")
            
            # 解析JSON响应
            cleaned_response = re.sub(r'```json\s*', '', response)
            cleaned_response = re.sub(r'```\s*$', '', cleaned_response)
            
            result = json.loads(cleaned_response)
            print(f"清理后响应: {result}")
            print(f"解析结果: {result}")
            
            # 添加原始问题到结果中
            result["original_question"] = question
            result["scene_graph_nodes"] = scene_graph_nodes
            
            print(f"=== 智能决策结果 ===")
            print(f"需要查询: {result.get('query_strategy', {}).get('needs_query', False)}")
            print(f"要查询的实体: {result.get('query_strategy', {}).get('entities_to_query', [])}")
            
            return result
            
        except Exception as e:
            print(f"智能决策失败: {e}")
            raise

    def _query_entity_information(self, entity_name: str) -> str:
        """
        查询实体信息 - 使用智能匹配的实体名称
        
        Args:
            entity_name: 实体名称（已经通过智能决策匹配过）
            
        Returns:
            实体信息字符串
        """
        print(f"🎯 查询 {entity_name} 结果: ", end="")
        
        # 构建基本信息
        info_parts = []
        
        # 添加隐含属性
        for attr in self.hidden_attributes:
            try:
                if isinstance(attr, dict) and attr.get('entity_id') == entity_name:
                    info_parts.append(f"- [属性] {entity_name} {attr.get('attribute_type', '')}: {attr.get('attribute_value', '')}")
                    print(f"✅ 添加隐含属性: - [属性] {entity_name} {attr.get('attribute_type', '')}: {attr.get('attribute_value', '')}")
            except Exception as e:
                print(f"⚠️ 处理隐含属性时出错: {e}, 属性: {attr}")
                continue
        
        # 如果有图对象，查询关系
        if self.graph and entity_name in self.graph.nodes():
            try:
                # 查找与该实体相关的关系
                for source, target, data in self.graph.edges(data=True):
                    # 检查source或target是否匹配当前实体
                    if source == entity_name:
                        # 当前实体是关系的源
                        relation = data.get('relation', 'related_to')
                        info_parts.append(f"- {entity_name} {relation} {target}")
                        print(f"✅ 添加关系: - {entity_name} {relation} {target}")
                    elif target == entity_name:
                        # 当前实体是关系的目标
                        relation = data.get('relation', 'related_to')
                        info_parts.append(f"- {source} {relation} {entity_name}")
                        print(f"✅ 添加关系: - {source} {relation} {entity_name}")
            except Exception as e:
                print(f"⚠️ 查询关系时出错: {e}")
        
        if info_parts:
            result = f"Here is what I know about '{entity_name}':\n" + "\n".join(info_parts)
        else:
            result = f"No specific information found for '{entity_name}'"
        
        print(result)
        return result
    
    def _fallback_query_entity_information(self, entity_name: str) -> str:
        """
        回退的实体查询方法
        
        Args:
            entity_name: 实体名称
            
        Returns:
            实体信息字符串
        """
        info_parts = []
        
        # 添加隐含属性
        for attr in self.hidden_attributes:
            if isinstance(attr, dict) and attr.get('entity_id') == entity_name:
                info_parts.append(f"- [属性] {entity_name} {attr.get('attribute_type', '')}: {attr.get('attribute_value', '')}")
        
        # 如果有图对象，查询关系
        if self.graph and entity_name in self.graph.nodes():
            try:
                # 查找与该实体相关的关系
                for source, target, data in self.graph.edges(data=True):
                    # 检查source或target是否匹配当前实体
                    if source == entity_name:
                        # 当前实体是关系的源
                        relation = data.get('relation', 'related_to')
                        info_parts.append(f"- {entity_name} {relation} {target}")
                    elif target == entity_name:
                        # 当前实体是关系的目标
                        relation = data.get('relation', 'related_to')
                        info_parts.append(f"- {source} {relation} {entity_name}")
            except Exception as e:
                print(f"⚠️ 回退查询关系时出错: {e}")
        
        if info_parts:
            result = f"Here is what I know about '{entity_name}':\n" + "\n".join(info_parts)
        else:
            result = f"No specific information found for '{entity_name}'"
        
        return result

    def _final_answer_with_query_results(self, question: str, query_results: Dict[str, str], original_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于查询结果生成最终答案
        
        Args:
            question: 原始问题
            query_results: 查询结果字典
            original_result: 原始LLM决策结果
            
        Returns:
            包含最终答案的结果字典
        """
        print(f"=== 基於查詢結果生成最終答案 ===")
        print(f"问题: {question}")
        print(f"查询结果: {query_results}")
        
        # 构建查询结果摘要
        query_summary = []
        for entity, result in query_results.items():
            query_summary.append(f"{entity}: {result}")
        
        # 调用LLM进行最终判断
        system_prompt = """
你是一个专业的视觉问答系统答案生成专家。基于查询到的实体信息，判断是否能回答用户问题。

请分析查询结果，判断：
1. 是否能直接回答问题
2. 如果能回答，给出具体答案
3. 如果不能回答，说明原因

**重要：位置关系识别**
- 当问题涉及"旁边"、"附近"、"周围"等空间关系时，重点关注位置关系
- 位置关系包括："在...旁边"、"在...左侧"、"在...右侧"、"在...上方"、"在...下方"等
- 例如：如果查询结果显示"耳机 在...左侧 电热水壶"，那么"电热水壶旁边有什么"的答案应该包含"耳机"

**位置关系示例：**
- "电热水壶旁边有什么" → 查找所有与电热水壶有位置关系的实体
- "桌子上面有什么" → 查找所有"在...上方 桌子"的关系
- "笔筒里面有什么" → 查找所有"包含"或"has_part"关系

**判断标准：**
1. **位置问题**：如果问题包含"旁边"、"附近"、"周围"、"上面"、"下面"等空间词汇，且查询结果中有相应的位置关系，则可以直接回答
2. **属性问题**：如果问题涉及颜色、材质等属性，且查询结果中有相应的隐含属性，则可以直接回答
3. **关系问题**：如果问题涉及实体间关系，且查询结果中有相应的关系信息，则可以直接回答

返回JSON格式：
{
    "has_direct_answer": true/false,
    "direct_answer": "如果能回答，写具体答案；否则为null",
    "answer_reasoning": "详细说明答案是如何得出的，包括实体匹配和推理过程",
    "confidence": 0.9,
    "matched_entities": [
        {
            "original_entity": "原始实体名称",
            "matched_entity": "匹配到的场景图实体",
            "relevant_info": "相关信息"
        }
    ]
}
"""

        user_prompt = f"""
问题：{question}

查询到的实体信息：
{chr(10).join(query_summary)}

智能决策中的实体匹配：
{chr(10).join([f"- {entity_info.get('question_entity', '')} -> {entity_info.get('scene_graph_entity', '')}" for entity_info in original_result.get('found_entities', [])])}

隐含属性信息：
{chr(10).join([f"- {attr.get('entity_id', '')}: {attr.get('attribute_type', '')} = {attr.get('attribute_value', '')}" for attr in self.hidden_attributes])}

**重要提示：**
- 请仔细分析查询结果中的位置关系
- 如果问题涉及空间关系（如"旁边"、"附近"等），重点关注位置关系信息
- 实体已经通过智能匹配进行了映射，可以直接使用匹配后的实体名称
- 隐含属性包含了重要的视觉信息（如颜色、材质等）

请基于以上信息判断是否能回答问题，特别注意位置关系的识别和利用。
"""

        try:
            response = self._call_llm_api(system_prompt + "\n\n" + user_prompt, "final_answer_generation")
            
            # 解析JSON响应
            cleaned_response = re.sub(r'```json\s*', '', response)
            cleaned_response = re.sub(r'```\s*$', '', cleaned_response)
            
            final_judgment = json.loads(cleaned_response)
            print(f"最终判断结果: {final_judgment}")
            
            # 构建最终结果
            result = {
                "original_question": question,
                "scene_graph_nodes": original_result.get("scene_graph_nodes", []),
                "found_entities": original_result.get("found_entities", []),
                "not_found_entities": original_result.get("not_found_entities", []),
                "has_direct_answer": final_judgment.get("has_direct_answer", False),
                "direct_answer": final_judgment.get("direct_answer"),
                "answer_reasoning": final_judgment.get("answer_reasoning", ""),
                "subquestions": self._generate_subquestions_for_fallback(question, original_result.get("found_entities", [])),
                "reasoning_evidence": self._generate_reasoning_evidence(
                    original_result.get("found_entities", []), 
                    original_result.get("scene_graph_nodes", [])
                ),
                "total_entities": len(original_result.get("found_entities", [])) + len(original_result.get("not_found_entities", [])),
                "found_count": len(original_result.get("found_entities", [])),
                "not_found_count": len(original_result.get("not_found_entities", []))
            }
            
            return result
            
        except Exception as e:
            print(f"最终答案生成失败: {e}")
            # 回退到原始结果
            return self._enhance_result_with_evidence(original_result, original_result.get("scene_graph_nodes", []))

    def _enhance_result_with_evidence(self, result: Dict[str, Any], scene_graph_nodes: List[str]) -> Dict[str, Any]:
        """
        增强结果，添加推理证据
        
        Args:
            result: 原始结果
            scene_graph_nodes: 场景图节点
            
        Returns:
            增强后的结果
        """
        print(f"=== 增强结果，添加推理证据 ===")
        
        # 生成推理证据
        reasoning_evidence = self._generate_reasoning_evidence(
            result.get("found_entities", []), 
            scene_graph_nodes
        )
        
        # 构建最终结果
        final_result = {
            "original_question": result.get("original_question", ""),
            "scene_graph_nodes": scene_graph_nodes,
            "found_entities": result.get("found_entities", []),
            "not_found_entities": result.get("not_found_entities", []),
            "has_direct_answer": result.get("has_direct_answer", False),
            "direct_answer": result.get("direct_answer"),
            "answer_reasoning": result.get("answer_reasoning", ""),
            "subquestions": result.get("subquestions", []),
            "reasoning_evidence": reasoning_evidence,
            "total_entities": len(result.get("found_entities", [])) + len(result.get("not_found_entities", [])),
            "found_count": len(result.get("found_entities", [])),
            "not_found_count": len(result.get("not_found_entities", []))
        }
        
        return final_result

    def _fallback_processing(self, question: str, scene_graph_nodes: List[str]) -> Dict[str, Any]:
        """
        回退处理 - 当智能决策失败时使用
        
        Args:
            question: 用户问题
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            处理结果
        """
        print(f"=== 回退到传统处理流程 ===")
        
        # 使用原有的实体提取和子问题生成逻辑
        try:
            # 提取实体
            entities_result = self._extract_entities(question)
            found_entities = entities_result.get('entities', [])
            
            # 映射到场景图
            mapped_entities = self._map_entities_to_scene_graph(found_entities, scene_graph_nodes)
            
            # 生成子问题
            subquestions_result = self._generate_subquestions(question, mapped_entities)
            subquestions = subquestions_result.get('subquestions', [])
            
            # 生成推理依据
            reasoning_evidence = self._generate_reasoning_evidence(mapped_entities, scene_graph_nodes)
            
            # 构建结果
            result = {
                'original_question': question,
                'scene_graph_nodes': scene_graph_nodes,
                'found_entities': mapped_entities,
                'not_found_entities': entities_result.get('not_found_entities', []),
                'has_direct_answer': False,
                'direct_answer': None,
                'answer_reasoning': '使用回退处理流程，需要进一步分析',
                'subquestions': subquestions,
                'reasoning_evidence': reasoning_evidence,
                'total_entities': len(found_entities),
                'found_count': len(mapped_entities),
                'not_found_count': len(entities_result.get('not_found_entities', []))
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 回退处理也失败: {e}")
            # 最后的回退
            return {
                'original_question': question,
                'scene_graph_nodes': scene_graph_nodes,
                'found_entities': [],
                'not_found_entities': [],
                'has_direct_answer': False,
                'direct_answer': None,
                'answer_reasoning': f'处理失败: {str(e)}',
                'subquestions': ['请重新描述问题'],
                'reasoning_evidence': [],
                'total_entities': 0,
                'found_count': 0,
                'not_found_count': 0
            }

    def _call_llm_api(self, prompt: str, task_type: str) -> str:
        """
        调用LLM API - 使用阿里云 dashscope API
        
        Args:
            prompt: 提示词
            task_type: 任务类型
            
        Returns:
            LLM响应
        """
        print(f"📞 调用LLM API - 任务类型: {task_type}")
        
        try:
            # 检查API Key
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                print("❌ DASHSCOPE_API_KEY 环境变量未设置")
                raise ValueError("API key not configured")
            
            # 设置API Key
            import dashscope
            dashscope.api_key = api_key
            
            # 根据任务类型设置不同的系统提示
            if task_type == "smart_decision":
                system_prompt = """你是一个专业的视觉问答系统决策专家。基于用户问题和场景图信息，进行智能实体匹配和决策。

你的任务：
1. 分析问题中提到的实体，智能匹配到场景图中的节点
2. 考虑同义词、近义词、上下位词等关系进行匹配
3. 判断是否需要查询特定实体的详细信息来回答问题
4. 判断是否能直接基于现有信息回答问题

实体匹配规则：
- 考虑同义词：如"小男孩"对应"小孩"，"头发"对应"头部"
- 考虑上下位词：如"衣服"可能对应具体的"上衣"、"裤子"等
- 考虑描述性词汇：如"红色的"可能对应带颜色属性的实体
- 考虑语境相关性：根据问题上下文判断最相关的实体

返回JSON格式：
{
    "found_entities": [
        {
            "question_entity": "问题中的实体",
            "scene_graph_entity": "场景图中对应的实体",
            "entity_type": "实体类型",
            "confidence": 0.9,
            "reasoning": "详细的匹配原因和推理过程"
        }
    ],
    "not_found_entities": [
        {
            "entity": "未找到的实体",
            "reason": "为什么没找到"
        }
    ],
    "query_strategy": {
        "needs_query": true/false,
        "entities_to_query": ["需要查询的实体列表"],
        "reasoning": "为什么需要查询"
    },
    "has_direct_answer": true/false,
    "direct_answer": "如果能直接回答，写答案；否则为null",
    "answer_reasoning": "答案推理过程",
    "subquestions": []
}"""
            elif task_type == "final_answer_generation":
                system_prompt = """你是一个专业的视觉问答系统答案生成专家。基于查询到的实体信息，判断是否能回答用户问题。

请分析查询结果，判断：
1. 是否能直接回答问题
2. 如果能回答，给出具具体答案
3. 如果不能回答，说明原因

注意：
- 实体可能已经通过智能匹配进行了映射
- 隐含属性包含了重要的视觉信息（如颜色、位置等）
- 需要结合问题类型和实体信息进行推理

返回JSON格式：
{
    "has_direct_answer": true/false,
    "direct_answer": "如果能回答，写具体答案；否则为null",
    "answer_reasoning": "详细说明答案是如何得出的，包括实体匹配和推理过程",
    "confidence": 0.9,
    "matched_entities": [
        {
            "original_entity": "原始实体名称",
            "matched_entity": "匹配到的场景图实体",
            "relevant_info": "相关信息"
        }
    ]
}"""
            elif task_type == "subquestion_generation":
                system_prompt = """你是一个专业的视觉问答问题分解专家。

请分析用户问题，理解问题的本质，并生成合适的子问题分解。

**问题类型识别：**
- 数量问题：询问"几个"、"多少"、"几支"等数量信息
- 颜色问题：询问"什么颜色"、"颜色"等外观信息
- 位置问题：询问"在哪里"、"旁边"、"位置"等空间关系
- 属性问题：询问"什么材质"、"大小"等属性信息
- 关系问题：询问"和谁"、"和什么"等关系信息

**子问题生成要求：**
1. 每个子问题都应该有明确的观察目标
2. 子问题之间要有逻辑递进关系
3. 最终能够回答原始问题

请分析问题并返回JSON格式：
{
    "question_analysis": {
        "question_type": "问题类型（数量/颜色/位置/属性/关系）",
        "target_entities": ["需要观察的主要实体"],
        "observation_focus": "观察重点描述",
        "reasoning": "问题分析推理"
    },
    "subquestions": [
        "子问题1：具体的观察任务",
        "子问题2：基于子问题1的进一步观察",
        "子问题3：最终的信息整合"
    ]
}

**示例：**
问题："笔筒内放了几支笔？"
分析：这是一个数量问题，需要观察笔筒内部并计数笔的数量
子问题：
1. 在图像中定位笔筒的位置
2. 观察笔筒内部的内容和结构
3. 计数笔筒内笔的具体数量
4. 确认数量并回答问题"""
            else:
                raise ValueError(f"不支持的任务类型: {task_type}")
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"text": system_prompt + "\n\n" + prompt}
                    ]
                }
            ]
            
            # 调用API
            response = dashscope.MultiModalConversation.call(
                model="qwen-vl-max",
                messages=messages,
                temperature=0.0,
            )
            
            if response.status_code != 200:
                print(f"❌ API调用失败: {response.status_code} - {response.message}")
                raise ValueError(f"API调用失败: {response.message}")
            
            # 解析响应
            content_data = response.output.choices[0].message.content
            if isinstance(content_data, list) and content_data and "text" in content_data[0]:
                response_text = content_data[0]["text"]
            elif isinstance(content_data, str):
                response_text = content_data
            else:
                raise ValueError(f"意外的响应格式: {content_data}")
            
            print(f"✅ API调用成功")
            print(f"📄 LLM原始响应: {response_text[:200]}...")  # 添加调试信息
            return response_text
            
        except Exception as e:
            print(f"❌ LLM API调用失败: {e}")
            raise

    def _generate_subquestions_for_fallback(self, question: str, found_entities: List[Dict]) -> List[str]:
        """
        为回退情况生成子问题 - 使用智能分析
        
        Args:
            question: 原始问题
            found_entities: 找到的实体列表
            
        Returns:
            子问题列表
        """
        try:
            # 使用LLM智能分析问题类型和生成子问题
            return self._generate_intelligent_subquestions(question, found_entities)
        except Exception as e:
            print(f"智能子问题生成失败，使用备用方案: {e}")
            return self._generate_basic_subquestions(question, found_entities)
    
    def _generate_intelligent_subquestions(self, question: str, found_entities: List[Dict]) -> List[str]:
        """
        使用LLM智能生成子问题
        
        Args:
            question: 原始问题
            found_entities: 找到的实体列表
            
        Returns:
            子问题列表
        """
        # 提取实体信息
        entity_names = [entity.get('scene_graph_entity', '') for entity in found_entities]
        entities_text = "、".join(entity_names) if entity_names else "相关实体"
        
        # 构建完整的提示词
        prompt = f"""
**当前问题涉及的实体：{entities_text}**

请分析问题：{question}

请返回JSON格式的子问题分解。"""
        
        try:
            # 调用LLM进行智能分析
            response = self._call_llm_api(prompt, "subquestion_generation")
            
            print(f"🔍 子问题生成LLM响应长度: {len(response)}")
            print(f"🔍 子问题生成LLM响应: {response}")  # 显示完整响应
            
            # 尝试清理响应中的markdown代码块标记
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            print(f"🔍 清理后的响应: {cleaned_response}")
            
            # 解析响应
            import json
            result = json.loads(cleaned_response)
            
            subquestions = result.get("subquestions", [])
            if subquestions:
                print(f"✅ 智能生成子问题成功")
                print(f"问题类型: {result.get('question_analysis', {}).get('question_type', '未知')}")
                print(f"生成的子问题: {subquestions}")
                return subquestions
            else:
                raise Exception("LLM返回的子问题为空")
                
        except Exception as e:
            print(f"❌ 智能子问题生成失败: {e}")
            print(f"🔍 尝试解析的响应内容: {response}")
            raise e
    
    def _generate_basic_subquestions(self, question: str, found_entities: List[Dict]) -> List[str]:
        """
        基础子问题生成（备用方案）
        
        Args:
            question: 原始问题
            found_entities: 找到的实体列表
            
        Returns:
            子问题列表
        """
        # 提取问题中的主要实体
        entity_names = [entity.get('scene_graph_entity', '') for entity in found_entities]
        main_entity = entity_names[0] if entity_names else "目标实体"
        
        # 基础问题分解
        subquestions = [
            f"1. 识别问题中提到的关键实体（{main_entity}）",
            f"2. 在图像中定位{main_entity}",
            f"3. 观察{main_entity}的具体特征和内容",
            f"4. 基于观察结果回答问题"
        ]
        
        return subquestions

    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """
        从问题中提取实体
        
        Args:
            question: 用户问题
            
        Returns:
            实体提取结果
        """
        # 简单的实体提取逻辑
        entities = []
        not_found_entities = []
        
        # 常见实体关键词
        entity_keywords = ['小孩', '男孩', '女孩', '人', '衣服', 'T恤', '泰迪熊', '熊', '眼镜', '帽子']
        
        for keyword in entity_keywords:
            if keyword in question:
                entities.append({
                    'name': keyword,
                    'type': 'entity',
                    'confidence': 0.8
                })
        
        return {
            'entities': entities,
            'not_found_entities': not_found_entities
        }

    def _map_entities_to_scene_graph(self, entities: List[Dict], scene_graph_nodes: List[str]) -> List[Dict]:
        """
        将提取的实体映射到场景图节点
        
        Args:
            entities: 提取的实体列表
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            映射后的实体列表
        """
        mapped_entities = []
        
        for entity in entities:
            entity_name = entity.get('name', '')
            best_match = self._find_best_mapping(entity_name, scene_graph_nodes)
            
            mapped_entities.append({
                'original_entity': entity_name,
                'scene_graph_entity': best_match,
                'confidence': entity.get('confidence', 0.5),
                'entity_type': 'Unknown'
            })
        
        return mapped_entities

    def _find_best_mapping(self, entity_name: str, scene_graph_nodes: List[str]) -> str:
        """
        找到最佳映射
        
        Args:
            entity_name: 实体名称
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            最佳匹配的节点名称
        """
        if entity_name in scene_graph_nodes:
            return entity_name
        
        # 模糊匹配
        for node in scene_graph_nodes:
            if entity_name in node or node in entity_name:
                return node
        
        return entity_name

    def _generate_subquestions(self, question: str, entities: List[Dict]) -> Dict[str, Any]:
        """
        生成子问题 - 使用智能分析
        
        Args:
            question: 原始问题
            entities: 实体列表
            
        Returns:
            子问题生成结果
        """
        try:
            # 使用智能分析生成子问题
            subquestions = self._generate_intelligent_subquestions(question, entities)
            return {
                'subquestions': subquestions
            }
        except Exception as e:
            print(f"智能子问题生成失败，使用基础方案: {e}")
            # 基础子问题生成
            subquestions = [
                "1. 识别问题中提到的实体",
                "2. 观察该实体的具体特征和内容",
                "3. 基于观察结果回答问题"
            ]
            return {
                'subquestions': subquestions
            }

    def _generate_reasoning_evidence(self, found_entities, scene_graph_nodes):
        """
        生成推理依据 - 调用图中节点信息
        
        Args:
            found_entities: 找到的实体列表
            scene_graph_nodes: 场景图节点列表
            
        Returns:
            推理依据列表
        """
        reasoning_evidence = []
        
        for entity in found_entities:
            try:
                # 处理不同格式的实体信息
                if isinstance(entity, dict):
                    scene_graph_entity = entity.get('scene_graph_entity', '')
                    question_entity = entity.get('question_entity', '')
                else:
                    # 如果是字符串，直接使用
                    scene_graph_entity = str(entity)
                    question_entity = str(entity)
                
                print(f"🔍 生成推理证据: {question_entity} -> {scene_graph_entity}")
                
                # 检查实体是否在场景图中
                has_relationships = scene_graph_entity in scene_graph_nodes
                
                # 调用图中节点信息
                node_details = self._get_node_details_from_graph(scene_graph_entity)
                
                # 构建推理依据
                evidence = {
                    'original_entity': question_entity,
                    'mapped_node': scene_graph_entity,
                    'has_relationships': has_relationships,
                    'detailed_relationships': node_details.get('relationships', []),
                    'relationship_summary': f"将'{question_entity}'映射到'{scene_graph_entity}'",
                    'node_type': node_details.get('node_type', 'Unknown'),
                    'description': node_details.get('description', ''),
                    'found': node_details.get('found', False),
                    'confidence': entity.get('confidence', 0.8) if isinstance(entity, dict) else 0.8,
                    'entity_type': entity.get('entity_type', 'Unknown') if isinstance(entity, dict) else 'Unknown',
                    'reasoning': entity.get('reasoning', '') if isinstance(entity, dict) else '',
                    'query_success': node_details.get('found', False),  # 添加查询成功标志
                    'node_details': node_details  # 添加完整的节点详细信息
                }
                
                print(f"✅ 推理证据生成成功: {evidence['relationship_summary']}")
                print(f"   关系数量: {len(evidence['detailed_relationships'])}")
                
                reasoning_evidence.append(evidence)
                
            except Exception as e:
                print(f"⚠️ 生成推理证据时出错: {e}, 实体: {entity}")
                continue
        
        return reasoning_evidence

    def _get_node_details_from_graph(self, entity_name: str) -> Dict[str, Any]:
        """
        从图中获取节点详细信息 - 直接调用app.py中query_graph的逻辑
        
        Args:
            entity_name: 实体名称
            
        Returns:
            节点详细信息
        """
        try:
            # 检查图是否存在
            if not self.graph:
                return {
                    'node_type': 'Unknown',
                    'description': f"节点 '{entity_name}' 在场景图中不存在",
                    'relationships': [],
                    'found': False
                }
            
            # 在图中查找节点（不区分大小写）
            all_nodes_lower = {n.lower(): n for n in self.graph.nodes()}
            original_case_entity = all_nodes_lower.get(entity_name.lower())
            
            if not original_case_entity:
                return {
                    'node_type': 'Unknown',
                    'description': f"节点 '{entity_name}' 在场景图中不存在",
                    'relationships': [],
                    'found': False
                }
            
            # 获取节点属性
            node_data = self.graph.nodes(data=True)[original_case_entity]
            node_type = node_data.get("type", "Unknown")
            description = node_data.get("description", f"场景图中的{node_type}节点")
            
            # 获取所有相关关系
            relationships = []
            for edge in self.graph.edges(data=True):
                source, target, data = edge
                if original_case_entity.lower() == source.lower():
                    relation = data.get('relation', 'unknown')
                    relationships.append(f"{source} {relation} {target}")
                elif original_case_entity.lower() == target.lower():
                    relation = data.get('relation', 'unknown')
                    relationships.append(f"{source} {relation} {target}")
            
            # 查询隐含属性
            for attr in self.hidden_attributes:
                if isinstance(attr, dict) and attr.get("entity_id", "").lower() == original_case_entity.lower():
                    attribute_info = f"[属性] {attr.get('entity_id', '')} {attr.get('attribute_type', '')}: {attr.get('attribute_value', '')}"
                    relationships.append(attribute_info)
            
            return {
                'node_type': node_type,
                'description': description,
                'relationships': relationships,
                'found': True,
                'entity_name': original_case_entity
            }
            
        except Exception as e:
            print(f"获取节点详细信息失败: {e}")
            return {
                'node_type': 'Unknown',
                'description': f"获取节点信息时发生错误",
                'relationships': [],
                'found': False
            }

    def _find_best_entity_match(self, entity_name: str) -> str:
        """
        智能实体匹配 - 处理同义词和相似词
        
        Args:
            entity_name: 实体名称
            
        Returns:
            最佳匹配的节点名称
        """
        if not self.graph:
            return None
        
        # 获取所有节点
        all_nodes = list(self.graph.nodes())
        
        # 1. 精确匹配（不区分大小写）
        for node in all_nodes:
            if entity_name.lower() == node.lower():
                return node
        
        # 2. 同义词匹配
        synonyms = {
            '小男孩': '小孩',
            '男孩': '小孩',
            '女孩': '小孩',
            '头发': '头部',
            '頭髮': '头部',
            '頭部': '头部',
            '衣服': 'T恤',
            '上衣': 'T恤',
            '裤子': '裤子',
            '鞋子': '鞋子',
            '眼镜': '眼镜',
            '帽子': '帽子',
            '泰迪熊': '泰迪熊',
            '熊': '泰迪熊',
            '玩具': '泰迪熊',
            '桌子': '桌子',
            '椅子': '椅子',
            '床': '床',
            '门': '门',
            '窗户': '窗户',
            '墙': '墙',
            '地板': '地板',
            '天花板': '天花板'
        }
        
        # 检查同义词
        if entity_name in synonyms:
            synonym_target = synonyms[entity_name]
            for node in all_nodes:
                if synonym_target.lower() == node.lower():
                    return node
        
        # 3. 包含匹配
        for node in all_nodes:
            if entity_name in node or node in entity_name:
                return node
        
        # 4. 模糊匹配（基于字符相似度）
        best_match = None
        best_score = 0
        
        for node in all_nodes:
            # 简单的相似度计算
            common_chars = len(set(entity_name) & set(node))
            total_chars = len(set(entity_name) | set(node))
            if total_chars > 0:
                similarity = common_chars / total_chars
                if similarity > best_score and similarity > 0.3:  # 30%相似度阈值
                    best_score = similarity
                    best_match = node
        
        return best_match

# 为向后兼容保留的函数
def process_question(question: str, scene_graph_nodes: List[str] = None, graph=None) -> Dict[str, Any]:
    """
    处理问题的主要函数
    
    Args:
        question: 用户问题
        scene_graph_nodes: 场景图节点列表
        graph: 可选的图对象，用于查询关系信息
        
    Returns:
        处理结果字典
    """
    processor = QuestionProcessor(graph=graph)
    return processor.extract_entities_and_subquestions(question, scene_graph_nodes)
