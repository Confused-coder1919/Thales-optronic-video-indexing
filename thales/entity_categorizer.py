"""
Entity categorization using ML-based zero-shot classification.
"""

import torch
from transformers import pipeline
from typing import Dict, List

from thales.config import ENTITY_CATEGORIES, ENTITY_TO_VISUAL_CATEGORY


def initialize_categorizer():
    """
    Initialize a zero-shot classification pipeline for entity categorization.
    
    Returns:
        Initialized zero-shot classification pipeline
    """
    print("Initializing entity categorizer model...")
    
    # Determine device
    if torch.cuda.is_available():
        device = 0
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = -1
    
    categorizer = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=device
    )
    print(f"Entity categorizer model loaded successfully on {device}")
    
    return categorizer


def categorize_entity_with_context(
    entity: str, 
    context: List[str], 
    categorizer
) -> str:
    """
    Categorize an entity into a visual category using ML with context.
    
    Args:
        entity: Entity name to categorize
        context: List of context strings where the entity appears
        categorizer: Initialized zero-shot classification pipeline
        
    Returns:
        Category string for visual detection
    """
    # First, check if entity is already a known high-level category
    entity_lower = entity.lower().strip()
    if entity_lower in ENTITY_TO_VISUAL_CATEGORY:
        return ENTITY_TO_VISUAL_CATEGORY[entity_lower]
    
    # Check if it's already a visual category
    if entity_lower in [c.lower() for c in ENTITY_CATEGORIES]:
        return entity_lower
    
    # Combine context for ML classification
    if context and len(context) > 0:
        context_snippets = sorted(context, key=len, reverse=True)[:3]
        full_context = " ".join(context_snippets)
        classification_text = (
            f"In the following context: '{full_context[:400]}', "
            f"the term '{entity}' refers to what type of entity?"
        )
    else:
        classification_text = f"The term '{entity}' refers to what type of entity?"
    
    try:
        result = categorizer(classification_text, ENTITY_CATEGORIES, multi_label=False)
        
        if result and 'labels' in result and len(result['labels']) > 0:
            top_label = result['labels'][0]
            top_score = result['scores'][0] if 'scores' in result else 0.0
            
            if top_score > 0.2:
                return top_label
            elif context:
                return categorize_entity_with_context(entity, [], categorizer)
            return top_label
        else:
            return "military personnel"
            
    except Exception as e:
        print(f"Error categorizing entity '{entity}' with ML: {e}")
        return "military personnel"


def categorize_entities(
    entities: List[str], 
    entity_contexts: Dict[str, List[str]], 
    categorizer=None
) -> Dict[str, str]:
    """
    Categorize a list of entities using ML with context.
    
    Args:
        entities: List of entity names
        entity_contexts: Dictionary mapping entity names to context strings
        categorizer: Optional pre-initialized categorizer
        
    Returns:
        Dictionary mapping entity names to their categories
    """
    if categorizer is None:
        categorizer = initialize_categorizer()
    
    entity_to_category = {}
    
    print(f"Categorizing {len(entities)} entities using ML with context...")
    for i, entity in enumerate(entities):
        if (i + 1) % 10 == 0:
            print(f"  Categorized {i+1}/{len(entities)} entities...")
        
        context = entity_contexts.get(entity, [])
        category = categorize_entity_with_context(entity, context, categorizer)
        entity_to_category[entity] = category
        
        if entity != category:
            print(f"    '{entity}' -> '{category}'")
    
    print("Entity categorization complete")
    return entity_to_category

