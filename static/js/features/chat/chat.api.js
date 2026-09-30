import {postStream} from '../../shared/http.js';
const text=(value,max)=>typeof value==='string'&&value.length<=max;
const validMeta=meta=>meta&&['retrieval','generated','no-match','clarification','support','conversation'].includes(meta.mode)&&
  text(meta.request_id,100)&&!!meta.request_id.trim()&&
  (meta.warning==null||text(meta.warning,1000))&&
  (meta.duration_ms===undefined||(Number.isFinite(meta.duration_ms)&&meta.duration_ms>=0))&&
  (meta.data_mode===undefined||['local','mongo'].includes(meta.data_mode));
const validSource=source=>source&&text(source.title,2000)&&text(source.url,2048)&&
  text(source.category,80)&&text(source.retrieved_at,64)&&
  Number.isFinite(source.similarity)&&source.similarity>=0&&source.similarity<=1&&
  (source.year==null||Number.isSafeInteger(source.year));

export function askQuestion(question, history, signal, onEvent) {
  let phase='start', hasText=false;
  return postStream(new URL('../../../../api/chat-stream', import.meta.url), {question, history}, signal, event=>{
    const invalid=()=>{throw new Error('Câu trả lời nhận được chưa hợp lệ. Vui lòng thử lại.');};
    if(event.type==='meta') {
      if(phase!=='start'||!validMeta(event))invalid();
      phase='text';
    } else if(event.type==='token') {
      if(phase!=='text'||typeof event.token!=='string'||event.token.length>16000)invalid();
      hasText ||= Boolean(event.token.trim());
    } else if(event.type==='sources') {
      if(phase!=='text'||!Array.isArray(event.sources)||event.sources.length>20)invalid();
      if(!event.sources.every(validSource))invalid();
      phase='sources';
    } else if(event.type==='done') {
      if(phase!=='sources'||!hasText)invalid();
      phase='done';
    } else invalid();
    onEvent(event);
  });
}

// Browser storage stays behind the feature API; nothing is stored until opt-in.
export function createSessionStore(storage=()=>globalThis.sessionStorage, now=()=>Date.now()) {
  const key='mambot:session:v1:'+new URL('.',import.meta.url).pathname;
  const maxBytes=262144, ttl=8*60*60*1000;
  const bytes=value=>new TextEncoder().encode(value).length;
  function sanitize(messages){
    if(!Array.isArray(messages)||messages.length%2||messages.length>100)throw new Error('invalid session');
    return messages.map((message,index)=>{
      if(!message||message.role!==(index%2?'assistant':'user')||!text(message.content,index%2?32000:800))throw new Error('invalid message');
      const clean={role:message.role,content:message.content};
      if(message.role==='user'){
        if(!message.content.trim())throw new Error('empty question');
        return clean;
      }
      if(!['done','error','cancelled'].includes(message.status))throw new Error('invalid status');
      if(message.status==='done'&&!message.content.trim())throw new Error('empty answer');
      clean.status=message.status;
      if(!Array.isArray(message.sources)||message.sources.length>20)throw new Error('invalid sources');
      clean.sources=message.sources.map(source=>{
        if(!validSource(source))throw new Error('invalid source');
        const saved={title:source.title,url:source.url,category:source.category,retrieved_at:source.retrieved_at,similarity:source.similarity};
        if(source.year!==undefined)saved.year=source.year;
        return saved;
      });
      const meta=message.meta;
      if(meta!=null){
        if(!validMeta(meta))throw new Error('invalid metadata');
        clean.meta={mode:meta.mode,request_id:meta.request_id,warning:meta.warning||null};
        if(meta.duration_ms!==undefined)clean.meta.duration_ms=meta.duration_ms;
        if(meta.data_mode!==undefined)clean.meta.data_mode=meta.data_mode;
      }
      return clean;
    });
  }
  return {
    read(){
      const raw=storage()?.getItem(key);if(!raw)return null;
      if(bytes(raw)>maxBytes)throw new Error('oversized session');
      const saved=JSON.parse(raw);
      if(saved?.version!==1||!Number.isFinite(saved.savedAt)||now()<saved.savedAt||now()-saved.savedAt>ttl){this.clear();return null;}
      return sanitize(saved.messages);
    },
    write(messages){
      const recent=messages.slice(-100).map(message=>({...message,status:['pending','streaming'].includes(message.status)?'cancelled':message.status}));
      const clean=sanitize(recent);
      let raw;
      do {
        raw=JSON.stringify({version:1,savedAt:now(),messages:clean});
        if(bytes(raw)<=maxBytes)break;
        clean.splice(0,2);
      } while(clean.length);
      if(bytes(raw)>maxBytes)throw new Error('oversized session');
      const target=storage();if(!target)throw new Error('storage unavailable');
      target.setItem(key,raw);
      return {trimmed:messages.length-clean.length};
    },
    clear(){storage()?.removeItem(key);}
  };
}
export const chatSession=createSessionStore();
