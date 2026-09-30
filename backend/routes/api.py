import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

class Turn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    role: Literal['user','assistant']
    content: str=Field(min_length=1,max_length=4000)

class ChatRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question: str=Field(min_length=1,max_length=800)
    history: list[Turn]=Field(default_factory=list,max_length=10)

    @field_validator('question')
    @classmethod
    def trim_question(cls,value):
        value=value.strip()
        if not value: raise ValueError('empty question')
        return value

def make_router(chat_service, library_service):
    router=APIRouter()

    @router.post('/api/chat')
    def chat(body:ChatRequest, request:Request):
        return chat_service.answer(body.question,[t.model_dump() for t in body.history],request.state.request_id)

    @router.post('/api/chat-stream')
    def chat_stream(body:ChatRequest, request:Request):
        # Compute first: validation/provider failures can still produce an HTTP error.
        result=chat_service.answer(body.question,[t.model_dump() for t in body.history],request.state.request_id)
        def events():
            yield json.dumps({'type':'meta',**{k:v for k,v in result.items() if k not in ('answer','sources')}},ensure_ascii=False)+'\n'
            for i in range(0,len(result['answer']),64):
                yield json.dumps({'type':'token','token':result['answer'][i:i+64]},ensure_ascii=False)+'\n'
            yield json.dumps({'type':'sources','sources':result['sources']},ensure_ascii=False)+'\n'
            yield json.dumps({'type':'done'})+'\n'
        return StreamingResponse(events(),media_type='application/x-ndjson',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})

    @router.get('/api/library')
    def library(request:Request): return library_service.list_sources(request.state.request_id)

    @router.get('/api/health')
    def health(request:Request): return library_service.health(request.state.request_id)
    return router
