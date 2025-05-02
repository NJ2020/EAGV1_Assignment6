### core.py

from agent.state import reset_state, last_response, iteration, iteration_response
from agent.config import MAX_ITERATIONS
from perception.llm_interface import generate_with_timeout, evaluate_prompt, client
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


system_prompt_nj = f"""You are an agent working with Microsoft Paint in iterations. 
                                    You have access to various Microsoft Paint tools. 
                                """
query_nj = """ 

    Your task is to follow the step-by-step plan below to accomplish the goal. 
    Think carefully before each step, explain your reasoning, identify the type of reasoning being used, 
    and use tools as needed.

    Goal:
    Step 1: Open Microsoft Paint.  
    Step 2: Add text 'INDIA' in Opened Paint App.

    Available tools:
    {tools_description}

    You must follow this reasoning and response format for each step:
    1. Step Reasoning: [Brief explanation of why and what you're doing]
    2. Reasoning Type: [e.g., lookup, tool-use, spatial reasoning, sequencing]
    3. Tool Decision: [if using a tool, state which one and what parameters it needs]
    4. Self-Check: [verify input/output validity or sanity check]
    5. Response Line (MUST be ONE line, NO other text):
    FUNCTION_CALL: function_name|param1|param2|...
    FINAL_ANSWER: [string value returned by the function call]
    6. If uncertain or if a tool fails (Error Handling or Fallbacks), use:
    - FUNCTION_CALL: report_error|[describe issue briefly]

    Examples:
    - FUNCTION_CALL: draw_rectangle|10|50|10|50
    - FUNCTION_CALL: add_text_in_paint|INDIA
    - FINAL_ANSWER: open_paint function called successfully....1111
    - FUNCTION_CALL: report_error|Unable to locate rectangle area

    Important Instructions:
    - Proceed step-by-step, one action per turn.
    - Do not skip steps or assume outcomes.
    - Do not include any explanation outside of the prescribed format.
    - Responses outside the "Response Line" will be ignored.

"""

class AgentRunner:
    def __init__(self):
        self.session = None
        self.tools = []
        self.system_prompt = system_prompt_nj
        self.query = query_nj

    async def initialize_session(self):
        server_params = StdioServerParameters(
            command="python",
            args=["actions/interfaces/paint_interface.py"]
        )

        self.stdio_client = stdio_client(server_params)
        self.client_context = self.stdio_client.__aenter__()
        read, write = await self.client_context
        self.session_context = ClientSession(read, write)
        self.session = await self.session_context.__aenter__()
        await self.session.initialize()

    async def load_tools(self):
        tools_result = await self.session.list_tools()
        self.tools = tools_result.tools
        tool_descriptions = [
            f"{i+1}. {t.name} - {getattr(t, 'description', 'No description')}" for i, t in enumerate(self.tools)
        ]
        self.system_prompt = "You are an agent working with Microsoft Paint.\nAvailable tools:\n" + "\n".join(tool_descriptions)


    async def run_iterations(self):
        global iteration, last_response

        while iteration < MAX_ITERATIONS:
            print(f"\n------- Iteration {iteration + 1} -------")
            current_query = self.query if last_response is None else f"{self.query}\n\n{' '.join(iteration_response)}\nWhat should I do next?"
            prompt = f"{self.system_prompt}\n\nQuery: {current_query}"

            try:
                response = await generate_with_timeout(prompt)
                response_text = response.text.strip()

                for line in response_text.split('\n'):
                    if line.strip().startswith("FUNCTION_CALL:"):
                        response_text = line.strip()
                        break
            except Exception as e:
                print(f"Error generating response: {e}")
                break

            if response_text.startswith("FUNCTION_CALL:"):
                await self.handle_function_call(response_text)
            elif response_text.startswith("FINAL_ANSWER:"):
                print("\n=== Agent Execution Complete ===")
                break

            iteration += 1

    async def handle_function_call(self, line):
        global last_response, iteration_response

        _, function_info = line.split(":", 1)
        parts = [p.strip() for p in function_info.split("|")]
        func_name, params = parts[0], parts[1:]

        try:
            tool = next((t for t in self.tools if t.name == func_name), None)
            if not tool:
                raise ValueError(f"Unknown tool: {func_name}")

            arguments = self.convert_params_to_args(tool.inputSchema.get('properties', {}), params)
            result = await self.session.call_tool(func_name, arguments=arguments)

            if hasattr(result, 'content'):
                content = result.content
                output = [item.text if hasattr(item, 'text') else str(item) for item in content] if isinstance(content, list) else str(content)
            else:
                output = str(result)

            output_str = f"[{', '.join(output)}]" if isinstance(output, list) else output
            iteration_response.append(
                f"Iteration {iteration+1}: Called {func_name} with {arguments}, got {output_str}"
            )
            last_response = output

        except Exception as e:
            import traceback
            traceback.print_exc()
            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")

    def convert_params_to_args(self, schema, params):
        args = {}
        for name, spec in schema.items():
            if not params:
                raise ValueError(f"Missing value for {name}")
            value = params.pop(0)
            if spec['type'] == 'integer':
                args[name] = int(value)
            elif spec['type'] == 'number':
                args[name] = float(value)
            elif spec['type'] == 'array':
                args[name] = [int(x.strip()) for x in value.strip('[]').split(',')]
            else:
                args[name] = value
        return args


    async def run(self):
        try:
            reset_state()
            await self.initialize_session()
            await self.load_tools()
            print("Prompt Evaluation:", evaluate_prompt(self.system_prompt + self.query))
            await self.run_iterations()
        finally:
            await self.session_context.__aexit__(None, None, None)
            await self.stdio_client.__aexit__(None, None, None)
