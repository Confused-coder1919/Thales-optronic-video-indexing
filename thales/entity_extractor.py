"""
Entity extraction from voice transcripts using pluggable LLM providers.
"""

import re
from typing import List, Set, Dict, Optional, Any

from thales.config import (
    ENTITY_NORMALIZATION,
    EXCLUDED_TERMS,
    VALID_CATEGORIES,
)
from thales.llm.router import generate_index
from thales.voice_parser import get_all_segments


def normalize_entity(entity: str) -> Optional[str]:
    """
    Normalize an entity to a high-level searchable category.
    
    Args:
        entity: Raw entity string
        
    Returns:
        Normalized entity string, or None if the entity should be excluded
    """
    entity_lower = entity.lower().strip()
    
    # Remove parenthetical descriptions like "(military truck)" or "(operator)"
    entity_clean = re.sub(r'\s*\([^)]*\)\s*', '', entity_lower).strip()
    
    # Check if this is an excluded term
    for excluded in EXCLUDED_TERMS:
        if excluded in entity_clean:
            return None
    
    # Check for direct normalization match
    if entity_clean in ENTITY_NORMALIZATION:
        return ENTITY_NORMALIZATION[entity_clean]
    
    # Check for partial matches in normalization
    for key, normalized in ENTITY_NORMALIZATION.items():
        if key in entity_clean:
            return normalized
    
    # Check for license plate pattern (letters and numbers)
    if re.match(r'^[A-Z0-9]{5,10}$', entity.strip().upper()):
        return entity.strip().upper()
    
    # Keep the original if it's a valid high-level category
    if entity_clean in VALID_CATEGORIES:
        return entity_clean
    
    # For specific vehicle models like "AS 90", "M1 Abrams", keep them
    if re.match(r'^[A-Z]{1,3}[\s-]?\d+', entity.strip().upper()):
        return entity.strip()
    
    # Default: return the cleaned entity
    return entity_clean if len(entity_clean) > 1 else None


def extract_entities_from_text(text: str, client: Any = None) -> List[str]:
    """
    Extract military-relevant entities from text using configured LLM provider.
    
    Args:
        text: Input text to analyze
        client: Deprecated, kept for backward compatibility and ignored
        
    Returns:
        List of entity names found in the text
    """
    if not text or len(text.strip()) == 0:
        return []
    
    payload = generate_index(
        {
            "text": text[:2000] if len(text) > 2000 else text,
            "timestamps": {},
            "vision_detections": [],
        }
    )
    entities = payload.get("entities", [])
    return [str(entity).strip() for entity in entities if str(entity).strip()]


def extract_military_entities(voice_file_path: str) -> Set[str]:
    """
    Extract all military-relevant entities from a voice file.
    
    Args:
        voice_file_path: Path to the voice file
        
    Returns:
        Set of unique normalized entity names
    """
    print(f"Parsing voice file: {voice_file_path}")
    segments = get_all_segments(voice_file_path)
    
    all_entities = set()
    
    print(f"Processing {len(segments)} segments with configured LLM provider...")
    for i, (timestamp, text) in enumerate(segments):
        if i % 10 == 0:
            print(f"  Processing segment {i+1}/{len(segments)}")
        
        entities = extract_entities_from_text(text)
        
        for entity in entities:
            normalized = normalize_entity(entity)
            if normalized:
                all_entities.add(normalized)
    
    print(f"Found {len(all_entities)} unique entities")
    return all_entities


def get_entity_list(voice_file_path: str) -> List[str]:
    """
    Get a sorted list of unique military entities from a voice file.
    
    Args:
        voice_file_path: Path to the voice file
        
    Returns:
        Sorted list of entity names
    """
    entities = extract_military_entities(voice_file_path)
    return sorted(list(entities))


def extract_entities_with_context(voice_file_path: str) -> Dict[str, List[str]]:
    """
    Extract entities with their surrounding context from a voice file.
    
    Args:
        voice_file_path: Path to the voice file
        
    Returns:
        Dictionary mapping entity names to lists of context strings
    """
    print(f"Parsing voice file: {voice_file_path}")
    segments = get_all_segments(voice_file_path)
    
    entity_contexts: Dict[str, List[str]] = {}
    
    print(f"Processing {len(segments)} segments with configured LLM provider...")
    for i, (timestamp, text) in enumerate(segments):
        if i % 10 == 0:
            print(f"  Processing segment {i+1}/{len(segments)}")
        
        entities = extract_entities_from_text(text)
        
        for entity_text in entities:
            normalized = normalize_entity(entity_text)
            if not normalized:
                continue
            
            try:
                entity_lower = entity_text.strip().lower()
                text_lower = text.lower()
                
                start_pos = 0
                while True:
                    entity_index = text_lower.find(entity_lower, start_pos)
                    if entity_index < 0:
                        break
                    
                    start = max(0, entity_index - 300)
                    end = min(len(text), entity_index + len(entity_text) + 300)
                    context = text[start:end].strip()
                    
                    if normalized not in entity_contexts:
                        entity_contexts[normalized] = []
                    entity_contexts[normalized].append(context)
                    
                    start_pos = entity_index + len(entity_text)
                    
            except Exception as e:
                print(f"Error extracting context for entity '{entity_text}': {e}")
                continue
    
    print(f"Found {len(entity_contexts)} unique entities with context")
    return entity_contexts
