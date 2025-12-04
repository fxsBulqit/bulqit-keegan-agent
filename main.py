#!/usr/bin/env python3
"""
Bulqit Keegan Agent - Main Entry Point
This agent makes friendly follow-up calls to homeowners who received Bulqit materials.
"""

import os
from dotenv import load_dotenv
from line import VoiceAgentApp, VoiceAgentSystem, Bridge
from line.events import UserStartedSpeaking, UserStoppedSpeaking, UserTranscriptionReceived
from config import AGENT_PROMPT, LOCATION
from llm_node import GeminiReasoningNode

# Load environment variables
load_dotenv()

# Get the complete system prompt from config
SYSTEM_PROMPT = AGENT_PROMPT

# Get Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set in .env file")
    print("Get one free at: https://ai.google.dev")

async def handle_new_call(system: VoiceAgentSystem, call_request):
    """
    Handle incoming/outbound calls using Line SDK.
    This function is called for each new call with system and call_request.
    """
    # Create LLM reasoning node
    llm_node = GeminiReasoningNode(
        system_prompt=SYSTEM_PROMPT,
        api_key=GEMINI_API_KEY or "dummy-key"  # Will fail gracefully if no key
    )

    # Create bridge for the LLM node
    bridge = Bridge(llm_node)

    # Add the node as the speaking node
    system.with_speaking_node(llm_node, bridge=bridge)

    # Set up event handlers for user speech
    bridge.on(UserTranscriptionReceived).map(llm_node.add_event)

    # When user stops speaking, generate response using base class generate()
    (
        bridge.on(UserStoppedSpeaking)
        .interrupt_on(UserStartedSpeaking, handler=llm_node.on_interrupt_generate)
        .stream(llm_node.generate)  # Base class method calls our process_context()
        .broadcast()
    )

    # Start the system
    await system.start()

    # Don't send initial greeting - wait for user to speak first
    # (Initial greeting commented out - agent will wait for user)

    # Wait for completion
    await system.wait_for_shutdown()

# Create the Voice Agent App
app = VoiceAgentApp(handle_new_call)

# Access the FastAPI app for uvicorn
fastapi_app = app.fastapi_app

if __name__ == "__main__":
    import uvicorn
    print("Bulqit Keegan Agent initialized successfully")
    print(f"System Prompt Length: {len(SYSTEM_PROMPT)} characters")
    print(f"Location: {LOCATION}")
    print(f"Gemini API Key Set: {bool(GEMINI_API_KEY)}")
    print("\n✓ Starting agent server...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
