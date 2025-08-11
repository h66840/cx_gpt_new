import re
from difflib import SequenceMatcher
from typing import Dict, Any, List

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculates the similarity between two texts using SequenceMatcher."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def normalize_relationship_text(relationship: str) -> str:
    """Normalizes relationship text for comparison."""
    normalized = re.sub(r'[^\w\s]', '', relationship.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def calculate_relationship_similarity(rel1: Dict[str, Any], rel2: Dict[str, Any]) -> float:
    """Calculates the semantic similarity between two relationship triplets."""
    subj1, pred1, obj1 = rel1.get("subject", ""), rel1.get("predicate", ""), rel1.get("object", "")
    subj2, pred2, obj2 = rel2.get("subject", ""), rel2.get("predicate", ""), rel2.get("object", "")
    
    subj_sim = calculate_text_similarity(subj1, subj2)
    pred_sim = calculate_text_similarity(normalize_relationship_text(pred1), normalize_relationship_text(pred2))
    obj_sim = calculate_text_similarity(obj1, obj2)
    
    weighted_similarity = (subj_sim * 0.3 + pred_sim * 0.5 + obj_sim * 0.3)
    
    return weighted_similarity

def find_similar_relationships(new_relationship: Dict[str, Any], existing_relationships: List[Dict[str, Any]], 
                             similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Finds relationships similar to a new one in a list of existing relationships."""
    similar_relationships = []
    
    for existing_rel in existing_relationships:
        similarity = calculate_relationship_similarity(new_relationship, existing_rel)
        if similarity >= similarity_threshold:
            similar_relationships.append({
                "relationship": existing_rel,
                "similarity": similarity
            })
    
    return similar_relationships

def should_add_relationship(new_relationship: Dict[str, Any], existing_relationships: List[Dict[str, Any]], 
                          similarity_threshold: float = 0.8) -> Dict[str, Any]:
    """Determines whether a new relationship should be added, considering semantic duplicates."""
    similar_rels = find_similar_relationships(new_relationship, existing_relationships, similarity_threshold)
    
    if similar_rels:
        most_similar = max(similar_rels, key=lambda x: x["similarity"])
        return {
            "should_add": False,
            "reason": "semantic_duplicate",
            "similar_relationship": most_similar["relationship"],
            "similarity_score": most_similar["similarity"],
            "action": "skip"
        }
    else:
        return {
            "should_add": True,
            "reason": "unique_relationship",
            "action": "add"
        }
