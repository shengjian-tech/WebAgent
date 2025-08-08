import os
import json
import requests
from typing import List
from qwen_agent.tools.base import BaseTool, register_tool
from concurrent.futures import ThreadPoolExecutor
AUTHORIZATION = os.getenv("AUTHORIZATION")
KNOWLEDGEBASE_API_URL = os.getenv("KNOWLEDGEBASE_API_URL")

@register_tool("knowledgeBase", allow_overwrite=True)
class knowledgeBase(BaseTool):
    name = "knowledgeBase"
    description = "Get answer of an question, the user shoud supply a question first."
    parameters = {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "query strings",
                }
            },
        "required": ["question"],
    }

    def call(self, params: str, **kwargs) -> str:
       
        try:
            params = self._verify_json_format_args(params)
            query = params["question"]
        except:
            return f"[knowledgeBase] 参数错误"

        try:
            # 调用外部服务
            payload = json.dumps({
                "messages": [
                    {
                    "role": "user",
                    "content": query
                    }
                ]
                })
            response = requests.post(
                KNOWLEDGEBASE_API_URL,
                headers={"Content-Type": "application/json",'Authorization': AUTHORIZATION},
                data=payload,
                timeout=300
            )
            if response.status_code != 200:
                return f"[knowledgeBase] 外部服务错误: {response.status_code} - {response.text} -{payload}"
            
            data = response.json()
            return data
        except Exception as e:
            return f"[knowledgeBase] 调用外部服务失败: {e}"

   
if __name__ == "__main__":
    print(knowledgeBase().call({"question": "盛见的简介"}))
