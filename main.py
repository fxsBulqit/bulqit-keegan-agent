#!/usr/bin/env python3
"""
Bulqit Keegan Agent - Main Entry Point
This agent makes friendly follow-up calls to homeowners who received Bulqit materials.
"""

import os
from dotenv import load_dotenv
from line import VoiceAgentApp, VoiceAgentSystem
from config import load_system_prompt, load_knowledge_base
from llm_node import GeminiReasoningNode

# Load environment variables
load_dotenv()

# System prompt for Keegan's personality + Knowledge Base
SYSTEM_PROMPT = load_system_prompt()
KNOWLEDGE_BASE = load_knowledge_base()

# Combine system prompt with knowledge base
FULL_PROMPT = f"{SYSTEM_PROMPT}\n\n===KNOWLEDGE BASE===\n{KNOWLEDGE_BASE}"

# Initial greeting message
INITIAL_MESSAGE = (
    "Hey, this is Keegan — I live nearby and help out with Bulqit. "
    "We dropped off a little coloring book and crayons the other day — "
    "did you get a chance to take a look?"
)

# Get Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set in .env file")
    print("Get one free at: https://ai.google.dev")

async def call_handler(system: VoiceAgentSystem):
    """
    Handle incoming/outbound calls using Line SDK.
    This function is called for each new call.
    """
    # Create LLM reasoning node
    llm_node = GeminiReasoningNode(
        system_prompt=FULL_PROMPT,
        api_key=GEMINI_API_KEY or "dummy-key"  # Will fail gracefully if no key
    )

    # Add the node as the speaking node
    system.with_speaking_node(llm_node, bridge=None)

    # Send initial greeting
    await system.send_initial_message(INITIAL_MESSAGE)

    # Start the system and wait for completion
    await system.start()
    await system.wait_for_shutdown()

# Create the Voice Agent App
app = VoiceAgentApp(call_handler=call_handler)

# Access the FastAPI app for uvicorn
fastapi_app = app.fastapi_app

if __name__ == "__main__":
    import uvicorn
    print("Bulqit Keegan Agent initialized successfully")
    print(f"System Prompt Length: {len(SYSTEM_PROMPT)} characters")
    print(f"Knowledge Base Length: {len(KNOWLEDGE_BASE)} characters")
    print(f"Initial Message: {INITIAL_MESSAGE}")
    print(f"Gemini API Key Set: {bool(GEMINI_API_KEY)}")
    print("\n✓ Starting agent server...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
