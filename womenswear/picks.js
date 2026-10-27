/* One selection ledger for the original gallery and public-platform catalog. */
(() => {
 'use strict';
 if(window.WomenswearPicks)return;
 const keys={picks:'womenswear-selection-v4',revision:'womenswear-selection-revision-v4',token:'womenswear-selection-device-v4'};
 const legacyKeys={picks:'womenswear-edit-2026-10-favorites',revision:'womenswear-sync-revision-v3',token:'womenswear-sync-device-v3'};
 const endpoint='https://avcaleb-womenswear-picks.jammybead24.chatgpt.site/api/picks';
 const valid=id=>typeof id==='string'&&/^\d{2,3}$/.test(id);
 const normalize=value=>new Set(Array.isArray(value)?value.filter(valid):[]);
 const listeners=new Set(),operations=new Map();
 let picks=new Set(),revision=0,baseRevision=0,token='',pending=false,remoteChecked=false,timer,sending=null,hasLedger=false,legacyToken='',legacyRevision=0;
 let syncStatus={state:'loading',label:'读取备选'};
 try{hasLedger=localStorage.getItem(keys.picks)!==null;legacyToken=localStorage.getItem(legacyKeys.token)||'';legacyRevision=Number(localStorage.getItem(legacyKeys.revision)||0)||0;picks=normalize(JSON.parse(localStorage.getItem(hasLedger?keys.picks:legacyKeys.picks)||'[]'));revision=hasLedger?Number(localStorage.getItem(keys.revision)||0)||0:legacyRevision;token=localStorage.getItem(keys.token)||'';}catch{}
 baseRevision=revision;
 function all(){return [...picks].sort();}
 function emit(){for(const fn of listeners){try{fn();}catch{}}}
 function status(state,label){syncStatus={state,label};emit();}
 function persist(){try{localStorage.setItem(keys.picks,JSON.stringify(all()));localStorage.setItem(keys.revision,String(revision));}catch{}}
 function readNewerLocal(){try{const rev=Number(localStorage.getItem(keys.revision)||0)||0;if(rev>revision){picks=normalize(JSON.parse(localStorage.getItem(keys.picks)||'[]'));revision=rev;emit();}}catch{}}
 function getToken(){if(!token){const bytes=crypto.getRandomValues(new Uint8Array(32));token=btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');try{localStorage.setItem(keys.token,token);}catch{}}return token;}
 async function request(method,body,credential){
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),9000);
  try{
   const headers={Authorization:'Bearer '+(credential||getToken())};if(body)headers['Content-Type']='application/json';
   const response=await fetch(endpoint,{method,headers,...(body?{body:JSON.stringify(body),keepalive:true}:{}),signal:controller.signal});
   if(!response.ok)throw new Error('保存未完成');return await response.json();
  }finally{clearTimeout(timeout);}
 }
 async function restore(){
  const remote=await request('GET');const remoteRevision=Number(remote.revision)||0,remotePicks=normalize(remote.picks);
  readNewerLocal();
  if(remoteRevision>baseRevision){
   picks=remotePicks;for(const [id,on] of operations)on?picks.add(id):picks.delete(id);
   revision=operations.size?Math.max(Date.now(),revision,remoteRevision+1):remoteRevision;persist();
  }
  remoteChecked=true;baseRevision=remoteRevision;
  pending=JSON.stringify(all())!==JSON.stringify([...remotePicks].sort());
  if(pending)revision=Math.max(Date.now(),revision,remoteRevision+1);
  persist();status(pending?'pending':'synced',pending?'待同步':'已同步');
 }
 function schedule(delay=400){clearTimeout(timer);timer=setTimeout(()=>push(),delay);}
 async function push(){
  if(sending)return sending;
  sending=(async()=>{
   try{
    if(!remoteChecked)await restore();
    if(picks.size>100){pending=true;status('pending','请减少备选至100款');return;}
    while(pending){
     status('sending','保存中');pending=false;const sentRevision=revision;
     const ack=await request('POST',{revision:sentRevision,picks:all(),version:location.hostname==='127.0.0.1'?'qa-platforms-v4':'aw-2026-v4'});
     if(!ack.saved){revision=Math.max(revision,Number(ack.revision)||0)+1;pending=true;persist();}
     else if(revision===sentRevision){operations.clear();baseRevision=sentRevision;}
    }
    status('synced','已同步');
   }catch{pending=true;status('pending','待同步');schedule(25000);}
  })().finally(()=>{sending=null;});
  return sending;
 }
 const ready=(async()=>{
  if(!hasLedger){
   // Import the old browser's choices, but use a new device credential. An
   // already-open v3 tab can therefore never overwrite the new full ledger.
   if(legacyToken){try{const old=await request('GET',null,legacyToken);if((Number(old.revision)||0)>legacyRevision)picks=normalize(old.picks);}catch{}}
   revision=Math.max(Date.now(),revision+1);baseRevision=0;remoteChecked=true;pending=picks.size>0;persist();status(pending?'pending':'idle',pending?'待同步':'自动保存');
  }
  else if(token){try{await restore();}catch{status('pending','待同步');schedule(25000);}}
  else {remoteChecked=true;pending=picks.size>0;if(pending){revision=Math.max(Date.now(),revision+1);persist();status('pending','待同步');}else status('idle','自动保存');}
  if(pending&&remoteChecked)schedule();
 })();
 async function change(ids,mode){
  await ready;readNewerLocal();const next=new Set(picks);
  for(const id of ids){if(!valid(id))throw new Error('款号无效');const on=mode==='add'||!next.has(id);on?next.add(id):next.delete(id);}
  if(next.size>100&&next.size>picks.size)throw new Error('最多保留100款，请先取消部分备选');
  for(const id of ids)operations.set(id,next.has(id));
  picks=next;revision=Math.max(Date.now(),revision+1);pending=true;persist();status('pending','待同步');schedule();return true;
 }
 window.WomenswearPicks=Object.freeze({ready,all,has:id=>picks.has(id),toggle:id=>change([id],'toggle'),addMany:ids=>change(ids,'add'),getStatus:()=>({...syncStatus}),subscribe:fn=>{listeners.add(fn);fn();return()=>listeners.delete(fn);},flush:async()=>{await ready;clearTimeout(timer);return push();}});
 window.addEventListener('storage',async event=>{
  if(event.key===keys.picks||event.key===keys.revision){readNewerLocal();return;}
  if(event.key!==legacyKeys.picks)return;
  await ready;readNewerLocal();
  try{
   const before=normalize(JSON.parse(event.oldValue||'[]')),after=normalize(JSON.parse(event.newValue||'[]')),next=new Set(picks);
   for(const id of before)if(Number(id)<100&&!after.has(id))next.delete(id);
   for(const id of after)if(Number(id)<100&&!before.has(id))next.add(id);
   if(JSON.stringify([...next].sort())===JSON.stringify(all()))return;
   picks=next;revision=Math.max(Date.now(),revision+1);pending=true;persist();status('pending','待同步');schedule();
  }catch{}
 });
 window.addEventListener('focus',()=>{readNewerLocal();if(pending)push();});
 window.addEventListener('online',()=>{if(pending)push();});
 window.addEventListener('pagehide',()=>{if(pending)push();});
})();
