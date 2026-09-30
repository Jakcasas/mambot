import test from 'node:test';
import {buildStudySchedule} from '../static/js/features/planner/planner.controller.js';
import assert from 'node:assert/strict';
import {createChatController} from '../static/js/features/chat/chat.controller.js';
import {createLibraryController} from '../static/js/features/library/library.controller.js';
import {postStream, getJson} from '../static/js/shared/http.js';
import {askQuestion,createSessionStore} from '../static/js/features/chat/chat.api.js';
import {readSystemStatus} from '../static/js/features/system/system.api.js';
import {readLibrary} from '../static/js/features/library/library.api.js';

const planInput={subjects:'Giải tích, Python, Tiếng Anh',startDate:'2026-09-23',startTime:'18:00',endTime:'20:00',minutes:90,weekdays:[1,2,3,4,5,6]};
test('planner respects availability, rest days and exact budget with no overlaps',()=>{
  const plan=buildStudySchedule(planInput);
  assert.equal(plan.days.length,7);assert.equal(plan.days.at(-1).date,'2026-09-29');assert.deepEqual(plan.unassigned,[]);
  const mins=s=>Number(s.slice(0,2))*60+Number(s.slice(3));
  for(const day of plan.days){
    if(day.weekday===0){assert.deepEqual(day.slots,[]);continue;}
    let cursor=1080,total=0;
    for(const slot of day.slots){assert.equal(mins(slot.start),cursor);assert.ok(mins(slot.end)>cursor);assert.ok(mins(slot.end)<=1200);total+=mins(slot.end)-cursor;cursor=mins(slot.end);}
    assert.equal(total,90);assert.ok(day.slots.some(s=>s.kind==='break'));
  }
});
test('planner rejects impossible dates, excess work, invalid days and names',()=>{
  for(const edit of [{startDate:'2026-02-30'},{startDate:'bad'},{startTime:'22:00',endTime:'06:00'},
    {startTime:'18:75'},{minutes:181},{minutes:0},{minutes:125},{weekdays:[]},{weekdays:[1,1]},
    {weekdays:[0,1,2,3,4,5,6]},{weekdays:[8]},{subjects:''},{subjects:'x'.repeat(41)}])
    assert.throws(()=>buildStudySchedule({...planInput,...edit}));
});
test('planner handles leap day and warns when subjects cannot all fit',()=>{
  const plan=buildStudySchedule({...planInput,startDate:'2028-02-28',subjects:'A,B,C',minutes:30,weekdays:[1]});
  assert.equal(plan.days[1].date,'2028-02-29');assert.equal(plan.days[2].date,'2028-03-01');assert.deepEqual(plan.unassigned,['B','C']);
});
test('planner deduplicates subjects and keeps hostile text inert',()=>{
  const plan=buildStudySchedule({...planInput,subjects:'Python, Python, <img src=x>'});
  assert.deepEqual(plan.subjects,['Python','<img src=x>']);
});

test('student support and AI conversation survive streaming without fabricated sources',async()=>{
  const original=globalThis.fetch;
  try{
    for(const mode of ['support','conversation']){
      const events=[{type:'meta',mode,request_id:'support-test',duration_ms:1},
        {type:'token',token:'Mình cùng bạn lập kế hoạch nhé.'},{type:'sources',sources:[]},{type:'done'}];
      globalThis.fetch=async()=>new Response(events.map(e=>JSON.stringify(e)).join('\n'),{headers:{'Content-Type':'application/x-ndjson'}});
      const controller=createChatController();assert.equal(await controller.send('Lập kế hoạch học'),true);
      assert.equal(controller.getState().messages[1].meta.mode,mode);
      assert.deepEqual(controller.getState().sources,[]);
      assert.ok(!controller.exportText().includes('NGUỒN\n'));
    }
  }finally{globalThis.fetch=original;}
});

test('student help modes persist through opt-in session restore with context intact',async()=>{
  for(const mode of ['support','conversation']){
    const memory=memorySession();
    const answer=async(q,h,s,event)=>{
      event({type:'meta',mode,request_id:'support-test'});event({type:'token',token:'Bạn học môn gì?'});
      event({type:'sources',sources:[]});
    };
    const original=createChatController(answer,memory.store);original.setRemember(true);
    await original.send('Lập kế hoạch ôn thi');
    const restored=createChatController(async(q,h,s,event)=>{
      assert.equal(h[0].content,'Lập kế hoạch ôn thi');assert.equal(h[1].content,'Bạn học môn gì?');
      return answer(q,h,s,event);
    },memory.store);
    assert.equal(restored.getState().messages[1].meta.mode,mode);
    assert.equal(await restored.send('Giải tích, 7 ngày, 2 giờ'),true);
  }
});

test('adding support modes does not allow arbitrary server response modes',async()=>{
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async()=>new Response('{"type":"meta","mode":"admin","request_id":"test"}\n',{headers:{'Content-Type':'application/x-ndjson'}});
    await assert.rejects(askQuestion('hi',[],undefined,()=>{}),/chưa hợp lệ/);
  }finally{globalThis.fetch=original;}
});

test('controller owns lifecycle and successful history',async()=>{
  let seen;
  const controller=createChatController(async(q,h,s,event)=>{seen=h;event({type:'token',token:'Xin chào'});event({type:'sources',sources:[{title:'Source'}]});});
  assert.equal(await controller.send('hi'),true);assert.equal(controller.getState().phase,'resolved');
  await controller.send('next');assert.equal(seen.length,2);
  const copy=controller.getState();copy.messages.length=0;assert.equal(controller.getState().messages.length,4);
});
test('duplicate sends rejected; stop blocks stale response and allows next send',async()=>{
  let release,callback;let calls=0;
  const c=createChatController(async(q,h,s,event)=>{calls++;callback=event;await new Promise(r=>release=r);});
  const first=c.send('first');assert.equal(await c.send('duplicate'),false);assert.equal(calls,1);
  c.stop();callback({type:'token',token:'stale'});release();await first;
  assert.equal(c.getState().phase,'cancelled');assert.equal(c.getState().messages[1].content,'');
});
test('reset cannot be overwritten by an old request',async()=>{
  let release,event;
  const c=createChatController(async(q,h,s,cb)=>{event=cb;await new Promise(r=>release=r);});
  const pending=c.send('old');c.reset();event({type:'token',token:'old token'});release();await pending;
  assert.equal(c.getState().phase,'idle');assert.equal(c.getState().messages.length,0);
});
test('API failure is visible and does not poison history',async()=>{
  let calls=0;
  const c=createChatController(async(q,h,s,event)=>{if(!calls++)throw new Error('offline');assert.equal(h.length,0);event({type:'token',token:'ok'});});
  assert.equal(await c.send('hello'),false);assert.equal(c.getState().error,'offline');await c.send('again');assert.equal(c.getState().phase,'resolved');
});
test('only ten history messages are sent',async()=>{
  const c=createChatController(async(q,h,s,event)=>{assert.ok(h.length<=10);event({type:'token',token:'ok'});});
  for(let i=0;i<12;i++)await c.send('question '+i);
});
test('library search supports Vietnamese without accents and category',async()=>{
  const c=createLibraryController(async()=>({items:[{title:'Công nghệ thông tin',text:'Lập trình',category:'major'}]}));let state;c.subscribe(s=>state=s);
  await c.load();c.filter('cong nghe','all');assert.equal(state.visible.length,1);c.filter('cong nghe','tuition');assert.equal(state.visible.length,0);
});
test('NDJSON parser survives split multibyte UTF-8 and a missing trailing newline',async()=>{
  const original=globalThis.fetch;
  try{
    const bytes=new TextEncoder().encode('{"type":"token","token":"Việt"}\n{"type":"done"}');
    globalThis.fetch=async()=>new Response(new ReadableStream({start(c){for(const byte of bytes)c.enqueue(new Uint8Array([byte]));c.close();}}),{headers:{'Content-Type':'application/x-ndjson'}});
    const events=[];await postStream('/test',{},undefined,e=>events.push(e));assert.equal(events[0].token,'Việt');assert.equal(events[1].type,'done');
  } finally {globalThis.fetch=original;}
});
test('incomplete stream is an error, not a successful answer',async()=>{
  const original=globalThis.fetch;
  try {globalThis.fetch=async()=>new Response('{"type":"token","token":"partial"}\n',{headers:{'Content-Type':'application/x-ndjson'}});await assert.rejects(postStream('/test',{},undefined,()=>{}),/bị ngắt/);}
  finally{globalThis.fetch=original;}
});

test('UTF-8 history stays below the request budget without splitting emoji',async()=>{
  const c=createChatController(async(q,h,s,event)=>{
    assert.ok(new TextEncoder().encode(JSON.stringify({question:q,history:h})).length<49152);
    assert.ok(h.length%2===0);
    h.filter(t=>t.role==='assistant').forEach(t=>assert.equal(t.content,'🙂'.repeat(4000)));
    event({type:'token',token:'🙂'.repeat(4001)});
  });
  for(let i=0;i<9;i++)await c.send('Câu hỏi thứ '+i);
});
test('retry replaces a failed pair and preserves only completed context',async()=>{
  let calls=0;
  const c=createChatController(async(q,h,s,event)=>{if(!calls++)throw new Error('offline');assert.equal(h.length,0);event({type:'token',token:'recovered'});});
  await c.send('hello');assert.equal(await c.retry(),true);assert.equal(c.getState().messages.length,2);assert.equal(c.getState().phase,'resolved');
});
test('empty response is rejected and bad input does not crash controller',async()=>{
  const c=createChatController(async()=>{});
  assert.equal(await c.send(null),false);assert.equal(await c.send('hi'),false);assert.equal(c.getState().phase,'error');
});
test('library snapshots cannot mutate internal source data',async()=>{
  const c=createLibraryController(async()=>({items:[{title:'Original',text:'Text',category:'major'}]}));let state;c.subscribe(s=>state=s);
  await c.load();state.visible[0].title='Mutated';c.filter('','all');assert.equal(state.visible[0].title,'Original');
});
test('stalled response times out and releases its reader',async()=>{
  const original=globalThis.fetch;let cancelled=false;
  try {
    globalThis.fetch=async()=>new Response(new ReadableStream({cancel(){cancelled=true;}}),{headers:{'Content-Type':'application/x-ndjson'}});
    await assert.rejects(postStream('/test',{},undefined,()=>{},{timeoutMs:15}),/quá lâu/);
    assert.equal(cancelled,true);
  }finally{globalThis.fetch=original;}
});
test('many short NDJSON lines still obey cumulative byte limit',async()=>{
  const original=globalThis.fetch;
  try {
    const encoder=new TextEncoder();globalThis.fetch=async()=>new Response(new ReadableStream({start(c){for(let i=0;i<20;i++)c.enqueue(encoder.encode('{"type":"token","token":"x"}\n'));c.close();}}),{headers:{'Content-Type':'application/x-ndjson'}});
    await assert.rejects(postStream('/test',{},undefined,()=>{},{maxBytes:100}),/vượt giới hạn/);
  }finally{globalThis.fetch=original;}
});
test('HTML error pages cannot masquerade as JSON API results',async()=>{
  const original=globalThis.fetch;
  try{globalThis.fetch=async()=>new Response('<html>proxy page</html>',{headers:{'Content-Type':'text/html'}});await assert.rejects(getJson('/test'),/sai định dạng/);}
  finally{globalThis.fetch=original;}
});
test('server request id is visible with a safe API error',async()=>{
  const original=globalThis.fetch;
  try{globalThis.fetch=async()=>new Response(JSON.stringify({detail:'Unavailable'}),{status:503,headers:{'X-Request-ID':'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}});await assert.rejects(getJson('/test'),/Mã yêu cầu: aaaaaaaa/);}
  finally{globalThis.fetch=original;}
});
test('chat contract rejects tokens before metadata',async()=>{
  const original=globalThis.fetch;
  try{globalThis.fetch=async()=>new Response('{"type":"token","token":"oops"}\n{"type":"done"}\n',{headers:{'Content-Type':'application/x-ndjson'}});await assert.rejects(askQuestion('hi',[],undefined,()=>{}),/chưa hợp lệ/);}
  finally{globalThis.fetch=original;}
});
test('events after done are rejected',async()=>{
  const original=globalThis.fetch;
  try{globalThis.fetch=async()=>new Response('{"type":"done"}\n{"type":"token","token":"late"}\n',{headers:{'Content-Type':'application/x-ndjson'}});await assert.rejects(postStream('/test',{},undefined,()=>{}),/sau khi kết thúc/);}
  finally{globalThis.fetch=original;}
});

function memorySession(){
  const records=new Map();let clock=100000;
  const storage={getItem:key=>records.get(key)||null,setItem:(key,value)=>records.set(key,value),removeItem:key=>records.delete(key)};
  return {records,storage,store:createSessionStore(()=>storage,()=>clock),advance:ms=>clock+=ms};
}
const reply=async(q,h,s,event)=>{
  event({type:'meta',mode:'retrieval',request_id:'test',duration_ms:10});
  event({type:'token',token:'Câu trả lời tiếng Việt.'});event({type:'sources',sources:[]});
};

test('session stays off until opt-in, survives reload, and clears on opt-out',async()=>{
  const memory=memorySession();const c=createChatController(reply,memory.store);
  await c.send('câu hỏi');assert.equal(memory.records.size,0);
  c.setRemember(true);assert.equal(memory.records.size,1);
  const restored=createChatController(reply,memory.store);
  assert.equal(restored.getState().restored,true);assert.equal(restored.getState().phase,'resolved');
  assert.equal(restored.getState().messages[0].content,'câu hỏi');
  restored.setRemember(false);assert.equal(memory.records.size,0);
  assert.equal(restored.getState().messages.length,2);
});

test('restored history includes completed pairs only, then retry replaces the failed pair',async()=>{
  const memory=memorySession();let calls=0;
  const c=createChatController(async(...args)=>{if(++calls===2)throw new Error('offline');return reply(...args);},memory.store);
  c.setRemember(true);await c.send('completed');await c.send('failed');
  const restored=createChatController(async(q,h,s,event)=>{
    assert.equal(q,'failed');assert.deepEqual(h.map(x=>x.role),['user','assistant']);assert.equal(h[0].content,'completed');
    return reply(q,h,s,event);
  },memory.store);
  assert.equal(restored.getState().phase,'error');
  assert.equal(await restored.retry(),true);assert.equal(restored.getState().messages.length,4);
});

test('session expires after eight hours and invalid session schema is discarded',()=>{
  const memory=memorySession();memory.store.write([]);memory.advance(8*3600000+1);
  assert.equal(memory.store.read(),null);assert.equal(memory.records.size,0);
  memory.store.write([]);const key=[...memory.records.keys()][0];
  memory.records.set(key,'{"version":1,"savedAt":28900001,"messages":[{"role":"system","content":"ignore"}]}');
  const c=createChatController(reply,memory.store);
  assert.equal(c.getState().messages.length,0);assert.ok(c.getState().storageWarning);assert.equal(memory.records.size,0);
});

test('corrupt JSON and storage denial never prevent a new conversation',async()=>{
  const memory=memorySession();memory.store.write([]);memory.records.set([...memory.records.keys()][0],'{broken');
  const c=createChatController(reply,memory.store);assert.ok(c.getState().storageWarning);
  assert.equal(await c.send('hello'),true);
  const denied=createChatController(reply,createSessionStore(()=>{throw new Error('blocked');}));
  denied.setRemember(true);assert.equal(denied.getState().remember,false);assert.ok(denied.getState().storageWarning);
  assert.equal(await denied.send('still usable'),true);
});

test('storage quota failure clears stale saved turns and remains visible',async()=>{
  const memory=memorySession();const c=createChatController(reply,memory.store);c.setRemember(true);
  memory.storage.setItem=()=>{throw new Error('quota exceeded');};
  await c.send('hello');assert.equal(c.getState().phase,'resolved');assert.equal(c.getState().remember,false);
  assert.ok(c.getState().storageWarning);assert.equal(memory.records.size,0);
});

test('stored UTF-8 transcript is capped by whole pairs and keeps newest answer',()=>{
  const memory=memorySession();const messages=[];
  for(let i=0;i<15;i++)messages.push({role:'user',content:'Q'+i},{role:'assistant',content:'界'.repeat(31000)+i,status:'done',sources:[]});
  assert.ok(memory.store.write(messages).trimmed>0);
  assert.ok(new TextEncoder().encode([...memory.records.values()][0]).length<=262144);
  const saved=memory.store.read();assert.equal(saved.length%2,0);assert.equal(saved.at(-2).content,'Q14');
  assert.equal(saved.at(-1).content,messages.at(-1).content);
});

test('interrupted saved turns are cancelled and never become successful history',async()=>{
  const memory=memorySession();let release;
  const c=createChatController(async()=>new Promise(r=>release=r),memory.store);
  c.setRemember(true);const pending=c.send('interrupted');
  const recovered=createChatController(async(q,h,s,event)=>{assert.deepEqual(h,[]);return reply(q,h,s,event);},memory.store);
  assert.equal(recovered.getState().phase,'cancelled');assert.equal(await recovered.retry(),true);
  c.stop();release();await pending;
});

test('reset removes saved content while keeping the opt-in preference',async()=>{
  const memory=memorySession();const c=createChatController(reply,memory.store);c.setRemember(true);await c.send('erase this');c.reset();
  const restored=createChatController(reply,memory.store);
  assert.equal(restored.getState().remember,true);assert.equal(restored.getState().messages.length,0);
  assert.ok(![...memory.records.values()][0].includes('erase this'));
});

test('message ids stay stable across turns; text export keeps sources and partial status',async()=>{
  const c=createChatController(async(q,h,s,event)=>{event({type:'token',token:'Answer'});event({type:'sources',sources:[{title:'Source',url:'https://huit.edu.vn/'}]});if(q==='partial')throw new Error('offline');});
  await c.send('first');const ids=c.getState().messages.map(x=>x.id);await c.send('partial');
  assert.deepEqual(c.getState().messages.slice(0,2).map(x=>x.id),ids);
  assert.equal(new Set(c.getState().messages.map(x=>x.id)).size,4);
  assert.match(c.exportText(),/https:\/\/huit.edu.vn/);assert.match(c.exportText(),/CHƯA HOÀN TẤT/);
});

test('health contract rejects malformed payload and accepts an empty trusted store',async()=>{
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async()=>Response.json({status:'ok',records:'45'});
    await assert.rejects(readSystemStatus(),/không hợp lệ/);
    const data={status:'empty',name:'Mambot',version:'1.2.0',records:0,data_mode:'local',dense_search:false,generation_configured:false,snapshot_date:null,authority:'verified',latest_verified:false};
    globalThis.fetch=async()=>Response.json(data);assert.deepEqual(await readSystemStatus(),data);
  }finally{globalThis.fetch=original;}
});

test('all feature requests resolve relative to the installed subsite',async()=>{
  const original=globalThis.fetch;const paths=[];
  try{
    globalThis.fetch=async url=>{
      paths.push(new URL(url).pathname);
      if(String(url).endsWith('chat-stream'))return new Response('{"type":"meta","mode":"no-match","request_id":"test"}\n{"type":"token","token":"Hello"}\n{"type":"sources","sources":[]}\n{"type":"done"}',{headers:{'Content-Type':'application/x-ndjson'}});
      if(String(url).endsWith('library'))return Response.json({items:[]});
      return Response.json({status:'ok',name:'Mambot',version:'1.2.0',records:45,data_mode:'local',dense_search:false,generation_configured:false,snapshot_date:'2026-07-27',authority:'verified',latest_verified:false});
    };
    await askQuestion('hi',[],undefined,()=>{});await readLibrary();await readSystemStatus();
    const installedRoot=new URL('../',import.meta.url).pathname;
    assert.deepEqual(paths,['api/chat-stream','api/library','api/health'].map(path=>installedRoot+path));
  }finally{globalThis.fetch=original;}
});

test('null error payload preserves HTTP status, request id and Retry-After',async()=>{
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async()=>new Response('null',{status:503,headers:{'Content-Type':'application/json','Retry-After':'2','X-Request-ID':'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}});
    await assert.rejects(getJson('/test'),error=>/503/.test(error.message)&&/2 giây/.test(error.message)&&/aaaaaaaa-aaaa/.test(error.message));
  }finally{globalThis.fetch=original;}
});

test('a stalled stream cancellation cannot hold the request past its deadline',async()=>{
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async()=>new Response(new ReadableStream({cancel(){return new Promise(()=>{});}}),{headers:{'Content-Type':'application/x-ndjson'}});
    const outcome=await Promise.race([
      postStream('/test',{},undefined,()=>{},{timeoutMs:10}).then(()=> 'unexpected success',error=>error.message),
      new Promise(resolve=>setTimeout(()=>resolve('still blocked'),100))
    ]);
    assert.match(outcome,/quá lâu/);
  }finally{globalThis.fetch=original;}
});

test('invalid UTF-8 is reported as invalid content, not a network outage',async()=>{
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async()=>new Response(new Uint8Array([0xff]),{headers:{'Content-Type':'application/json'}});
    await assert.rejects(getJson('/test'),/UTF-8 không hợp lệ/);
  }finally{globalThis.fetch=original;}
});

test('oversized response rejects promptly even if underlying cancellation hangs',async()=>{
  const original=globalThis.fetch;
  try{
    globalThis.fetch=async()=>new Response(new ReadableStream({start(c){c.enqueue(new Uint8Array(30));},cancel(){return new Promise(()=>{});}}),{headers:{'Content-Type':'application/x-ndjson'}});
    const outcome=await Promise.race([
      postStream('/test',{},undefined,()=>{},{timeoutMs:20,maxBytes:10}).then(()=> 'unexpected success',error=>error.message),
      new Promise(resolve=>setTimeout(()=>resolve('still blocked'),100))
    ]);
    assert.match(outcome,/vượt giới hạn/);
  }finally{globalThis.fetch=original;}
});

test('clarification is a complete valid streamed reply and survives an opted-in reload',async()=>{
  const original=globalThis.fetch;const memory=memorySession();
  try{
    const events=[{type:'meta',mode:'clarification',request_id:'clarify-test',duration_ms:1},
      {type:'token',token:'Bạn đang hỏi ngành nào?'},{type:'sources',sources:[]},{type:'done'}];
    globalThis.fetch=async()=>new Response(events.map(event=>JSON.stringify(event)).join('\n'),{headers:{'Content-Type':'application/x-ndjson'}});
    const c=createChatController(askQuestion,memory.store);c.setRemember(true);
    assert.equal(await c.send('Ngành đó?'),true);
    assert.equal(c.getState().messages.at(-1).meta.mode,'clarification');
    const restored=createChatController(askQuestion,memory.store);
    assert.equal(restored.getState().phase,'resolved');
    assert.equal(restored.getState().messages.at(-1).meta.mode,'clarification');
    assert.equal(restored.getState().messages.at(-1).content,'Bạn đang hỏi ngành nào?');
  }finally{globalThis.fetch=original;}
});

test('unknown reply mode is still rejected by the stream and session boundaries',async()=>{
  const original=globalThis.fetch;const memory=memorySession();
  try{
    globalThis.fetch=async()=>new Response('{"type":"meta","mode":"arbitrary","request_id":"test"}\n',{headers:{'Content-Type':'application/x-ndjson'}});
    await assert.rejects(askQuestion('hello',[],undefined,()=>{}),/chưa hợp lệ/);
    assert.throws(()=>memory.store.write([{role:'user',content:'hello'},
      {role:'assistant',content:'answer',status:'done',sources:[],meta:{mode:'arbitrary',request_id:'test'}}]),/metadata/);
  }finally{globalThis.fetch=original;}
});

test('stop then retry suppresses a late failed stream and keeps completed history',async()=>{
  let releaseOld,oldEvents;let calls=0;let retriedHistory;
  const c=createChatController(async(q,h,signal,event)=>{
    calls++;
    if(calls===2){oldEvents=event;await new Promise(resolve=>releaseOld=resolve);throw new Error('late failure');}
    if(calls===3)retriedHistory=h;
    event({type:'token',token:calls===1?'first answer':'retry answer'});
    event({type:'sources',sources:[]});
  });
  await c.send('first question');const pending=c.send('second question');
  oldEvents({type:'token',token:'unfinished'});c.stop();
  assert.equal(await c.retry(),true);
  oldEvents({type:'token',token:'stale'});releaseOld();await pending;
  assert.equal(c.getState().phase,'resolved');assert.equal(c.getState().error,null);
  assert.equal(c.getState().messages.length,4);
  assert.equal(c.getState().messages.at(-1).content,'retry answer');
  assert.deepEqual(retriedHistory.map(turn=>turn.content),['first question','first answer']);
});

test('library search ignores surrounding and repeated whitespace and Unicode accent form',async()=>{
  const c=createLibraryController(async()=>({items:[{title:'Công nghệ thông tin',text:'Lập trình',category:'major'}]}));
  let state;c.subscribe(value=>state=value);await c.load();
  for(const query of ['  cong   nghe\tthong tin  ','  Công  nghệ  '.normalize('NFD')]){
    c.filter(query,'all');assert.equal(state.visible.length,1);
  }
  c.filter(' \n\t ','all');assert.equal(state.visible.length,1);
});

test('library multiword search requires every term and keeps the category filter',async()=>{
  const c=createLibraryController(async()=>({items:[
    {title:'Công nghệ thông tin',text:'Mã ngành 7480201. Lập trình phần mềm',category:'major'},
    {title:'Học phí',text:'Ngành Công nghệ thông tin',category:'tuition'}]}));
  let state;c.subscribe(value=>state=value);await c.load();
  c.filter('lap trinh cong nghe','major');assert.equal(state.visible.length,1);
  c.filter('7480201 cong nghe','all');assert.equal(state.visible.length,1);
  c.filter('cong nghe','tuition');assert.equal(state.visible.length,1);assert.equal(state.visible[0].category,'tuition');
  c.filter('lap trinh hoc bong','all');assert.equal(state.visible.length,0);
});

test('library keeps a filter entered while loading and ignores a stale older response',async()=>{
  const finish=[];const c=createLibraryController(()=>new Promise(resolve=>finish.push(resolve)));
  let state;c.subscribe(value=>state=value);
  const first=c.load();c.filter('marketing','major');const second=c.load();
  finish[1]({items:[{title:'Marketing',text:'Nội dung',category:'major'}]});await second;
  finish[0]({items:[{title:'Old data',text:'Nội dung',category:'major'}]});await first;
  assert.equal(state.loading,false);assert.equal(state.visible.length,1);assert.equal(state.visible[0].title,'Marketing');
});

const source17={title:'Nguồn học phí',url:'https://ts.huit.edu.vn/',category:'tuition',retrieved_at:'2026-07-27',similarity:0.5,year:2026};
function stream17(meta={},sources=[source17]){
  const events=[{type:'meta',mode:'retrieval',request_id:'session-test',...meta},
    {type:'token',token:'Câu trả lời đã kiểm tra.'},{type:'sources',sources},{type:'done'}];
  return new Response(events.map(event=>JSON.stringify(event)).join('\n'),{headers:{'Content-Type':'application/x-ndjson'}});
}

test('stream rejects malformed optional metadata before completing a reply',async()=>{
  const original=globalThis.fetch;
  try{
    for(const meta of [{duration_ms:-1},{duration_ms:'10'},{warning:{}},{warning:'x'.repeat(1001)},
      {request_id:''},{request_id:'x'.repeat(101)},{data_mode:'untrusted'}]){
      globalThis.fetch=async()=>stream17(meta);
      await assert.rejects(askQuestion('học phí',[],undefined,()=>{}),/chưa hợp lệ/);
    }
  }finally{globalThis.fetch=original;}
});

test('stream and stored sources enforce the same field and year limits',async()=>{
  const original=globalThis.fetch;const memory=memorySession();
  try{
    for(const fields of [{title:'x'.repeat(2001)},{url:'x'.repeat(2049)},{category:'x'.repeat(81)},
      {retrieved_at:'x'.repeat(65)},{year:'2026'},{year:2026.5},{year:9007199254740992}]){
      const sources=[{...source17,...fields}];globalThis.fetch=async()=>stream17({},sources);
      await assert.rejects(askQuestion('học phí',[],undefined,()=>{}),/chưa hợp lệ/);
      assert.throws(()=>memory.store.write([{role:'user',content:'học phí'},
        {role:'assistant',content:'answer',status:'done',sources}]),/source/);
    }
  }finally{globalThis.fetch=original;}
});

test('reload and JSON export preserve source year and data mode, including legacy sessions',async()=>{
  const original=globalThis.fetch;
  try{
    for(const year of [2026,null,undefined]){
      const memory=memorySession();
      globalThis.fetch=async()=>stream17({data_mode:'local',duration_ms:0},[{...source17,year}]);
      const c=createChatController(askQuestion,memory.store);c.setRemember(true);
      assert.equal(await c.send('học phí'),true);
      const restored=createChatController(askQuestion,memory.store);
      assert.equal(restored.getState().messages.at(-1).meta.data_mode,'local');
      assert.equal(restored.exportConversation().messages.at(-1).sources[0].year,year);
      assert.equal(restored.getState().phase,'resolved');
    }
  }finally{globalThis.fetch=original;}
});

test('a malformed stream cannot erase previous saved turns or disable remembering',async()=>{
  const original=globalThis.fetch;const memory=memorySession();
  try{
    globalThis.fetch=async()=>stream17();
    const c=createChatController(askQuestion,memory.store);c.setRemember(true);
    assert.equal(await c.send('câu hỏi đầu tiên'),true);
    globalThis.fetch=async()=>stream17({duration_ms:-1});
    assert.equal(await c.send('câu hỏi tiếp theo'),false);
    assert.equal(c.getState().remember,true);assert.equal(c.getState().storageWarning,null);
    const saved=memory.store.read();assert.equal(saved.length,4);
    assert.equal(saved[0].content,'câu hỏi đầu tiên');assert.equal(saved[1].status,'done');
    assert.equal(saved[3].status,'error');
  }finally{globalThis.fetch=original;}
});

test('new-chat reset requires confirmation for unsent content and existing conversation',async()=>{
  const c=createChatController(reply,memorySession().store);
  assert.equal(c.needsResetConfirmation(''),false);
  assert.equal(c.needsResetConfirmation(' \n '),false);
  assert.equal(c.needsResetConfirmation('bản nháp chưa gửi'),true);
  await c.send('câu hỏi');assert.equal(c.needsResetConfirmation(''),true);
  c.reset();assert.equal(c.needsResetConfirmation(''),false);
});

test('a burst of answer fragments keeps full text without hundreds of UI snapshots',async()=>{
  const c=createChatController(async(q,h,s,event)=>{
    for(let i=0;i<256;i++)event({type:'token',token:'Nội dung '+i+'\n'});
    event({type:'sources',sources:[]});
  },memorySession().store);
  let updates=0;c.subscribe(()=>updates++);
  assert.equal(await c.send('câu hỏi'),true);
  assert.equal(c.getState().messages.at(-1).content,Array.from({length:256},(_,i)=>'Nội dung '+i+'\n').join(''));
  assert.ok(updates<=6,`Too many UI snapshots for one burst: ${updates}`);
});

test('stop preserves the last received fragment and suppresses queued progress notifications',async()=>{
  let event,release;
  const c=createChatController(async(q,h,s,emit)=>{event=emit;await new Promise(resolve=>release=resolve);},memorySession().store);
  let updates=0;c.subscribe(()=>updates++);
  const pending=c.send('câu hỏi');event({type:'token',token:'Phần một. '});event({type:'token',token:'Phần hai.'});
  c.stop();const afterStop=updates;
  await Promise.resolve();assert.equal(updates,afterStop);
  assert.equal(c.getState().messages.at(-1).content,'Phần một. Phần hai.');
  assert.equal(c.getState().phase,'cancelled');
  event({type:'token',token:'Cũ'});release();await pending;
  assert.equal(c.getState().messages.at(-1).content,'Phần một. Phần hai.');
});

test('reset cancels queued progress while a new conversation can complete normally',async()=>{
  let release,event;
  const c=createChatController(async(q,h,s,emit)=>{
    if(q==='old'){event=emit;await new Promise(resolve=>release=resolve);}
    else{assert.deepEqual(h,[]);emit({type:'token',token:'New answer'});}
  },memorySession().store);
  let updates=0;c.subscribe(()=>updates++);
  const old=c.send('old');event({type:'token',token:'Old answer'});c.reset();
  const afterReset=updates;await Promise.resolve();assert.equal(updates,afterReset);
  assert.equal(await c.send('new'),true);release();await old;
  assert.equal(c.getState().messages.length,2);assert.equal(c.getState().messages.at(-1).content,'New answer');
});

test('batched partial text survives failure but never becomes successful context',async()=>{
  let calls=0;
  const c=createChatController(async(q,h,s,event)=>{
    if(!calls++){
      event({type:'token',token:'Partial '});event({type:'token',token:'answer'});throw new Error('disconnected');
    }
    assert.deepEqual(h,[]);event({type:'token',token:'Recovered'});
  },memorySession().store);
  assert.equal(await c.send('first'),false);assert.equal(c.getState().messages.at(-1).content,'Partial answer');
  assert.equal(c.getState().phase,'error');assert.equal(await c.retry(),true);
  assert.equal(c.getState().messages.length,2);assert.equal(c.getState().messages.at(-1).content,'Recovered');
});

test('text export distinguishes source year from snapshot date after restoring a session',async()=>{
  const memory=memorySession();
  const c=createChatController(async(q,h,s,event)=>{
    event({type:'meta',mode:'retrieval',request_id:'year-export'});
    event({type:'token',token:'Nội dung [1] [2]'});
    event({type:'sources',sources:[{...source17,year:2025},{...source17,year:2026}]});
  },memory.store);
  c.setRemember(true);await c.send('So sánh hai năm');
  const restored=createChatController(reply,memory.store);
  const text=restored.exportText();
  assert.match(text,/Năm: 2025/);assert.match(text,/Năm: 2026/);
  assert.match(text,/Bản lưu: 2026-07-27/);
});

test('source export does not fabricate a year for legacy or undated sources',async()=>{
  const c=createChatController(async(q,h,s,event)=>{
    event({type:'token',token:'Nội dung'});
    event({type:'sources',sources:[{title:'Nguồn cũ',url:'https://huit.edu.vn/',year:null}]});
  },memorySession().store);
  await c.send('hỏi');const text=c.exportText();
  assert.match(text,/Nguồn cũ/);assert.doesNotMatch(text,/Năm:|undefined|null/);
});
