import os
from typing import List, Optional
from google import genai
from google.genai import types
from src.core.tool import BaseTool
import json
import logging

logger = logging.getLogger(__name__)

class Agent:
    def __init__(
        self,
        name: str,
        model: str = "gemini-2.5-flash",
        tools: Optional[List[BaseTool]] = None,
        instruction: Optional[str] = None
    ):
        self.name = name
        self.model = model
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.instruction = instruction
        self.client = genai.Client()
    
    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get_genai_tools(self) -> List[types.Tool]:
        if not self.tools:
            return []
        
        genai_function_declarations = []
        for tool_name, tool in self.tools.items():
            genai_function_declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.parameters
                )
            )
        
        return [types.Tool(function_declarations=genai_function_declarations)]

    def run(self, message: str) -> str:
        config = types.GenerateContentConfig()
        if self.instruction:
            config.system_instruction = self.instruction
        
        genai_tools = self.get_genai_tools()
        if genai_tools:
            config.tools = genai_tools

        try:
            # First pass: user message to model
            response = self.client.models.generate_content(
                model=self.model,
                contents=message,
                config=config,
            )

            # Check if there are function calls
            if response.function_calls:
                # We need to execute the function calls and send results back
                messages = [
                    types.Content(role="user", parts=[types.Part.from_text(text=message)]),
                    response.candidates[0].content
                ]
                
                parts = []
                for function_call in response.function_calls:
                    name = function_call.name
                    args = function_call.args
                    
                    if name in self.tools:
                        try:
                            logger.info(f"Executing tool {name} with args: {args}")
                            tool_result = self.tools[name].execute(**args)
                        except Exception as e:
                            logger.error(f"Error executing tool {name}: {e}")
                            tool_result = f"Error: {e}"
                        
                        parts.append(types.Part.from_function_response(
                            name=name,
                            response={"result": tool_result}
                        ))
                    else:
                        parts.append(types.Part.from_function_response(
                            name=name,
                            response={"error": f"Tool {name} not found"}
                        ))
                
                messages.append(types.Content(role="user", parts=parts))
                
                # Second pass: send tool results back to model
                final_response = self.client.models.generate_content(
                    model=self.model,
                    contents=messages,
                    config=config
                )
                return final_response.text
            else:
                return response.text

        except Exception as e:
            logger.error(f"Error in Agent.run: {e}")
            return f"Error: {e}"