# ### main.py

# import asyncio
# from agent.core import run_agent

# if __name__ == "__main__":
#     asyncio.run(run_agent())



### main.py

import asyncio
from agent.core import AgentRunner

if __name__ == "__main__":
    agent = AgentRunner()
    asyncio.run(agent.run())