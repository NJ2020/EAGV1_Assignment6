agentic_agent/
+-- agent/  (Decision Making by Agents)
¦   +-- core.py              # Main reasoning + loop logic from talk2mcp
¦   +-- config.py            # Config, timeouts, flags
¦   +-- state.py             # Tracks state, iteration, history
+-- perception/
¦   +-- llm_interface.py     # Gemini wrapper, evaluation logic
¦   +-- parsers.py           # Prompt parsing / formatting
¦   +-- sensors.py           # Optional for external inputs
+-- memory/
¦   +-- short_term.py        # Holds recent preference state
¦   +-- long_term.py         # Placeholder for future vector store
¦   +-- retrieval.py         # Fetch memory items by key/context
+-- planning/
¦   +-- agent_controller.py  # What to do next, prompt builder
¦   +-- decision_engine.py   # Strategy logic, fallback handler
¦   +-- intent_classifier.py # Recognize task types from input
+-- actions/
¦   +-- tools.py             # Registered tools
¦   +-- executor.py          # Tool invoker
¦   +-- interfaces/
¦       +-- paint_interface.py  # Paint-specific tools from example2_Neeresh.py
+-- main.py                  # Entrypoint, launches agent
+-- .env                     # Contains GEMINI_API_KEY

How to run the code:

python main.py

main.py ? runs agent/core.py

core.py ? connects to paint_interface.py (MCP server)

Tools are discovered dynamically.

A prompt is generated, evaluated, and the LLM instructs what to do.

The MCP client executes Paint commands like opening Paint, adding text, etc.

