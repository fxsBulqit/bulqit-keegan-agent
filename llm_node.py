"""
LLM Reasoning Node for Keegan Agent
Integrates with Google Gemini for conversational responses
"""

import os
from typing import AsyncGenerator, Union
from line import ReasoningNode
from line.nodes.conversation_context import ConversationContext
from line.events import AgentResponse

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class GeminiReasoningNode(ReasoningNode):
    """Reasoning node that uses Google Gemini for responses"""

    def __init__(self, system_prompt: str, api_key: str, model_name: str = "gemini-pro"):
        super().__init__(system_prompt=system_prompt)

        if not HAS_GEMINI:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[Union[AgentResponse], None]:
        """Process conversation context and generate response using Gemini"""

        # Build conversation history for Gemini
        messages = []
        for event in context.events:
            if hasattr(event, 'text'):
                role = "user" if event.__class__.__name__ == "UserTranscriptionReceived" else "model"
                messages.append({"role": role, "parts": [event.text]})

        # Get the latest user message
        if not messages:
            return

        latest_user_message = messages[-1] if messages else None
        if not latest_user_message:
            return

        # Generate response
        try:
            # Create chat with history
            chat = self.model.start_chat(history=messages[:-1] if len(messages) > 1 else [])

            # Add system prompt context
            prompt_with_context = f"{self.system_prompt}\n\nUser: {latest_user_message['parts'][0]}"

            response = chat.send_message(prompt_with_context)

            # Yield response in chunks
            yield AgentResponse(text=response.text)

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            yield AgentResponse(text="I'm having trouble connecting right now. Could you try again?")
