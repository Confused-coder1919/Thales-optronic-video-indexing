"""
Entity extraction from voice transcripts using Mistral LLM.
"""

import re
import json
from typing import List, Set, Dict, Optional
from mistralai import Mistral

from thales.config import (
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    ENTITY_NORMALIZATION,
    EXCLUDED_TERMS,
    VALID_CATEGORIES,
)
from thales.voice_parser import get_all_segments


def get_mistral_client() -> Mistral:
    """
    Get an initialized Mistral API client.
    
    Returns:
        Initialized Mistral client
        
    Raises:
        ValueError: If MISTRAL_API_KEY is not configured
    """
    if not MISTRAL_API_KEY:
        raise ValueError(
            "MISTRAL_API_KEY not found in .env file. "
            "Please add MISTRAL_API_KEY=your_api_key to your .env file."
        )
    return Mistral(api_key=MISTRAL_API_KEY)


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


def extract_entities_from_text(text: str, client: Mistral) -> List[str]:
    """
    Extract military-relevant entities from text using Mistral LLM.
    
    Args:
        text: Input text to analyze
        client: Initialized Mistral client
        
    Returns:
        List of entity names found in the text
    """
    if not text or len(text.strip()) == 0:
        return []
    
    text_snippet = text[:2000] if len(text) > 2000 else text
    
    prompt = f"""Extract all military-relevant entities from this text and categorize them using HIGH-LEVEL, SEARCHABLE terms.

IMPORTANT RULES:
1. Use general categories, NOT specific descriptions
2. Normalize similar items to the same term
3. Focus on what would be searchable in a database
4. DISTINGUISH between military personnel and civilians

CATEGORY MAPPINGS (use these exact terms when applicable):
- Driver, operator, signaler, crew member, technician → "military personnel"
- Commander, officer, soldier, gunner, loader → "military personnel" 
- Any person working with military equipment → "military personnel"
- Civilian, bystander, passerby, spectator → "civilian"
- Any military truck (semi, transport, logistics, DAF, etc.) → "military truck"
- Any tank, armored vehicle → "armored vehicle"
- Self-propelled artillery (AS 90, M109, etc.) → "artillery vehicle"
- Trailer, flatbed, low loader → "trailer"
- Helicopter → "helicopter"
- Fixed-wing aircraft → "aircraft"
- Drone, UAV → "drone"
- Gun, cannon, missile, weapon system → "weapon"
- Turret, gun barrel → "turret"
- Tracks, wheels, hull (vehicle components) → DO NOT include separately, they are part of vehicles
- License plates → include as the plate number only (e.g., "AAB960A")
- Clothing items → DO NOT include
- Generic descriptions → DO NOT include

Text:
{text_snippet}

Return ONLY a JSON object with the entity list. Format: {{"entities": ["military personnel", "military truck", "artillery vehicle"]}}
Do NOT add descriptions in parentheses. Keep entities simple and searchable.
If no entities found, return: {{"entities": []}}
"""
    
    try:
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                if 'entities' in parsed and isinstance(parsed['entities'], list):
                    return [str(e).strip() for e in parsed['entities'] if e]
                for key in ['entity_list', 'result', 'entities_found', 'items']:
                    if key in parsed and isinstance(parsed[key], list):
                        return [str(e).strip() for e in parsed[key] if e]
                for value in parsed.values():
                    if isinstance(value, list):
                        return [str(e).strip() for e in value if e]
            elif isinstance(parsed, list):
                return [str(e).strip() for e in parsed if e]
        except json.JSONDecodeError:
            # Try to extract array from text
            array_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
            if array_match:
                array_content = array_match.group(1)
                entities = []
                for match in re.finditer(r'["\']([^"\']+)["\']|(\w+(?:\s+\w+)*)', array_content):
                    entity = match.group(1) or match.group(2)
                    if entity:
                        entities.append(entity.strip())
                if entities:
                    return entities
        
        print(f"Warning: Could not parse entity extraction response: {content[:200]}")
        return []
        
    except Exception as e:
        print(f"Error extracting entities with Mistral: {e}")
        return []


def extract_military_entities(voice_file_path: str) -> Set[str]:
    """
    Extract all military-relevant entities from a voice file.
    
    Args:
        voice_file_path: Path to the voice file
        
    Returns:
        Set of unique normalized entity names
    """
    print("Initializing Mistral client...")
    client = get_mistral_client()
    
    print(f"Parsing voice file: {voice_file_path}")
    segments = get_all_segments(voice_file_path)
    
    all_entities = set()
    
    print(f"Processing {len(segments)} segments with Mistral LLM...")
    for i, (timestamp, text) in enumerate(segments):
        if i % 10 == 0:
            print(f"  Processing segment {i+1}/{len(segments)}")
        
        entities = extract_entities_from_text(text, client)
        
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
    print("Initializing Mistral client...")
    client = get_mistral_client()
    
    print(f"Parsing voice file: {voice_file_path}")
    segments = get_all_segments(voice_file_path)
    
    entity_contexts: Dict[str, List[str]] = {}
    
    print(f"Processing {len(segments)} segments with Mistral LLM...")
    for i, (timestamp, text) in enumerate(segments):
        if i % 10 == 0:
            print(f"  Processing segment {i+1}/{len(segments)}")
        
        entities = extract_entities_from_text(text, client)
        
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

