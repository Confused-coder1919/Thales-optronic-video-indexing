"""
Entity detection in video frames using Pixtral vision model.
"""

import base64
import io
from PIL import Image
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple
from mistralai import Mistral

from thales.config import (
    ENTITY_CATEGORIES,
    ENTITY_TO_VISUAL_CATEGORY,
    DISCOVERY_MODE,
    MISTRAL_API_KEY,
    PIXTRAL_MODEL,
    MAX_IMAGE_SIZE,
)
from thales.video_processor import extract_frames_at_intervals, seconds_to_timestamp
from thales.entity_extractor import get_entity_list, extract_entities_with_context
from thales.entity_categorizer import categorize_entities, initialize_categorizer
from thales.discovery import discover_entities_in_video


def get_pixtral_client() -> Mistral:
    """
    Get an initialized Mistral client for Pixtral vision model.
    
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


def frame_to_base64(frame: np.ndarray) -> str:
    """
    Convert OpenCV frame (BGR) to base64-encoded JPEG string.
    
    Args:
        frame: OpenCV frame as numpy array (BGR)
        
    Returns:
        Base64-encoded JPEG image string
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    
    if pil_image.width > MAX_IMAGE_SIZE or pil_image.height > MAX_IMAGE_SIZE:
        pil_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    
    return base64.standard_b64encode(buffer.read()).decode("utf-8")


def detect_entities_in_frame_batch(
    client: Mistral, 
    frame: np.ndarray, 
    entities: List[str], 
    entity_to_category: Dict[str, str]
) -> Dict[str, bool]:
    """
    Detect multiple entities in a single frame using Pixtral.
    
    Args:
        client: Initialized Mistral client
        frame: Video frame as numpy array (BGR format)
        entities: List of entity names to detect
        entity_to_category: Dictionary mapping entity names to visual categories
        
    Returns:
        Dictionary mapping entity names to detection results (True/False)
    """
    try:
        image_base64 = frame_to_base64(frame)
        
        entity_queries = []
        for entity in entities:
            category = entity_to_category.get(entity, entity)
            entity_queries.append(f"- {entity} (look for: {category})")
        
        entities_list = "\n".join(entity_queries)
        
        prompt = f"""Analyze this image carefully and determine which of the following entities are ACTUALLY VISIBLE in the frame.

Entities to check:
{entities_list}

IMPORTANT RULES:
1. Only mark an entity as present if you can CLEARLY see it in the image
2. Be strict - if you're uncertain, mark it as NOT present
3. "military personnel" = people in military context (uniforms, operating equipment)
4. "civilian" = people in civilian clothing NOT operating military equipment
5. "military truck" = large military transport trucks (not regular cars)
6. "artillery vehicle" = self-propelled guns like AS 90, M109 (tracked vehicles with large gun)
7. "trailer" = flatbed or transport trailer carrying equipment
8. "turret" = rotating gun platform on a vehicle
9. "weapon" = visible guns, cannons, missiles

For each entity, respond with ONLY "YES" or "NO".

Format your response EXACTLY like this (one per line):
ENTITY_NAME: YES
ENTITY_NAME: NO

List ALL entities with their detection status:"""

        response = client.chat.complete(
            model=PIXTRAL_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_base64}"
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        results = {entity: False for entity in entities}
        
        for line in content.split('\n'):
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                entity_name = parts[0].strip()
                detection = parts[1].strip().upper()
                
                for entity in entities:
                    if entity.lower() == entity_name.lower():
                        results[entity] = detection == "YES"
                        break
        
        return results
        
    except Exception as e:
        print(f"Error detecting entities in frame with Pixtral: {e}")
        return {entity: False for entity in entities}


def detect_entities_in_video(
    video_path: str, 
    entities: List[str], 
    entity_to_category: Dict[str, str],
    interval_seconds: int = 1
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect entities in video frames at regular intervals.
    
    Args:
        video_path: Path to the video file
        entities: List of entity names to detect
        entity_to_category: Dictionary mapping entity names to categories
        interval_seconds: Interval between frames in seconds
        
    Returns:
        Dictionary mapping entity names to lists of detections
    """
    print("Initializing Pixtral vision model...")
    client = get_pixtral_client()
    
    print(f"Extracting frames from {video_path}...")
    frames = extract_frames_at_intervals(video_path, interval_seconds)
    
    if not frames:
        print("No frames extracted from video")
        return {}
    
    print(f"Detecting {len(entities)} entities in {len(frames)} frames using Pixtral...")
    
    results: Dict[str, List[Dict[str, Any]]] = {entity: [] for entity in entities}
    
    for i, (second, frame) in enumerate(frames):
        timestamp = seconds_to_timestamp(second)
        print(f"  Processing frame {i+1}/{len(frames)} at {timestamp}...")
        
        frame_detections = detect_entities_in_frame_batch(
            client, frame, entities, entity_to_category
        )
        
        for entity in entities:
            is_present = frame_detections.get(entity, False)
            results[entity].append({
                "timestamp": timestamp,
                "second": second,
                "present": is_present
            })
    
    print("Detection complete")
    return results


def process_video_with_voice(
    video_path: str,
    voice_file_path: str,
    interval_seconds: int = 1,
) -> Dict[str, List[Dict[str, Any]]] | Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    """
    Process a video using entities extracted from a voice file.

    Returns detection results and, when discovery mode is enabled, optional
    per-entity metadata (source/discovered_only).
    """
    print(f"Extracting entities from {voice_file_path}...")
    speech_entities = get_entity_list(voice_file_path)
    speech_set = set(speech_entities)

    discovery_entities = set()
    if DISCOVERY_MODE:
        try:
            discoveries = discover_entities_in_video(
                video_path, interval_seconds_discovery=interval_seconds
            )
            for entry in discoveries:
                for entity in entry.get("entities", []):
                    discovery_entities.add(entity)
            if discovery_entities:
                print(
                    f"Discovery mode proposed {len(discovery_entities)} entities "
                    f"(sampled vision frames)."
                )
        except Exception as exc:
            print(f"Warning: discovery mode failed: {exc}")

    candidate_entities = set(speech_entities)
    if discovery_entities:
        candidate_entities |= discovery_entities

    entity_metadata: Optional[Dict[str, Dict[str, Any]]] = None

    if not candidate_entities:
        print("No entities found in voice file; running baseline vision scan.")
        entities = list(ENTITY_CATEGORIES)
        entity_to_category = {
            entity: ENTITY_TO_VISUAL_CATEGORY.get(entity, entity)
            for entity in entities
        }
        results = detect_entities_in_video(
            video_path,
            entities,
            entity_to_category,
            interval_seconds,
        )
        if DISCOVERY_MODE:
            entity_metadata = {
                entity: {"source": "vision", "discovered_only": False}
                for entity in entities
            }
        return (results, entity_metadata) if entity_metadata else results

    entities = sorted(candidate_entities)
    print(
        f"Found {len(entities)} entities: "
        f"{', '.join(entities[:5])}{'...' if len(entities) > 5 else ''}"
    )

    print("\nExtracting context for entities...")
    entity_contexts = (
        extract_entities_with_context(voice_file_path) if speech_entities else {}
    )

    print("\nCategorizing entities using ML with context...")
    categorizer = initialize_categorizer()
    entity_to_category = categorize_entities(entities, entity_contexts, categorizer)

    if DISCOVERY_MODE:
        entity_metadata = {}
        for entity in entities:
            in_speech = entity in speech_set
            in_vision = entity in discovery_entities
            if in_speech and in_vision:
                source = "both"
            elif in_speech:
                source = "speech"
            else:
                source = "vision"
            entity_metadata[entity] = {
                "source": source,
                "discovered_only": bool(in_vision and not in_speech),
            }

    print(f"\nDetecting entities in {video_path}...")
    results = detect_entities_in_video(
        video_path, entities, entity_to_category, interval_seconds
    )

    return (results, entity_metadata) if entity_metadata else results
