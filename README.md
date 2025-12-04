# Bulqit Homeowner Agent (Cartesia)

Voice agent for homeowner follow-up calls about Bulqit services - coloring book recipients in Encino & Sherman Oaks.

**Test Change:** Testing GitHub auto-deploy - timestamp: 2025-11-17 11:16 AM CST

## Customization

To customize this agent for your use case, follow the instructions below.

### Update constants in `config.py`

- **AGENT_PROMPT**: Define the agent's personality, role, and conversation style
- **LOCATION**: Set the agent's current location context
- **INITIAL_MESSAGE**: Set the first message sent to the user when the call is started. Set to None for outbound agents.

## Running the Agent

### Quick Start

```bash
uv run main.py
```

The agent will start on `http://localhost:8000`. Use the `/chats` endpoint to obtain a websocket url that you can connect to to talk to your agent.

### Environment Variables

Required:
- `GEMINI_API_KEY`: Your Google Gemini API key

Optional:
- `PORT`: Server port (default: 8000)
