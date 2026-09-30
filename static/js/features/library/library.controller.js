import {readLibrary} from './library.api.js';
const normalize=value=>value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').trim().replace(/\s+/g,' ');
export function createLibraryController(api=readLibrary){
  let state={items:[],loading:false,error:null,query:'',category:'all',loaded:false};let sequence=0;let abort;const listeners=new Set();
  const snapshot=()=>{
    const terms=normalize(state.query).split(' ').filter(Boolean);
    return structuredClone({...state,visible:state.items.filter(item=>{
      if(state.category!=='all'&&item.category!==state.category)return false;
      const searchable=normalize(item.title+' '+item.text);
      return terms.every(term=>searchable.includes(term));
    })});
  };
  const publish=patch=>{state={...state,...patch};listeners.forEach(fn=>fn(snapshot()));};
  return {subscribe(fn){listeners.add(fn);fn(snapshot());return()=>listeners.delete(fn);},
    filter(query,category){publish({query,category});},
    async load(){abort?.abort();abort=new AbortController();const id=++sequence;publish({loading:true,error:null});try{const result=await api(abort.signal);if(id===sequence)publish({items:result.items,loading:false,loaded:true});}catch(error){if(id===sequence&&error.name!=='AbortError')publish({error:error.message,loading:false});}},
    dispose(){++sequence;abort?.abort();listeners.clear();}};
}
