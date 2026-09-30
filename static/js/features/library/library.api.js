import {getJson} from '../../shared/http.js';
export async function readLibrary(signal){
  const result=await getJson(new URL('../../../../api/library',import.meta.url),signal);
  if(!result||!Array.isArray(result.items)||result.items.length>100||result.items.some(item=>!item||!['title','text','url','category','retrieved_at'].every(key=>typeof item[key]==='string')))
    throw new Error('Kho tri thức trả dữ liệu sai cấu trúc.');
  return result;
}
