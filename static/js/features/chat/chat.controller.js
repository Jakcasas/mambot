import {askQuestion, chatSession} from './chat.api.js';

export function createChatController(api = askQuestion, session = chatSession) {
  let state={phase:'idle',messages:[],sources:[],error:null,remember:false,restored:false,storageWarning:null};
  let sequence=0; let messageId=0; let pending=null; let history=[]; const listeners=new Set();
  try {
    const saved=session.read();
    if(saved){
      state.messages=saved.map(message=>({...message,id:++messageId}));
      const last=state.messages.at(-1);
      state={...state,remember:true,restored:!!last,sources:last?.sources||[],phase:last?(last.status==='done'?'resolved':last.status):'idle'};
      for(let i=0;i<saved.length;i+=2)if(saved[i+1].status==='done')history.push(
        {role:'user',content:saved[i].content},{role:'assistant',content:Array.from(saved[i+1].content).slice(0,4000).join('')});
      history=history.slice(-10);
    }
  } catch {
    try{session.clear();}catch{}
    state.storageWarning='Không đọc được phiên đã lưu. Bạn vẫn có thể trò chuyện bình thường.';
  }
  const snapshot=()=>structuredClone(state);
  let scheduled=null;
  const notify=()=>listeners.forEach(listener=>listener(snapshot()));
  const publish=(patch,coalesce=false)=>{
    state={...state,...patch};
    if(coalesce){
      // Keep state current, but clone/render once for fragments delivered together.
      if(scheduled)return;
      const ticket={};scheduled=ticket;
      queueMicrotask(()=>{if(scheduled!==ticket)return;scheduled=null;notify();});
    }else{scheduled=null;notify();}
  };
  const updateLast=patch=>{state.messages=state.messages.map((message,index)=>index===state.messages.length-1?{...message,...patch}:message);};
  const boundedHistory=()=>{
    const recent=history.slice(-10);
    while(recent.length && new TextEncoder().encode(JSON.stringify(recent)).length>32000)recent.splice(0,2);
    return recent;
  };
  const persist=()=>{
    if(!state.remember)return;
    try{
      const result=session.write(state.messages);
      publish({storageWarning:result?.trimmed?'Phiên lưu chỉ giữ các lượt gần nhất do giới hạn dung lượng. Xuất hội thoại để giữ đầy đủ.':null});
    }catch{
      try{session.clear();}catch{}
      publish({remember:false,storageWarning:'Trình duyệt không lưu được phiên. Hãy xuất hội thoại trước khi tải lại trang.'});
    }
  };
  const controller = {
    subscribe(listener){listeners.add(listener);listener(snapshot());return()=>listeners.delete(listener);},
    getState:snapshot,
    needsResetConfirmation(draft=''){return state.messages.length>0||!!draft.trim();},
    async send(value) {
      if(typeof value!=='string')return false;
      const question=value.trim();
      if(!question || ['pending','streaming'].includes(state.phase)) return false;
      if(question.length>800){publish({error:'Câu hỏi tối đa 800 ký tự.'});return false;}
      const id=++sequence; const abort=new AbortController();pending=abort;
      publish({phase:'pending',error:null,sources:[],restored:false,messages:[...state.messages,
        {id:++messageId,role:'user',content:question},{id:++messageId,role:'assistant',content:'',status:'pending',sources:[]}]});
      persist();
      let answer='';let meta={};let sources=[];
      try {
        await api(question,boundedHistory(),abort.signal,event=>{
          if(id!==sequence || abort.signal.aborted) return;
          if(event.type==='meta') meta=event;
          if(event.type==='token') {
            if(typeof event.token!=='string'||answer.length+event.token.length>32000)throw new Error('Nội dung phản hồi không hợp lệ hoặc quá dài.');
            answer+=event.token;updateLast({content:answer,status:'streaming'});publish({phase:'streaming'},true);
          }
          if(event.type==='sources') {sources=event.sources;updateLast({sources});publish({sources},true);}
        });
        if(id!==sequence || abort.signal.aborted) return false;
        if(!answer.trim())throw new Error('Máy chủ trả câu trả lời trống. Vui lòng thử lại.');
        history=[...history,{role:'user',content:question},{role:'assistant',content:Array.from(answer).slice(0,4000).join('')}].slice(-10);
        updateLast({content:answer,status:'done',meta,sources});publish({phase:'resolved'});
        return true;
      } catch(error) {
        if(id!==sequence) return false;
        const cancelled=error?.name==='AbortError' || abort.signal.aborted;
        updateLast({status:cancelled?'cancelled':'error',content:answer || (cancelled?'Đã dừng câu trả lời.':'Chưa nhận được câu trả lời.')});
        publish({phase:cancelled?'cancelled':'error',error:cancelled?null:(error?.message || 'Không thể kết nối máy chủ.')});return false;
      } finally {if(id===sequence){pending=null;persist();}}
    },
    stop(){if(!pending)return;pending.abort();++sequence;pending=null;updateLast({status:'cancelled'});publish({phase:'cancelled'});persist();},
    retry(){
      if(!['error','cancelled'].includes(state.phase))return Promise.resolve(false);
      const previous=state.messages[state.messages.length-2];
      if(previous?.role!=='user')return Promise.resolve(false);
      state.messages=state.messages.slice(0,-2);
      return controller.send(previous.content);
    },
    reset(){pending?.abort();++sequence;pending=null;history=[];publish({phase:'idle',messages:[],sources:[],error:null,restored:false});persist();},
    setRemember(value){
      publish({remember:!!value,restored:false,storageWarning:null});
      if(value)persist();
      else try{session.clear();}catch{publish({storageWarning:'Chưa xóa được phiên lưu do trình duyệt chặn truy cập. Hãy đóng tab để kết thúc phiên.'});}
    },
    exportConversation(){return {application:'Mambot',exported_at:new Date().toISOString(),messages:snapshot().messages};},
    exportText(){
      return 'MAMBOT — HỘI THOẠI\n'+new Date().toLocaleString('vi-VN')+'\n\n'+state.messages.map(message=>
        (message.role==='user'?'BẠN':'MAMBOT')+(message.role==='assistant'&&message.status!=='done'?' [CHƯA HOÀN TẤT]':'')+'\n'+message.content+
        (message.sources?.length?'\n\nNGUỒN\n'+message.sources.map((source,i)=>`[${i+1}] ${source.title}\n${source.url}`+
          (source.year!=null?`\nNăm: ${source.year}`:'')+(source.retrieved_at?`\nBản lưu: ${source.retrieved_at.slice(0,10)}`:'')).join('\n'):'')).join('\n\n────────────\n\n');
    },
    dispose(){pending?.abort();++sequence;scheduled=null;listeners.clear();}
  };
  return controller;
}
