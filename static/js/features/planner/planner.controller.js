// Pure local planning: times include breaks; no account or school timetable access.
export function buildStudySchedule(input) {
  if(!input||typeof input!=='object')throw new Error('Vui lòng nhập thông tin lịch học.');
  const subjects=[...new Set(String(input.subjects??'').split(/[,;\n]/).map(x=>x.trim()).filter(Boolean))];
  if(!subjects.length||subjects.length>6||subjects.some(x=>x.length>40))throw new Error('Nhập 1–6 môn, mỗi tên tối đa 40 ký tự, ngăn bằng dấu phẩy.');
  const date=String(input.startDate??'');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date))throw new Error('Chọn ngày bắt đầu hợp lệ.');
  const first=new Date(date+'T12:00:00Z');
  if(!Number.isFinite(first.getTime())||first.toISOString().slice(0,10)!==date||first.getUTCFullYear()<2000||first.getUTCFullYear()>2100)throw new Error('Ngày bắt đầu phải hợp lệ, trong năm 2000–2100.');
  const time=value=>{if(!/^\d{2}:\d{2}$/.test(String(value)))return NaN;const [h,m]=value.split(':').map(Number);return h<24&&m<60?h*60+m:NaN;};
  const start=time(input.startTime),end=time(input.endTime),budget=Number(input.minutes);
  if(!Number.isFinite(start)||!Number.isFinite(end)||start<360||end>1320||end<=start)throw new Error('Chọn khung giờ trong cùng ngày, từ 06:00 đến 22:00, kết thúc sau bắt đầu.');
  if(!Number.isInteger(budget)||budget<30||budget>180||budget>end-start)throw new Error('Chọn 30–180 phút/ngày, không vượt khung giờ rảnh; tổng đã gồm giờ nghỉ.');
  if(!Array.isArray(input.weekdays)||!input.weekdays.length||input.weekdays.length>6||new Set(input.weekdays).size!==input.weekdays.length||input.weekdays.some(x=>!Number.isInteger(x)||x<0||x>6))throw new Error('Chọn 1–6 ngày học mỗi tuần để có ít nhất một ngày nghỉ.');
  const format=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  let subjectIndex=0;
  const days=Array.from({length:7},(_,i)=>{
    const day=new Date(first);day.setUTCDate(first.getUTCDate()+i);
    const slots=[];let at=start,remaining=budget;
    if(input.weekdays.includes(day.getUTCDay()))while(remaining>0){
      const duration=Math.min(25,remaining),subject=subjects[subjectIndex++%subjects.length];
      slots.push({start:format(at),end:format(at+duration),kind:'study',label:subject});at+=duration;remaining-=duration;
      if(remaining>0){const rest=Math.min(5,remaining);slots.push({start:format(at),end:format(at+rest),kind:'break',label:'Nghỉ, đứng dậy hoặc uống nước'});at+=rest;remaining-=rest;}
    }
    return {date:day.toISOString().slice(0,10),weekday:day.getUTCDay(),slots};
  });
  return {subjects,days,minutes:budget,unassigned:subjects.filter(s=>!days.some(d=>d.slots.some(slot=>slot.kind==='study'&&slot.label===s)))};
}
