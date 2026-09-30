// The only browser transport primitive. Requests have deadlines and bounded responses.
const MAX_BYTES = 1048576;
const validId = value => typeof value === 'string' && /^[0-9a-f-]{36}$/i.test(value);

async function withResponse(url, options, consume, timeoutMs) {
  const abort = new AbortController();
  let timedOut = false;
  const cancel = () => abort.abort();
  options.signal?.addEventListener('abort', cancel, {once:true});
  if (options.signal?.aborted) cancel();
  const timer = setTimeout(() => {timedOut=true; abort.abort();}, timeoutMs);
  try {
    abort.signal.throwIfAborted();
    const result = await fetch(url, {...options, credentials:'same-origin', signal:abort.signal});
    if (!result.ok) {
      let payload = {};
      try {
        const parsed=JSON.parse(await readText(result, abort.signal, 8192));
        if(parsed&&typeof parsed==='object'&&!Array.isArray(parsed))payload=parsed;
      } catch {}
      const detail = typeof payload.detail === 'string' ? payload.detail.slice(0,500) : `Kết nối gặp lỗi (${result.status}).`;
      const id = result.headers.get('x-request-id') || payload.request_id;
      const delay=result.headers.get('retry-after');
      const seconds=delay&&/^\d{1,5}$/.test(delay)?Number(delay):0;
      const retry=[429,503].includes(result.status)&&seconds>0?` Thử lại sau ${seconds} giây.`:'';
      throw new Error(detail + retry + (validId(id) ? ` Mã yêu cầu: ${id}` : ''));
    }
    return await consume(result, abort.signal);
  } catch (error) {
    if (timedOut) throw new Error('Máy chủ phản hồi quá lâu. Vui lòng thử lại.');
    if (options.signal?.aborted) throw new DOMException('Đã hủy yêu cầu.', 'AbortError');
    if (error instanceof TypeError) throw new Error('Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.');
    throw error;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener('abort', cancel);
  }
}

async function readChunks(result, signal, maxBytes, consume) {
  if (!result.body) throw new Error('Máy chủ không trả nội dung.');
  const reader = result.body.getReader();
  const cancel = () => {reader.cancel().catch(()=>{});};
  signal.addEventListener('abort',cancel,{once:true});
  let size=0;
  try {
    while (true) {
      signal.throwIfAborted();
      const part=await reader.read();
      signal.throwIfAborted();
      if(part.done)break;
      size+=part.value.byteLength;
      if(size>maxBytes)throw new Error('Phản hồi vượt giới hạn cho phép.');
      consume(part.value);
    }
  } finally {
    signal.removeEventListener('abort',cancel);
    // Underlying cancellation can itself hang; cleanup must not hold a failed request open.
    reader.cancel().catch(()=>{});
    reader.releaseLock();
  }
}
async function readText(result,signal,maxBytes=MAX_BYTES) {
  const decoder=new TextDecoder('utf-8',{fatal:true});let text='';
  await readChunks(result,signal,maxBytes,bytes=>{text+=decode(decoder,bytes,true);});
  return text+decode(decoder);
}
function decode(decoder,bytes,stream=false){
  try{return decoder.decode(bytes,{stream});}
  catch{throw new Error('Máy chủ trả văn bản UTF-8 không hợp lệ. Vui lòng thử lại.');}
}
function requireType(result, expected) {
  const type=(result.headers.get('content-type')||'').split(';')[0].trim().toLowerCase();
  if(type!==expected)throw new Error('Máy chủ trả dữ liệu sai định dạng. Vui lòng thử lại.');
}
export async function getJson(url, signal, {timeoutMs=15000}={}) {
  return withResponse(url,{signal},async(result,combined)=>{
    requireType(result,'application/json');
    try{return JSON.parse(await readText(result,combined));}
    catch(error){if(error instanceof SyntaxError)throw new Error('Dữ liệu máy chủ không hợp lệ.');throw error;}
  },timeoutMs);
}
export async function postStream(url, body, signal, onEvent, {timeoutMs=45000,maxBytes=MAX_BYTES}={}) {
  return withResponse(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal},async(result,combined)=>{
    requireType(result,'application/x-ndjson');
    const decoder=new TextDecoder('utf-8',{fatal:true});let buffer='';let done=false;
    const consume=line=>{
      if(!line.trim())return;
      if(done)throw new Error('Luồng phản hồi có dữ liệu sau khi kết thúc.');
      let event;
      try{event=JSON.parse(line);}catch{throw new Error('Luồng phản hồi chứa dữ liệu không hợp lệ.');}
      if(!event || typeof event!=='object' || Array.isArray(event))throw new Error('Sự kiện phản hồi không hợp lệ.');
      if(event.type==='done')done=true;
      onEvent(event);
    };
    await readChunks(result,combined,maxBytes,bytes=>{
      buffer+=decode(decoder,bytes,true);
      let end;while((end=buffer.indexOf('\n'))>=0){consume(buffer.slice(0,end));buffer=buffer.slice(end+1);}
    });
    buffer+=decode(decoder);consume(buffer);
    if(!done)throw new Error('Kết nối bị ngắt trước khi nhận đủ câu trả lời.');
  },timeoutMs);
}
