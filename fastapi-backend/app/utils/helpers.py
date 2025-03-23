import os
import time
import tempfile
from typing import Optional, List, Dict, Any, Tuple


def ensure_dir_exists(dir_path: str) -> bool:
    """Ensure that a directory exists, creating it if necessary"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            return True
        except Exception:
            return False
    return True


def create_timestamp() -> str:
    """Create a timestamp string for filenames"""
    return time.strftime("%Y%m%d_%H%M%S")


def create_temp_file(suffix: str = None) -> Tuple[str, str]:
    """Create a temporary file and return its path and name"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    filename = os.path.basename(path)
    return path, filename


def clean_dict_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a dictionary to ensure it's JSON serializable"""
    if not data:
        return {}
    
    # Convert to dict if it's not already
    if not isinstance(data, dict):
        data = dict(data)
    
    # Remove any non-serializable objects
    clean_data = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean_data[key] = value
        elif isinstance(value, (list, tuple)):
            # Recursively clean lists
            clean_data[key] = [clean_dict_for_json(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            # Recursively clean nested dicts
            clean_data[key] = clean_dict_for_json(value)
        # Skip other types
    
    return clean_data


def format_insights(text: str) -> List[str]:
    """Format insights text into a list of distinct insights"""
    if not text:
        return []
    
    # Split by common delimiters
    insights = []
    
    # Try to split by numbered points
    import re
    numbered_items = re.split(r'\d+\.\s+', text)
    
    if len(numbered_items) > 1:
        # Remove empty first element if the text started with a number
        if not numbered_items[0].strip():
            numbered_items = numbered_items[1:]
        insights = [item.strip() for item in numbered_items if item.strip()]
    else:
        # Try to split by bullet points
        bullet_items = re.split(r'[•\-\*]\s+', text)
        if len(bullet_items) > 1:
            # Remove empty first element if the text started with a bullet
            if not bullet_items[0].strip():
                bullet_items = bullet_items[1:]
            insights = [item.strip() for item in bullet_items if item.strip()]
        else:
            # Just split by newlines
            insights = [line.strip() for line in text.split('\n') if line.strip()]
    
    return insights