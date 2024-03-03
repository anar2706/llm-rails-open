import os
import time
import json
import asyncio
import traceback

from fastapi.exceptions import HTTPException
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from fastapi.responses import StreamingResponse
from application.helpers.core import send_log_slack_message
from application.models.callback import AsyncIteratorCallbackHandler, wrap_done
from application.helpers.logger import logger
from application.utils.send_task import send_usage_task


class Chat:
    def __init__(self, query, stream, user_data, message_pid, msg_record, gpt_model, prompt, session_id = None):
        self.final  = ''
        self.query  = query
        self.stream = stream
        self.prompt = prompt
        self.user_data   = user_data
        self.message_pid = message_pid
        self.msg_record  = msg_record
        self.gpt_model   = gpt_model
        self.session_id  = session_id

        
    async def listen_for_disconnect(self, receive) -> None:
        while True:
            message = await receive()
            logger.info(f'message {message}')
            if message["type"] == "http.disconnect":
                logger.info(f'Disconnect {self.final}')
                
                self.msg_record.message = self.final
                self.msg_record.save()
                break
            
    def send_message_sync(self):
        print(self.gpt_model)
        llm = ChatOpenAI(model_name=self.gpt_model, verbose=True, streaming=False, n=1,temperature=0.2)
       
        template = (
            f"""
            SYSTEM: {self.prompt}
            =========
            HUMAN: {self.query}
            =========
            AI Assistant:"""
        )
        
        try:
            resp  = llm.generate([[HumanMessage(content=template)]])
            usage = resp.llm_output['token_usage']
            send_usage_task(input=usage['prompt_tokens'],output=usage['completion_tokens'],
                user=self.user_data,model=self.gpt_model, msg_id=self.message_pid,process=False)
            
        except Exception as e:
            print(traceback.format_exc())
            send_log_slack_message(f'OpenAI {traceback.format_exc()}')
            raise HTTPException(400,str(e))
        
        resp = resp.generations[0][0].text
        self.msg_record.message = resp
        self.msg_record.save()

        return {'text':resp,'id':self.message_pid,'session_id':self.session_id,'docs':[]}
        

    async def send_message(self):
        callback = AsyncIteratorCallbackHandler()
        llm = ChatOpenAI(model_name=self.gpt_model, verbose=True, streaming=True, n=1,
            callbacks=[callback], temperature=0.2, max_retries=3)
        
        template = f"""
            SYSTEM: {self.prompt}
            =========
            HUMAN: {self.query}
            =========
            AI Assistant:
        """
               
        task = asyncio.create_task(wrap_done(llm.agenerate([[HumanMessage(content=template)]]), callback.done))
        
        async for token in callback.aiter():
            self.final += token
            message = {'id':self.message_pid, "message":token}
            
            if self.session_id:
                message['session_id'] = self.session_id
            
            message = json.dumps(message, ensure_ascii=False)
            yield f"data: {message}\n\n"


        try:
            await task

        except BaseException as e:
            print(traceback.format_exc())
            send_log_slack_message(f'OpenAI {traceback.format_exc()}')
            message = json.dumps({"error":str(e)})
            yield f"data: {message}\n\n"
           
        else:
            send_usage_task(input=template, output=callback.response,
                user=self.user_data, model=self.gpt_model, msg_id=self.message_pid, process=True)
            
            logger.info(f'Ended nodoc {callback.response}')
            self.msg_record.message = callback.response
            self.msg_record.save()
        
    def generate(self):
        
        if self.stream is True:
            StreamingResponse.listen_for_disconnect = self.listen_for_disconnect
            return StreamingResponse(self.send_message(),
                media_type="text/event-stream")
            
        else:
            return self.send_message_sync()

        
    
    