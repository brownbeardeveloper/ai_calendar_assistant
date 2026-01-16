import asyncio
import openai
import backoff
import os, dotenv
from prompts.assistant_prompt import SYSTEM_PROMPT

import json

dotenv.load_dotenv()

class LLMService:
    """
    LLM service to parse user messages and generate responses using OpenAI tool calling.

    Attributes:
        client (AsyncOpenAI): The OpenAI client to use for generating responses.
        model_name (str): The name of the model to use for generating responses.
        system_prompt (str): The system prompt to use for generating responses.
    """
    def __init__(self, model_name="gpt-4o") -> None:
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        self.system_prompt = SYSTEM_PROMPT

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    async def run(self, history: list, tools: list = None, tool_map: dict = None) -> str:
        """
        Run the LLM with the given history and tools.
        
        Args:
            history (list): The conversation history.
            tools (list, optional): List of tools definitions for OpenAI.
            tool_map (dict, optional): Mapping of tool names to functions.
        
        Returns:
            str: The final response from the assistant.
        """
        messages = [{"role": "system", "content": self.system_prompt}] + history
        
        # First call to LLM
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # If there are tool calls, execute them
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if tool_map and function_name in tool_map:
                    function_to_call = tool_map[function_name]
                    try:
                        function_response = function_to_call(**function_args)
                        # Ensure response is a string
                        if not isinstance(function_response, str):
                            function_response = json.dumps(function_response)
                    except Exception as e:
                        function_response = f"Error executing tool {function_name}: {str(e)}"
                else:
                    function_response = f"Error: Tool {function_name} not found."

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
            # Second call to LLM to get the final response
            second_response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return second_response.choices[0].message.content
            
        return response_message.content