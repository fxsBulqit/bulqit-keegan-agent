# Bulqit Keegan Voice Agent

Voice agent for Bulqit homeowner outreach calls.

## Features

- Friendly "Keegan" personality for neighborhood outreach
- Integrated knowledge base about Bulqit services
- Powered by Google Gemini AI
- Built with Cartesia Line SDK

## Environment Variables

Create a `.env` file with:

```
CARTESIA_API_KEY=your_cartesia_key
GEMINI_API_KEY=your_gemini_key
VOICE_ID=69267136-1bdc-412f-ad78-0caad210fb40
```

## Files

- `main.py` - Agent entry point and call handler
- `config.py` - Configuration and prompt loader
- `llm_node.py` - Gemini LLM integration
- `knowledge_base.txt` - Bulqit service information
- `../prompt.txt` - Keegan's conversational personality

## Deployment

Deploy to Cartesia:
```bash
cartesia deploy --agent-id YOUR_AGENT_ID
```
