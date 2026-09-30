import {createChatController} from './features/chat/chat.controller.js';
import {createLibraryController} from './features/library/library.controller.js';
import {createSystemController} from './features/system/system.controller.js';
import {buildStudySchedule} from './features/planner/planner.controller.js';

const $=selector=>document.querySelector(selector);
const chat=createChatController(), library=createLibraryController(), system=createSystemController();
let currentPage='chat';let libraryOpened=false;
const messageNodes=new Map();let sourcesKey='';let announcedId=null;
const labels={major:'NGÀNH HỌC',tuition:'HỌC PHÍ',cutoff:'ĐIỂM TUYỂN SINH',admission:'XÉT TUYỂN',scholarship:'HỌC BỔNG',contact:'LIÊN HỆ'};
function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
function safeLink(url){try{if(typeof url!=='string'||/[\\\u0000-\u0020\u007f]/.test(url))return null;const parsed=new URL(url);return parsed.protocol==='https:'&&!parsed.username&&!parsed.password&&(!parsed.port||parsed.port==='443')&&(parsed.hostname==='huit.edu.vn'||parsed.hostname.endsWith('.huit.edu.vn'))?parsed.href:null;}catch{return null;}}
function sourceAnchor(url){const a=el('a');const safe=safeLink(url);if(safe){a.href=safe;a.target='_blank';a.rel='noopener noreferrer';}return a;}

function showPage(name){
  if(!['chat','library','system'].includes(name))name='chat';
  if(currentPage==='chat'&&name!=='chat')chat.stop();
  currentPage=name;
  document.querySelectorAll('.page').forEach(page=>{page.hidden=page.id!==`page-${name}`;});
  document.querySelectorAll('[data-page]').forEach(button=>{button.classList.toggle('active',button.dataset.page===name);if(button.dataset.page===name)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');});
  if(name==='library'&&!libraryOpened){libraryOpened=true;library.load();}
  if(name==='system')system.reload();
}
document.querySelectorAll('[data-page]').forEach(button=>button.addEventListener('click',()=>{location.hash=button.dataset.page;}));
window.addEventListener('hashchange',()=>showPage(location.hash.slice(1)));
showPage(location.hash.slice(1)||'chat');

chat.subscribe(state=>{
  const busy=['pending','streaming'].includes(state.phase);
  $('#welcome').hidden=state.messages.length>0;
  $('#chat-shortcuts').hidden=!state.messages.length;
  $('#send-chat').hidden=busy;$('#stop-chat').hidden=!busy;
  $('#question').readOnly=busy;
  $('#question').setAttribute('aria-busy',String(busy));
  $('#export-chat').disabled=!state.messages.length;$('#export-json').disabled=!state.messages.length;
  $('#remember-chat').checked=state.remember;
  $('#session-note').textContent=state.remember?(state.restored?'Đã khôi phục hội thoại. ':'')+'Lưu trong phiên tab, hết hạn sau 8 giờ không cập nhật. Bỏ chọn để xóa bản lưu.':'Chưa bật lưu phiên. Tải lại trang sẽ xóa hội thoại.';
  $('#session-warning').hidden=!state.storageWarning;$('#session-warning').textContent=state.storageWarning||'';
  document.querySelectorAll('[data-question]').forEach(button=>button.disabled=busy);
  $('#chat-error').hidden=!state.error;$('#chat-error').textContent=state.error||'';
  $('#retry-chat').hidden=!['error','cancelled'].includes(state.phase);
  const status={idle:'Sẵn sàng lắng nghe. Bạn muốn bắt đầu từ đâu?',pending:'Mambot đang chuẩn bị câu trả lời…',streaming:'Mambot đang trả lời…',resolved:'Đã trả lời. Bạn có thể mở nguồn để đọc thêm.',cancelled:'Đã dừng. Bạn có thể gửi câu hỏi khác.',error:'Chưa hoàn tất. Hãy thử gửi lại câu hỏi.'};
  const replyMode=state.messages.at(-1)?.meta?.mode;
  $('#chat-status').textContent=state.phase==='resolved'?(replyMode==='clarification'?'Mambot cần bạn làm rõ câu hỏi. Hãy trả lời tiếp ở ô nhập.':replyMode==='no-match'?'Chưa có dữ liệu phù hợp. Thử nêu rõ ngành, chủ đề hoặc năm.':!state.sources.length?'Bạn cứ hỏi tiếp. Mình sẽ cùng bạn làm rõ từng bước.':status.resolved):status[state.phase];
  const container=$('#messages');const nearBottom=container.scrollHeight-container.scrollTop-container.clientHeight<100;
  const present=new Set(state.messages.map(message=>message.id));
  for(const [id,nodes] of messageNodes)if(!present.has(id)){nodes.article.remove();messageNodes.delete(id);}
  state.messages.forEach(message=>{
    let nodes=messageNodes.get(message.id);
    if(!nodes){
      const article=el('article','message '+message.role),body=el('div','message-body'),foot=el('div','message-foot');
      article.dataset.messageId=String(message.id);
      article.append(el('div','message-label',message.role==='user'?'BẠN / QUESTION':'MAMBOT / ANSWER'),body);
      if(message.role==='assistant')article.append(foot);
      nodes={article,body,foot,status:null};messageNodes.set(message.id,nodes);container.append(article);
    }
    const content=message.content||(['pending','streaming'].includes(message.status)?'Mình đang xem câu hỏi của bạn…':'Đã dừng.');
    if(nodes.body.textContent!==content)nodes.body.textContent=content;
    if(message.role==='assistant'&&nodes.status!==message.status){
      nodes.status=message.status;const foot=nodes.foot;foot.replaceChildren();
      if(message.status==='done'){
        const modeLabels={generated:'DIỄN ĐẠT BẰNG AI · CÓ NGUỒN',conversation:'GỢI Ý BẰNG AI · THAM KHẢO',support:'HƯỚNG DẪN TỪ MAMBOT',clarification:'CẦN LÀM RÕ CÂU HỎI','no-match':'CHƯA CÓ DỮ LIỆU PHÙ HỢP'};
        foot.append(el('span','',modeLabels[message.meta?.mode]||(message.sources?.length?'TRÍCH ĐOẠN TỪ KHO TRI THỨC':'TRÒ CHUYỆN CÙNG MAMBOT')));
        if(message.meta?.duration_ms!==undefined)foot.append(el('span','',message.meta.duration_ms+' MS'));
        const copy=el('button','copy-answer','SAO CHÉP');copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(message.content);copy.textContent='ĐÃ SAO CHÉP';}catch{copy.textContent='HÃY CHỌN VÀ SAO CHÉP VĂN BẢN';}});foot.append(copy);
        if(message.meta?.warning)foot.append(el('span','',message.meta.warning));
        message.sources?.forEach((source,index)=>{const a=sourceAnchor(source.url);a.textContent=`[${index+1}] MỞ NGUỒN ↗`;foot.append(a);});
      } else if(['cancelled','error'].includes(message.status))foot.append(el('span','',message.status==='cancelled'?'CHƯA HOÀN TẤT · ĐÃ DỪNG':'CHƯA HOÀN TẤT · LỖI KẾT NỐI'));
    }
  });
  if(nearBottom)container.scrollTop=container.scrollHeight;
  const last=state.messages.at(-1);
  if(last?.status==='done'&&last.id!==announcedId){announcedId=last.id;$('#answer-announcement').textContent='Mambot: '+last.content.slice(0,300)+(last.content.length>300?'… Đọc phần hội thoại để xem đầy đủ.':'');}
  if(!last){announcedId=null;$('#answer-announcement').textContent='';}
  const nextSourcesKey=JSON.stringify([state.sources,busy,state.phase,last?.meta?.mode]);
  if(nextSourcesKey===sourcesKey)return;sourcesKey=nextSourcesKey;
  $('#source-count').textContent=`[${String(state.sources.length).padStart(2,'0')}]`;
  const sourceList=$('#source-list');sourceList.replaceChildren();
  if(!state.sources.length){
    const noMatch=last?.meta?.mode==='no-match',clarify=last?.meta?.mode==='clarification';
    const p=el('p','empty-sources',busy?'Đang chuẩn bị câu trả lời…':clarify?'Đang chờ bạn làm rõ.':noMatch?'Chưa tìm được nguồn phù hợp.':state.messages.length?'Cùng bạn tìm bước tiếp theo.':'Câu trả lời có điểm tựa.');
    p.append(el('span','',clarify?'Trả lời câu hỏi của Mambot để tra cứu đúng nội dung.':noMatch?'Hãy thử nêu rõ ngành học, chủ đề và năm bạn quan tâm.':state.messages.length?'Lượt này là trò chuyện hoặc hướng dẫn tham khảo, không phải thông báo của HUIT. Khi tra cứu, nguồn sẽ xuất hiện tại đây.':'Nguồn tham khảo sẽ xuất hiện khi Mambot tìm được tài liệu liên quan.'));sourceList.append(p);
  }
  state.sources.forEach((source,index)=>{const a=sourceAnchor(source.url);a.className='source-card';a.append(el('span','source-number',`[${String(index+1).padStart(2,'0')}] ${labels[source.category]||'TÀI LIỆU'} ↗`),el('strong','',source.title),el('small','',`${source.year!=null?'NĂM '+source.year+' · ':''}BẢN LƯU ${source.retrieved_at?.slice(0,10)||'KHÔNG RÕ NGÀY'}\nĐỘ KHỚP: ${Math.round(source.similarity*100)}% · KHÔNG PHẢI ĐỘ CHÍNH XÁC`));sourceList.append(a);});
});
function clearDraft(){$('#question').value='';$('#char-count').textContent='0 / 800';}
function send(question){
  const text=question.trim();if(!text)return;
  const before=chat.getState().messages.length;
  chat.send(text);
  if(chat.getState().messages.length>before){
    if($('#question').value.trim()===text)clearDraft();
    $('#question').focus();
  }
}
$('#chat-form').addEventListener('submit',event=>{event.preventDefault();send($('#question').value);});
$('#question').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!$('#question').readOnly)send($('#question').value);}});
$('#question').addEventListener('input',()=>$('#char-count').textContent=`${$('#question').value.length} / 800`);
document.querySelectorAll('[data-question]').forEach(button=>button.addEventListener('click',()=>send(button.dataset.question)));
$('#stop-chat').addEventListener('click',()=>chat.stop());
$('#retry-chat').addEventListener('click',()=>chat.retry());
function focusChat(){location.hash='chat';showPage('chat');$('#question').focus();}
function newChat(){if(chat.needsResetConfirmation($('#question').value)){$('#reset-dialog').returnValue='cancel';$('#reset-dialog').showModal();}else{clearDraft();focusChat();}}
$('#new-chat').addEventListener('click',newChat);$('#new-chat-mobile').addEventListener('click',newChat);
$('#reset-dialog').addEventListener('close',()=>{if($('#reset-dialog').returnValue==='confirm'){chat.reset();clearDraft();focusChat();}});
$('#remember-chat').addEventListener('change',()=>chat.setRemember($('#remember-chat').checked));
function download(content,type,extension){const blob=new Blob([content],{type});const url=URL.createObjectURL(blob);const a=el('a');a.href=url;a.download='mambot-hoi-thoai-'+new Date().toISOString().slice(0,10)+'.'+extension;a.hidden=true;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}
$('#export-chat').addEventListener('click',()=>download('\uFEFF'+chat.exportText(),'text/plain;charset=utf-8','txt'));
$('#export-json').addEventListener('click',()=>download(JSON.stringify(chat.exportConversation(),null,2),'application/json','json'));

library.subscribe(state=>{
  $('#library-count').textContent=state.loaded?`${state.visible.length} / ${state.items.length} BẢN GHI`:'KHO TRI THỨC';
  const status=$('#library-status');status.replaceChildren();
  if(state.loading)status.textContent='Đang tải kho tri thức…';
  else if(state.error){status.append(el('p','error',state.error));const retry=el('button','text-button','THỬ LẠI ↻');retry.addEventListener('click',()=>library.load());status.append(retry);}
  else if(state.loaded&&!state.visible.length)status.textContent='Không tìm thấy tài liệu. Thử từ khóa khác hoặc bỏ bộ lọc.';
  const fragment=document.createDocumentFragment();
  state.visible.forEach((item,index)=>{const row=el('article','library-row');row.append(el('span','row-index',String(index+1).padStart(2,'0')));const text=el('div');text.append(el('h3','',item.title.replace(/\s*\(HUIT.*\)$/, '')),el('p','',item.text.replace(/^\[[^\]]+\]\s*/, '').replace(/[#*]/g,'').slice(0,145)+'…'));row.append(text,el('span','row-meta',`${labels[item.category]||item.category.toUpperCase()}\n${item.year||'KHÔNG RÕ NĂM'} / BẢN LƯU`));const a=sourceAnchor(item.url);a.textContent='↗';a.setAttribute('aria-label','Mở nguồn '+item.title);row.append(a);const details=el('details');details.append(el('summary','','ĐỌC NỘI DUNG BẢN LƯU'),el('p','',item.text));row.append(details);fragment.append(row);});
  $('#library-items').replaceChildren(fragment);
});
const filterLibrary=()=>library.filter($('#library-search').value,$('#category').value);
$('#library-search').addEventListener('input',filterLibrary);$('#category').addEventListener('change',filterLibrary);
system.subscribe(state=>{
  $('#refresh-system').disabled=state.loading;
  if(state.loading){$('#system-status').textContent='Đang kiểm tra kho dữ liệu và authority…';return;}
  if(state.error){$('#top-status').textContent='KẾT NỐI GIÁN ĐOẠN';$('#system-status').textContent=state.error;return;}
  if(!state.data)return;
  const d=state.data;
  $('#top-status').textContent=d.status==='empty'?'KHO TRI THỨC CHƯA CÓ DỮ LIỆU':`${d.data_mode==='local'?'BẢN LƯU TẠI MÁY':'KHO DỮ LIỆU KẾT NỐI'} / ${d.records} TÀI LIỆU`;
  $('#system-status').textContent=`● ${d.records} tài liệu · ${d.data_mode==='local'?'Dữ liệu tại máy':'Kho dữ liệu máy chủ'} · Authority đã kiểm tra\n${d.generation_configured?'Đã cấu hình AI hội thoại':'Hướng dẫn có sẵn + trích đoạn; chưa cấu hình AI hội thoại'} · ${d.dense_search?'Tìm kiếm ngữ nghĩa đã bật':'TF–IDF + cosine'} · Bản lưu từ ${d.snapshot_date||'ngày chưa xác định'}`;
});
$('#refresh-system').addEventListener('click',()=>system.reload());system.reload();
window.addEventListener('pagehide',event=>{
  chat.stop();
  if(!event.persisted){chat.dispose();library.dispose();system.dispose();}
});
window.addEventListener('pageshow',event=>{if(event.persisted)system.reload();});

// Planner presentation is entirely local; only the pure controller allocates time.
const today=new Date();
$('#plan-date').value=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
let plannerUrl=null,plannerRevision=0;
function clearPlanner(){
  plannerRevision++;if(plannerUrl)URL.revokeObjectURL(plannerUrl);plannerUrl=null;
  $('#planner-download').removeAttribute('href');$('#planner-download').hidden=true;$('#planner-result').hidden=true;
  $('#planner-status').textContent='';
}
$('#planner-form').addEventListener('input',clearPlanner);
$('#open-planner').addEventListener('click',event=>{event.preventDefault();$('#study-planner').open=true;$('#plan-subjects').focus();});
function paintSchedule(plan){
  const canvas=$('#planner-canvas');canvas.width=1200;canvas.height=1640;
  const ctx=canvas.getContext('2d');if(!ctx)throw new Error('Trình duyệt chưa hỗ trợ ảnh lịch. Bạn vẫn có thể đọc lịch dạng chữ.');
  ctx.fillStyle='#eef5fc';ctx.fillRect(0,0,1200,1640);ctx.fillStyle='#0b5598';ctx.fillRect(0,0,1200,175);
  ctx.fillStyle='white';ctx.font='bold 48px Arial';ctx.fillText('MAMBOT / LỊCH TỰ HỌC',48,74);
  ctx.font='25px Arial';ctx.fillText(`${plan.days[0].date} → ${plan.days[6].date} · ${plan.minutes} phút/ngày, gồm nghỉ`,48,123);
  const names=['CHỦ NHẬT','THỨ HAI','THỨ BA','THỨ TƯ','THỨ NĂM','THỨ SÁU','THỨ BẢY'];
  plan.days.forEach((day,i)=>{
    const x=40+(i%2)*580,y=205+Math.floor(i/2)*330;
    ctx.fillStyle='white';ctx.fillRect(x,y,560,306);ctx.fillStyle='#0b5598';ctx.font='bold 25px Arial';ctx.fillText(`${names[day.weekday]} · ${day.date.slice(8)}/${day.date.slice(5,7)}`,x+18,y+35);
    ctx.font='21px Arial';
    if(!day.slots.length){ctx.fillStyle='#36556f';ctx.fillText('Ngày nghỉ / sinh hoạt cá nhân',x+18,y+80);return;}
    // Six study slots maximum; paired breaks keep all text legible without truncation.
    let row=0;
    day.slots.forEach((slot,j)=>{
      if(slot.kind!=='study')return;
      ctx.fillStyle='#183449';ctx.font='20px Arial';
      const label=`${slot.start}–${slot.end}  ${slot.label}`;
      ctx.fillText(label,x+18,y+72+row*36,524);
      const rest=day.slots[j+1];if(rest?.kind==='break'){
        ctx.fillStyle='#5b7185';ctx.font='15px Arial';ctx.fillText(`Nghỉ ${rest.start}–${rest.end}`,x+18,y+88+row*36);
      }row++;
    });
  });
  ctx.fillStyle='#244966';ctx.font='24px Arial';ctx.fillText('Học vừa sức. Tự làm trước, xem lại lỗi sau.',48,1580);
  ctx.font='20px Arial';ctx.fillText('Lịch cá nhân gợi ý • Không thay thế thời khóa biểu HUIT • Điều chỉnh khi bận hoặc mệt.',48,1616);
  return canvas;
}
$('#planner-form').addEventListener('submit',event=>{
  event.preventDefault();clearPlanner();const revision=plannerRevision;
  try{
    const plan=buildStudySchedule({subjects:$('#plan-subjects').value,startDate:$('#plan-date').value,startTime:$('#plan-start').value,endTime:$('#plan-end').value,minutes:$('#plan-minutes').value,weekdays:[...document.querySelectorAll('[name="weekday"]:checked')].map(x=>Number(x.value))});
    const days=$('#planner-days');days.replaceChildren();
    for(const day of plan.days){const section=el('section');section.append(el('h3','',`${['CN','Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7'][day.weekday]} · ${day.date}`));
      const list=el('ul');for(const slot of day.slots)list.append(el('li',slot.kind,`${slot.start}–${slot.end} · ${slot.label}`));
      section.append(day.slots.length?list:el('p','','Ngày nghỉ / sinh hoạt cá nhân'));days.append(section);
    }
    $('#planner-result').hidden=false;
    $('#planner-status').textContent=plan.unassigned.length?`Chưa đủ phiên cho: ${plan.unassigned.join(', ')}. Hãy tăng ngày học hoặc giảm số môn.`:'Đã tạo lịch 7 ngày. Bạn có thể đọc bên dưới và tải ảnh PNG.';
    paintSchedule(plan).toBlob(blob=>{
      if(revision!==plannerRevision)return;
      if(!blob){$('#planner-status').textContent+=' Chưa xuất được ảnh; hãy thử lại.';return;}
      plannerUrl=URL.createObjectURL(blob);$('#planner-download').href=plannerUrl;$('#planner-download').download=`Mambot-lich-hoc-${plan.days[0].date}.png`;$('#planner-download').hidden=false;
    },'image/png');
  }catch(error){$('#planner-status').textContent=error.message;}
});
window.addEventListener('pagehide',event=>{if(!event.persisted)clearPlanner();});
