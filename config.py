import os
from pathlib import Path

# Load system prompt from prompt.txt (one level up)
PROMPT_FILE = Path(__file__).parent.parent / "prompt.txt"
KNOWLEDGE_BASE_FILE = Path(__file__).parent / "knowledge_base.txt"

def load_system_prompt():
    """Load the conversational direction for Keegan"""
    if PROMPT_FILE.exists():
        with open(PROMPT_FILE, 'r') as f:
            return f.read()
    return "You are Keegan, a friendly neighbor helping introduce Bulqit services."

def load_knowledge_base():
    """Load the knowledge base content"""
    if KNOWLEDGE_BASE_FILE.exists():
        with open(KNOWLEDGE_BASE_FILE, 'r') as f:
            return f.read()
    return ""

# Agent Configuration
AGENT_CONFIG = {
    "name": "Keegan - Bulqit Neighborhood Helper",
    "voice_id": os.getenv("VOICE_ID", "69267136-1bdc-412f-ad78-0caad210fb40"),
    "system_prompt": load_system_prompt(),
    "knowledge_base": load_knowledge_base(),
    "temperature": 0.7,  # Natural conversational variance
    "max_tokens": 150,   # Keep responses concise
}
