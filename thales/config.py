"""
Configuration and constants for the Thales entity detection pipeline.

This module centralizes all configuration, constants, and entity mappings
used throughout the pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = "mistral-large-latest"
PIXTRAL_MODEL = "pixtral-large-latest"
DISCOVERY_MODE = os.getenv("THALES_DISCOVERY_MODE", "").strip().lower() in {"1", "true", "yes", "on"}

# =============================================================================
# Entity Categories for Visual Detection
# =============================================================================

ENTITY_CATEGORIES = [
    "military personnel",
    "civilian",
    "military truck",
    "armored vehicle",
    "artillery vehicle",
    "military vehicle",
    "trailer",
    "aircraft",
    "helicopter",
    "drone",
    "weapon",
    "turret",
    "equipment",
]

# =============================================================================
# Entity Normalization Mappings
# =============================================================================

# Map specific terms to high-level categories
ENTITY_NORMALIZATION = {
    # Military Personnel
    "driver": "military personnel",
    "signaler": "military personnel",
    "crew": "military personnel",
    "crew member": "military personnel",
    "technician": "military personnel",
    "operator": "military personnel",
    "worker": "military personnel",
    "loader": "military personnel",
    "gunner": "military personnel",
    "commander": "military personnel",
    "officer": "military personnel",
    "soldier": "military personnel",
    "troop": "military personnel",
    "troops": "military personnel",
    "personnel": "military personnel",
    "man": "military personnel",
    "woman": "military personnel",
    "person": "military personnel",
    
    # Civilians
    "civilian": "civilian",
    "bystander": "civilian",
    "passerby": "civilian",
    "spectator": "civilian",
    
    # Vehicles
    "semi truck": "military truck",
    "transport truck": "military truck",
    "logistics truck": "military truck",
    "daf truck": "military truck",
    "daf semi truck": "military truck",
    "military transport truck": "military truck",
    "logistics vehicle": "military truck",
    "tank": "armored vehicle",
    "apc": "armored vehicle",
    "ifv": "armored vehicle",
    "self-propelled artillery": "artillery vehicle",
    "artillery": "artillery vehicle",
    "howitzer": "artillery vehicle",
    "flatbed": "trailer",
    "flatbed trailer": "trailer",
    "low loader": "trailer",
    "transport trailer": "trailer",
    
    # Aircraft
    "uav": "drone",
    "unmanned aerial vehicle": "drone",
    "fixed-wing": "aircraft",
    "jet": "aircraft",
    "fighter": "aircraft",
    "bomber": "aircraft",
    
    # Weapons
    "gun": "weapon",
    "cannon": "weapon",
    "missile": "weapon",
    "rocket": "weapon",
    "main gun": "turret",
    "gun barrel": "turret",
}

# Map high-level entities to visual detection categories
ENTITY_TO_VISUAL_CATEGORY = {
    "operator": "military personnel",
    "personnel": "military personnel",
    "soldier": "military personnel",
    "military personnel": "military personnel",
    "civilian": "civilian",
    "bystander": "civilian",
    "military truck": "truck",
    "armored vehicle": "tank",
    "artillery vehicle": "artillery vehicle",
    "military vehicle": "military vehicle",
    "trailer": "trailer",
    "helicopter": "helicopter",
    "aircraft": "aircraft",
    "drone": "drone",
    "weapon": "weapon",
    "turret": "turret",
    "equipment": "equipment",
}

# Terms to exclude from entity extraction
EXCLUDED_TERMS = {
    "sweater", "jeans", "shirt", "pants", "jacket", "clothing", "clothes",
    "tracks", "wheels", "road wheels", "hull", "armor", "rear tracks",
    "travel lock", "suspension", "engine",
}

# Valid high-level categories (for normalization validation)
VALID_CATEGORIES = {
    "military personnel", "civilian", "military truck", "armored vehicle",
    "artillery vehicle", "military vehicle", "trailer", "helicopter", 
    "aircraft", "drone", "weapon", "turret", "vehicle", "equipment"
}

# =============================================================================
# Processing Defaults
# =============================================================================

DEFAULT_FRAME_INTERVAL = 5  # seconds between video frames
DEFAULT_OUTPUT_DIR = "reports"
MAX_IMAGE_SIZE = 1024  # pixels for Pixtral

# =============================================================================
# Paths
# =============================================================================

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_project_root() / "data"


def get_reports_dir() -> Path:
    """Get the reports directory path."""
    return get_project_root() / "reports"
