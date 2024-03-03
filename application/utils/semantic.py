import os
import json
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage
from fastapi.exceptions import HTTPException
from application.helpers.core import send_log_slack_message
from application.utils.send_task import send_usage_task

def summarize(docs, query, user_data):
    llm = AzureChatOpenAI(openai_api_base='https://roboforce.openai.azure.com',openai_api_key=json.loads(os.environ['app'])['azure-openai'],openai_api_version="2023-05-15",
        model='gpt-35-turbo-16k',deployment_name='gpt3516k',openai_api_type = "azure",request_timeout=1200,
        streaming=False,temperature=0.2)

    system_prompt = """You are a search bot that takes results and summarizes them as a coherent answer:
- You must only use information from the provided facts.
- Only cite the most relevant facts that answer the question accurately.
- If the facts are of low relevance and not useful, then respond with "I don't know"."""
    base_template = f"""SYSTEM: {system_prompt}.
                =========
                DOCUMENTS: {docs}
                =========
                """
    template = (
            base_template + f"""
                                HUMAN: {query}
                                =========
                                AI Assistant:"""
    )

    try:
        resp  = llm.generate([[HumanMessage(content=template)]])
        usage = resp.llm_output['token_usage']
        print(usage)
        send_usage_task(input=usage['prompt_tokens'],output=usage['completion_tokens'],
                user=user_data, model='gpt-3.5-turbo', msg_id=0, process=False)
       
    except Exception as e:
        send_log_slack_message(f'OpenAI {e}')
        raise HTTPException(400,str(e))
    
    return {'text':resp.generations[0][0].text}

