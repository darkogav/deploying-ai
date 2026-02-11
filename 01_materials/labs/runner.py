#append src

import sys
sys.path.append('../../05_src/')

# load logger
from utils.logger import get_logger
_logs = get_logger(__name__, log_dir='../../06_logs/')

# send mgs to log
_logs.info('This is a log message.')

# load secrets
from dotenv import load_dotenv
load_dotenv('../../05_src/.secrets')

import os
os.getenv('LOG_LEVEL')

from openai import OpenAI

prompt = "can you tell me the capital of Uganda?"


client = OpenAI(base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1', 
                api_key='any value',
                default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')})

response = client.responses.create(
    model = 'gpt-4o-mini',
    input = prompt
    
)

print("Question:", prompt)
print("Answer:", response.output_text)

#print(response.input)
#print(response.output_text)

#response.model_dump()

