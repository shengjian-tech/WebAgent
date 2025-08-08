import copy
from typing import Dict, Iterator, List, Literal, Union, Optional

from qwen_agent.agents import Assistant
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import  USER, FUNCTION, Message, DEFAULT_SYSTEM_MESSAGE,SYSTEM,ROLE
from qwen_agent.tools import BaseTool
from qwen_agent.log import logger
from pathlib import Path
import requests
from urllib.parse import urlparse, unquote
import os

UPLOAD_IMAGE_API_URL = os.getenv("UPLOAD_IMAGE_API_URL")

class SearchAgent(Assistant):

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None,
                 rag_cfg: Optional[Dict] = None,
                 extra: Optional[Dict] = {},
                 custom_user_prompt: Optional[str] = '',
                 make_system_prompt = None,
                 addtional_agent = None):
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message=system_message,
                         name=name,
                         description=description,
                         files=files,
                         rag_cfg=rag_cfg)
        self.extra = extra
        self.custom_user_prompt = custom_user_prompt
        self.make_system_prompt = make_system_prompt
        self.addtional_agent = addtional_agent

    def insert_in_custom_user_prompt(self, messages: List[Message]) -> List[Message]:
        for message in messages:
            if message.role == USER:
                message.content[0].text = self.custom_user_prompt + message.content[0].text
                break
        return messages
    def _run(self,
             messages: List[Message],
             lang: Literal['en', 'zh'] = 'zh',
             knowledge: str = '',
             **kwargs) -> Iterator[List[Message]]:
        messages = self._prepend_knowledge_prompt(messages=messages, lang=lang, knowledge=knowledge, **kwargs)
        messages = copy.deepcopy(messages)
        self.insert_in_custom_user_prompt(messages=messages)
        if self.make_system_prompt:
            if not messages or messages[0][ROLE] != SYSTEM:
                messages.insert(0, Message(role=SYSTEM, content=self.make_system_prompt()))
        for msg in messages:
            if isinstance(msg.content, list):
                #assert len(msg.content) == 1
                ## 记录上传的文件路径
                content_text = msg.content[0].text
                for i in range(1,len(msg.content)): 
                    #logger.info("上传的文件路径:"+"---"+str(i)+"-------"+msg.content[i])
                    # 转成 Path 对象
                    image_path = msg.content[i]["image"]
                    if image_path is None:
                        break
                    # 解析 file:// URL
                    if image_path.startswith("file:"):
                        parsed = urlparse(image_path)  # 解析 URL
                        path = Path(unquote(parsed.path))  # 转成 Path 并解码中文/空格
                    else:
                        path = Path(image_path)
                    # 只处理图片
                    if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:

                        with open(path, 'rb') as f:
                            files = [
                                ('file', (path.name, f, 'image/png'))
                            ]
                            response = requests.post(UPLOAD_IMAGE_API_URL, files=files, timeout=300)

                        if response.status_code != 200:
                            return f"[knowledgeBase] 外部服务错误: {response.status_code} - {response.text}"

                        result = response.json()

                        # 兼容 result 是 dict 或 list 的情况
                        if isinstance(result, dict):
                            content_text += result.get("data", "")
                        elif isinstance(result, list):
                            for item in result:
                                if isinstance(item, dict):
                                    content_text += item.get("data", "")

                logger.info("解析出来的内容:"+content_text)    
                msg.content = content_text
              
            if msg.role == USER:
                msg.content = msg.content.strip()

        reasoning = self.extra.get('reasoning', True)
        num_llm_calls_available = self.extra.get('max_llm_calls', 20)
        response = []
        while True and num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            extra_generate_cfg = {'lang': lang}
            if kwargs.get('seed') is not None:
                extra_generate_cfg['seed'] = kwargs['seed']
            output_stream = self._call_llm(messages=messages,
                                           functions=[func.function for func in self.function_map.values()],
                                           extra_generate_cfg=extra_generate_cfg)
            output: List[Message] = []
            for output in output_stream:
                if output:
                    first_msg = output[0]
                    if reasoning and isinstance(first_msg.content, str):
                        first_msg.content = "<think>\n" + first_msg.content.strip()
                    yield response + output
            if output:
                response.extend(output)
                messages.extend(output)
                used_any_tool = False
                for out in output:
                    use_tool, tool_name, tool_args, _ = self._detect_tool(out)
                    logger.info(f"{self.name} use_tool: {use_tool}, tool_name: {tool_name}, tool_args: {tool_args}")
                    if use_tool:
                        tool_result = self._call_tool(tool_name, tool_args, messages=messages, **kwargs)
                        fn_msg = Message(
                            role=FUNCTION,
                            name=tool_name,
                            content=tool_result,
                        )
                        messages.append(fn_msg)
                        response.append(fn_msg)
                        yield response
                        used_any_tool = True
                if not used_any_tool:
                    logger.info(f'{self.name} not used any tool, skip out')
                    break
        yield response

        if self.addtional_agent:
            new_messages = copy.deepcopy(messages)
            new_messages.pop()
            new_response = copy.deepcopy(response)
            new_response.pop()
            if new_messages[0][ROLE] == SYSTEM:
                # Add the system instruction to the agent
                new_messages[0].content = self.addtional_agent.make_system_prompt()
            print(new_messages)
            for rsp in self.addtional_agent._run(messages=new_messages, **kwargs):
                yield new_response + rsp
        