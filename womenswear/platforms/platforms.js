/* Public metrics and shared private selections have separate storage. */
const assetBase=new URL('.',document.currentScript.src);
const el=id=>document.getElementById(id),picks=window.WomenswearPicks;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const countNumber=n=>n>=10000?(n/10000).toLocaleString('zh-CN',{maximumFractionDigits:2})+'万':n.toLocaleString('zh-CN');
const money=r=>typeof r.price==='number'?(r.currency==='AUD'?'A$':'$')+r.price.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}):r.priceStatus?'价格待复核':'—';
const metricType=r=>r.recentBadgeOriginal?'recent':r.platform==='tiktok'?'cumulative':r.rank?'rank':'reference';
const metricValue=r=>metricType(r)==='recent'?r.recentBucket:r.soldNumericForChart||0;
const metricDisplay=r=>metricType(r)==='recent'?countNumber(r.recentBucket)+(r.recentBadgeOriginal.includes('+')?'+':''):metricType(r)==='cumulative'?countNumber(r.soldNumericForChart):r.rank?'#'+r.rank:'原图库';
const metricLabel=r=>metricType(r)==='recent'?'近月购买徽标':metricType(r)==='cumulative'?'累计已售':r.rank?r.categoryLabel+'当前名次':r.seasonLabel||'原图库';
const state={data:null,index:{},platform:'amazon',amazonView:'recent',savedOnly:new URLSearchParams(location.search).get('saved')==='1',view:'bars',visible:[]};
let lastSelection='',toastTimer;

function notify(message){el('toast').textContent=message;el('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el('toast').hidden=true,2800);}
function pickButton(r,bar=false){const chosen=picks.has(r.selectionId);return '<button type="button" class="pick-button'+(bar?' bar-pick':'')+'" data-pick="'+esc(r.selectionId)+'" aria-pressed="'+chosen+'" aria-label="'+(chosen?'取消':'记下')+esc(r.name)+'">'+(chosen?'♥':'♡')+'</button>';}
function currentRows(){
 if(state.savedOnly)return picks.all().map(id=>state.index[id]||{selectionId:id,id,platform:'legacy',name:'历史选款 · '+id,brand:'历史选款',categoryLabel:'原图库',currency:'',metric:'reference'});
 return state.data.rows.filter(r=>state.platform==='tiktok'?r.platform==='tiktok':r.platform==='amazon'&&r.category===state.amazonView);
}
function updateSelectionStatus(){
 const s=picks.getStatus();el('sync-button').textContent=s.label;el('sync-button').dataset.state=s.state;el('sync-button').disabled=['loading','sending'].includes(s.state);el('sync-button').setAttribute('aria-label','备选'+s.label);
 el('saved-count').textContent=picks.all().length;el('show-saved').classList.toggle('active',state.savedOnly);el('show-saved').setAttribute('aria-pressed',String(state.savedOnly));
}
function render(){
 updateSelectionStatus();if(!state.data)return;
 const tt=state.platform==='tiktok',recent=state.platform==='amazon'&&state.amazonView==='recent',quantity=tt||recent;
 const all=currentRows(),q=el('search').value.trim().toLowerCase(),threshold=tt?1000:500;
 let rows=all.filter(r=>(state.savedOnly||!el('winter-only').checked||r.eligibleAutumnWinter)&&(state.savedOnly||!quantity||!el('threshold').checked||metricValue(r)>=threshold)&&(!q||[r.title,r.name,r.brand,r.id,r.selectionId].join(' ').toLowerCase().includes(q)));
 if(!state.savedOnly)rows.sort((a,b)=>quantity?metricValue(b)-metricValue(a):a.rank-b.rank);
 state.visible=rows;
 el('page-title').textContent=state.savedOnly?'备选':'选款';
 el('metric').textContent=state.savedOnly?'原图库 / Amazon / TikTok':recent?'近月购买徽标 · 非自然月销量':tt?'商品累计已售 · 含退货 · 平台约数':'官方当前品类名次 · 非销量数量';
 el('market').textContent=state.savedOnly?'我的备选':tt?'TikTok Shop US / USD':'Amazon US / USD / 配送 10001';
 el('amazon-view').hidden=state.savedOnly||tt;el('winter-wrap').hidden=state.savedOnly;el('threshold-wrap').hidden=state.savedOnly||!quantity;
 el('threshold-label').textContent=tt?'累计 ≥ 1千':'近月徽标 ≥ 500';
 el('view-toggle').hidden=state.savedOnly||!quantity;el('view-toggle').textContent=state.view==='bars'?'切换图库':'切换图表';
 el('export-picks').hidden=!state.savedOnly;el('all-csv').hidden=state.savedOnly;
 el('count').textContent=rows.length+' / '+all.length+(state.savedOnly?' 款':' 条');
 el('source-link').hidden=state.savedOnly;el('source-link').href=all[0]?.sourcePage||'https://shop.tiktok.com/us';
 el('footer-context').textContent=state.savedOnly?'备选自动保存':tt?'商品累计已售 · 按商品链接计':'美国站 / 美元 / New York 10001';
 const bars=!state.savedOnly&&quantity&&state.view==='bars';el('results').className=bars?'bars':'grid';el('chart-head').hidden=!bars;
 el('chart-metric').textContent=tt?'TikTok · 累计已售 · 含退货':'Amazon · 近月购买徽标';
 const max=Math.max(1,...all.map(metricValue));
 const groupMax=kind=>Math.max(1,...rows.filter(r=>metricType(r)===kind).map(metricValue));
 const recentMax=groupMax('recent'),cumulativeMax=groupMax('cumulative');
 el('empty').hidden=rows.length!==0;el('empty').textContent=state.savedOnly?'暂无备选':'没有匹配记录';
 el('results').innerHTML=rows.map(r=>{
  const image=r.image?'<img '+(bars?'class="thumb" ':'')+'src="'+esc(r.image)+'" alt="'+esc(r.name)+'" loading="lazy" decoding="async" referrerpolicy="no-referrer">':'<span class="no-photo">'+esc(r.id)+'</span>';
  const url=r.url?.startsWith('https://')?r.url:'#';
  const title=(r.title||r.name)+' / 商品号：'+r.id+(r.recentBadgeOriginal?' / '+r.recentBadgeOriginal:r.soldOriginal?' / '+r.soldOriginal:r.rank?' / 原榜 #'+r.rank:'');
  const kind=metricType(r),width=metricValue(r)/max*100,localMax=kind==='recent'?recentMax:cumulativeMax;
  if(bars)return '<article class="bar-row"><a class="thumb-link" href="'+esc(url)+'" target="_blank" rel="noopener noreferrer" title="'+esc(title)+'">'+image+'</a><a class="bar-name" href="'+esc(url)+'" target="_blank" rel="noopener noreferrer" title="'+esc(title)+'"><span class="brand-line">'+esc(r.brand||'商品原页')+'</span><b>'+esc(r.name)+'</b><small>'+money(r)+' '+esc(r.currency||'')+' ↗</small></a><div class="track" role="img" aria-label="'+esc(r.recentBadgeOriginal||r.soldOriginal||'')+'"><div class="fill" style="width:'+width+'%"></div></div><div class="amount">'+pickButton(r,true)+'<span>'+metricDisplay(r)+'</span><small>'+metricLabel(r)+'</small></div></article>';
  const quantitative=kind==='recent'||kind==='cumulative';
  return '<article class="card"><div class="photo"><a class="photo-link" href="'+esc(url)+'" target="_blank" rel="noopener noreferrer" title="'+esc(title)+'">'+image+'</a><span class="rank">'+(state.savedOnly?esc(r.platform==='amazon'?'Amazon':r.platform==='tiktok'?'TikTok':'原图库'):r.category==='recent'?metricDisplay(r)+' 近月购买':r.platform==='tiktok'?metricDisplay(r)+' 已售':esc(r.categoryLabel)+' #'+String(r.rank).padStart(2,'0'))+'</span>'+pickButton(r)+'</div><span class="brand-line">'+esc(r.brand||'商品原页')+'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer" aria-label="'+esc(r.name)+'商品原页">↗</a></span><h2>'+esc(r.name)+'</h2><div class="price">'+money(r)+' <small>'+esc(r.currency||'')+'</small></div>'+(quantitative?'<div class="sold-mini"><span>'+metricLabel(r)+'</span><span class="mini-track"><i style="width:'+(metricValue(r)/localMax*100)+'%"></i></span><span>'+metricDisplay(r)+'</span></div>':r.rank?'<div class="metric-missing">近月购买量未公开</div>':'')+'</article>';
 }).join('');
 document.querySelectorAll('#tabs button').forEach(b=>{const active=b.dataset.platform===state.platform&&!state.savedOnly;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
}
function exportSelection(){
 const fields=['selectionId','name','platform','id','price','currency','recentBadgeOriginal','soldOriginal','rank','observedDate','url'];
 const csv='\ufeff'+[fields,...state.visible.map(r=>fields.map(k=>r[k]??''))].map(row=>row.map(value=>'"'+String(value).replace(/"/g,'""')+'"').join(',')).join('\n');
 const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='womenswear-picks.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
}
async function init(){
 const responses=await Promise.all(['data.json','selection-index.json'].map(name=>fetch(new URL(name,assetBase),{cache:'no-cache'})));if(responses.some(r=>!r.ok))throw new Error('data unavailable');
 [state.data,state.index]=await Promise.all(responses.map(r=>r.json()));
 if(state.data.schemaVersion!==2||state.data.rows.some(r=>!state.index[r.selectionId]))throw new Error('incomplete catalog update');
 el('tabs').innerHTML='<button type="button" data-platform="amazon">Amazon US<small>近月购买 / 当前榜</small></button><button type="button" data-platform="tiktok">TikTok US<small>累计已售</small></button>';
 el('tabs').addEventListener('click',e=>{const b=e.target.closest('[data-platform]');if(!b)return;state.platform=b.dataset.platform;state.savedOnly=false;render();});
 el('amazon-view').addEventListener('change',()=>{state.amazonView=el('amazon-view').value;render();});
 ['winter-only','threshold'].forEach(id=>el(id).addEventListener('change',render));el('search').addEventListener('input',render);
 el('view-toggle').addEventListener('click',()=>{state.view=state.view==='bars'?'grid':'bars';render();});
 el('show-saved').addEventListener('click',()=>{state.savedOnly=!state.savedOnly;el('search').value='';render();});
 el('sync-button').addEventListener('click',()=>picks.flush());
 el('export-picks').addEventListener('click',exportSelection);
 el('results').addEventListener('click',e=>{const b=e.target.closest('[data-pick]');if(b)picks.toggle(b.dataset.pick).catch(error=>notify(error.message));});
 picks.subscribe(()=>{updateSelectionStatus();const signature=picks.all().join(',');if(signature!==lastSelection){lastSelection=signature;render();}});
 const imported=(new URLSearchParams(location.search).get('pick')||'').split(',').filter(id=>state.index[id]);
 if(imported.length){await picks.addMany(imported);state.savedOnly=true;}render();
}
init().catch(()=>{el('results').className='error';el('results').textContent='数据加载失败，请刷新或查看平台原页。';});
