#!/bin/bash

cd $(dirname $0) || exit

# GOOGLE_SEARCH_KEY
export GOOGLE_SEARCH_KEY=''
export SEARCH_API_URL='https://google.serper.dev/search'

# JINA
export JINA_API_KEY=''
export JINA_API_URL='https://r.jina.ai/'
# OPENAI 优先使用OpenAI接口
export OPENAI_API_KEY=''
export OPENAI_BASE_URL='https://api.openai.com/v1'
export OPENAI_MODEL='gpt-4o'
# DASHSCOPE
#export DASHSCOPE_API_KEY=''
#export DASHSCOPE_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
#export DASHSCOPE_MODEL='qwen-plus'

# WebDancer 模型
export WEbDANCER_API_KEY='EMPTY'
export WEbDANCER_BASE_URL='http://127.0.0.1:8004/v1'
export WEbDANCER_MODEL='WebDancer-QwQ-32B'

# knowledgeBase tool 配置
export AUTHORIZATION='Bearer xxx'
export KNOWLEDGEBASE_API_URL='xxx'

#  上传图片配置
export UPLOAD_IMAGE_API_URL='xxx'


cd ..

python -m demos.assistant_qwq_chat