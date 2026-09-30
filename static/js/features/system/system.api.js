import {getJson} from '../../shared/http.js';
export async function readSystemStatus(signal){
  const result=await getJson(new URL('../../../../api/health',import.meta.url),signal);
  if(!result||!['ok','empty'].includes(result.status)||result.name!=='Mambot'||
    !['local','mongo'].includes(result.data_mode)||!Number.isInteger(result.records)||result.records<0||result.records>100||
    ['dense_search','generation_configured','latest_verified'].some(key=>typeof result[key]!=='boolean')||
    result.authority!=='verified'||typeof result.version!=='string'||
    !(result.snapshot_date===null||/^\d{4}-\d{2}-\d{2}$/.test(result.snapshot_date)))
    throw new Error('Trạng thái máy chủ không hợp lệ. Vui lòng kiểm tra lại.');
  return result;
}
