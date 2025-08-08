import os
import json
import requests
from typing import List
from qwen_agent.tools.base import BaseTool, register_tool
from concurrent.futures import ThreadPoolExecutor
MAX_MULTIQUERY_NUM = os.getenv("MAX_MULTIQUERY_NUM", 3)
GOOGLE_SEARCH_KEY = os.getenv("GOOGLE_SEARCH_KEY")

@register_tool("weather", allow_overwrite=True)
class Weather(BaseTool):
    name = "weather"
    description = "Get weather of an location, the user shoud supply a location first."
    parameters = {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },
        "required": ["location"],
    }

    def call(self, params: str, **kwargs) -> str:
       
        try:
            params = self._verify_json_format_args(params)
            query = params["location"]
        except:
            return "[location] Invalid request format: Input must be a JSON object containing 'query' field"

        return "The current temperature in "+query+" is 24°C."

   
if __name__ == "__main__":
    print(Weather().call({"location": "Hangzhou"}))
