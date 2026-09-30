import {readSystemStatus} from './system.api.js';
export function createSystemController(api=readSystemStatus){
  let state={data:null,loading:false,error:null};let abort;let sequence=0;const listeners=new Set();
  const publish=patch=>{state={...state,...patch};listeners.forEach(fn=>fn(structuredClone(state)));};
  return {subscribe(fn){listeners.add(fn);fn(structuredClone(state));return()=>listeners.delete(fn);},
    async reload(){abort?.abort();abort=new AbortController();const id=++sequence;publish({loading:true,error:null});try{const data=await api(abort.signal);if(id===sequence)publish({data,loading:false});}catch(error){if(id===sequence&&error.name!=='AbortError')publish({error:error.message,loading:false});}},
    dispose(){++sequence;abort?.abort();listeners.clear();}};
}
