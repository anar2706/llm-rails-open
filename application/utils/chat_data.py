import json
import time
import asyncio
import traceback

from langchain.chat_models import ChatOpenAI
from fastapi.responses import StreamingResponse
from langchain.schema import HumanMessage
from fastapi.exceptions import HTTPException
from application.helpers.core import send_log_slack_message
from application.models.callback import AsyncIteratorCallbackHandler, wrap_done

from application.helpers.logger import logger
from application.helpers.constants import default_document
from application.utils.retriever import WeaviateHybridSearchRetriever
from application.utils.send_task import send_usage_task
from models import Usage


class ChatWithData:
    def __init__(self, schema, model, gpt_model, text, stream, user_data, 
                message_id, msg_record, session_id, prompt, datastore_id):
        
        self.final  = ''
        self.model  = model
        self.schema = schema
        self.text   = text
        self.stream = stream
        self.user_data = user_data
        self.gpt_model = gpt_model
        self.message_id = message_id
        self.msg_record = msg_record
        self.session_id = session_id
        self.prompt     = prompt
        self.datastore_id = datastore_id


    def search_documents(self):
        retriever = WeaviateHybridSearchRetriever(self.schema, self.model, self.user_data['key'])
        docs = retriever.get_relevant_documents(self.text)['docs']
        
        Usage.create(type='datastore',subtype='chat',unit='search',quantity=1,meta={"datastore_id": self.datastore_id},
            api_id=self.user_data['id'],workspace_id=self.user_data['workspace_id'],created=time.time())
	
        if docs:
            return docs
        else:
            return default_document
        
    async def listen_for_disconnect(self, receive) -> None:
        while True:
            message = await receive()
            logger.info(f'message {message}')
            
            if message["type"] == "http.disconnect":
                logger.info(f'Disconnect {self.final}')
                self.msg_record.message = self.final
                self.msg_record.save()
                
                send_usage_task(input=self.messages[0].content,output=self.final,
                    user=self.user_data,model=self.gpt_model,msg_id=self.message_id,process=True)
            
                break
    
    def get_message_format(self, docs):
        all_docs = [f"{doc.text}" for doc in docs]
        base_template = f"""SYSTEM: {self.prompt}. Follow Chat History.
                    =========
                    DOCUMENTS: {all_docs}
                    =========
                    """
        template = (
                base_template + f"""
                                    HUMAN: {self.text}
                                    =========
                                    AI Assistant:"""
        )
        
        self.messages =  [HumanMessage(content=template)]
        return self.messages
            
    def send_message_sync(self,docs):
        llm = ChatOpenAI(model_name=self.gpt_model, verbose=True, streaming=False, 
            n=1, temperature=0.2, max_retries=3)
       
        messages = self.get_message_format(docs)
        try:
            resp  = llm.generate([messages])
            usage = resp.llm_output['token_usage']
            send_usage_task(input=usage['prompt_tokens'],output=usage['completion_tokens'],
                user=self.user_data,model=self.gpt_model,msg_id=self.message_id,process=False)
        
        except Exception as e:
            print(traceback.format_exc())
            send_log_slack_message(f'OpenAI {traceback.format_exc()}')
            raise HTTPException(400,str(e))
        
        resp = resp.generations[0][0].text
        self.msg_record.message = resp
        self.msg_record.save()
        
        return {'text':resp}
        

    async def send_message(self, docs):
        callback = AsyncIteratorCallbackHandler()
        llm = ChatOpenAI(model_name=self.gpt_model, verbose=True, streaming=True, n=1,
            callbacks=[callback], temperature=0.2, max_retries=3)
        
        messages = self.get_message_format(docs)        
        task = asyncio.create_task(wrap_done(llm.agenerate([messages]), callback.done))
        
        async for token in callback.aiter():
            self.final += token
            message = json.dumps({
                'id':self.message_id, 
                'session_id':self.session_id, 
                "message":token
            }, ensure_ascii=False)
            
            yield f"data: {message}\n\n"

        try:
            await task

        except BaseException as e:
            print(traceback.format_exc())
            send_log_slack_message(f'OpenAI {traceback.format_exc()}')
            message = json.dumps({"error":str(e)})
            yield f"data: {message}\n\n"
           
        else:
            logger.info(f'Ended {callback.response}')
            send_usage_task(input=self.messages[0].content,output=callback.response,
                user=self.user_data,model=self.gpt_model,msg_id=self.message_id,process=True)
            
            self.msg_record.message = callback.response
            self.msg_record.save()
        
    def generate(self, docs):
        if self.stream is True:
            resp =  StreamingResponse(self.send_message(docs),
                media_type="text/event-stream")
            
            resp.listen_for_disconnect = self.listen_for_disconnect
            return resp
            
        else:
            return self.send_message_sync(docs)

        
