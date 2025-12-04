"""
LLM Reasoning Node for Keegan Agent
Integrates with Google Gemini for conversational responses
"""

from typing import AsyncGenerator, Union, Optional
from line import ReasoningNode
from line.nodes.conversation_context import ConversationContext
from line.events import AgentResponse
from line.utils.gemini_utils import convert_messages_to_gemini
from google import genai
from google.genai import types as gemini_types


class GeminiReasoningNode(ReasoningNode):
    """Reasoning node that uses Google Gemini for responses"""

    def __init__(
        self,
        system_prompt: str,
        api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_context_length: int = 100
    ):
        super().__init__(system_prompt=system_prompt, max_context_length=max_context_length)

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature

        # Create generation config
        self.generation_config = gemini_types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=500,  # Increased for fuller conversational responses
        )

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[Union[AgentResponse], None]:
        """
        Process the conversation context and generate response using Gemini.
        This is called by the base class generate() method.
        """

        if not context.events:
            return

        # Convert events to Gemini messages format using SDK utility
        messages = convert_messages_to_gemini(context.events)

        if not messages:
            return

        try:
            # Generate response using Gemini
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=messages,
                config=self.generation_config,
            )

            # Yield response chunks
            async for msg in stream:
                if msg.text:
                    yield AgentResponse(content=msg.text)

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            yield AgentResponse(content="I'm having trouble connecting right now. Could you try again?")
