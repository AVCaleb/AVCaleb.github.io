/* Only source-observed ranks and cumulative listing counters are rendered. */
const el=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=r=>typeof r.price==='number'?'$'+r.price.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}):r.priceStatus?'价格待复核':'原页价格 ↗';
const amount=r=>r.soldNumericForChart>=10000?(r.soldNumericForChart/10000).toLocaleString('zh-CN',{maximumFractionDigits:2})+'万':r.soldNumericForChart.toLocaleString('zh-CN');
const state={data:null,tab:null,view:'bars'};
const categories=[{id:'coats',name:'Amazon · 外套'},{id:'sweaters',name:'Amazon · 毛衣'},{id:'hoodies',name:'Amazon · 卫衣'},{id:'tiktok',name:'TikTok · 已售'}];
function allForTab(){return state.data.rows.filter(r=>state.tab==='tiktok'?r.platform==='tiktok':r.platform==='amazon'&&r.category===state.tab);}
function render(){
 const tt=state.tab==='tiktok',all=allForTab(),q=el('search').value.trim().toLowerCase();
 let rows=all.filter(r=>(!el('winter-only').checked||r.eligibleAutumnWinter)&&(!tt||!el('threshold').checked||r.soldNumericForChart>=1000)&&(!q||(r.title+' '+r.name+' '+r.brand+' '+r.id).toLowerCase().includes(q)));
 rows.sort((a,b)=>tt?b.soldNumericForChart-a.soldNumericForChart:a.rank-b.rank);
 el('metric').textContent=tt?'商品累计已售 · 含退货 · 平台约数':'官方当前品类名次 · 非年度销量榜';
 el('market').textContent=tt?'TikTok Shop US / USD':'Amazon US / USD / 配送 10001';
 el('threshold-wrap').hidden=!tt;el('view-toggle').hidden=!tt;
 el('view-toggle').textContent=state.view==='bars'?'切换图库':'切换图表';
 el('count').textContent=rows.length+' / '+all.length+' 条';
 el('source-link').href=all[0]?.sourcePage||'https://shop.tiktok.com/us';
 el('footer-context').textContent=tt?'商品累计已售 · 按商品链接计':'美国站 / 美元 / New York 10001';
 const bars=tt&&state.view==='bars';el('results').className=bars?'bars':'grid';el('chart-head').hidden=!bars;
 const max=Math.max(1,...all.map(r=>r.soldNumericForChart||0));
 el('empty').hidden=rows.length!==0;
 el('results').innerHTML=rows.map(r=>{
  const image='<img '+(bars?'class="thumb" ':'')+'src="'+esc(r.image)+'" alt="'+esc(r.name)+'" loading="lazy" decoding="async" referrerpolicy="no-referrer">';
  const title='原始标题：'+r.title+' / 商品号：'+r.id+(tt?' / '+r.soldOriginal:' / 原榜 #'+r.rank);
  const width=(r.soldNumericForChart||0)/max*100;
  if(bars)return '<a class="bar-row" href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer" title="'+esc(title)+'">'+image+'<div class="bar-name"><span class="brand-line">'+esc(r.brand)+'</span><b>'+esc(r.name)+'</b><small>'+money(r)+' · USD ↗</small></div><div class="track"><div class="fill" style="width:'+width+'%"></div></div><div class="amount">'+amount(r)+'<small>累计已售</small></div></a>';
  return '<article class="card"><a class="photo" href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer" title="'+esc(title)+'">'+image+'<span class="rank">'+(tt?amount(r)+' 已售':esc(r.categoryLabel)+' #'+String(r.rank).padStart(2,'0'))+'</span></a><span class="brand-line">'+esc(r.brand)+'<a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer" aria-label="'+esc(r.name)+'商品原页">↗</a></span><h2>'+esc(r.name)+'</h2><div class="price">'+money(r)+' <small>USD</small></div>'+(tt?'<div class="sold-mini"><span>累计已售</span><span class="mini-track"><i style="width:'+width+'%"></i></span><span>'+amount(r)+'</span></div>':'')+'</article>';
 }).join('');
 document.querySelectorAll('#tabs button').forEach(b=>{const active=b.dataset.tab===state.tab;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
}
async function init(){
 const response=await fetch('data.json',{cache:'no-cache'});if(!response.ok)throw new Error('data unavailable');state.data=await response.json();
 const available=categories.filter(c=>state.data.rows.some(r=>c.id==='tiktok'?r.platform==='tiktok':r.platform==='amazon'&&r.category===c.id));
 state.tab=available[0].id;
 el('tabs').innerHTML=available.map(c=>{const n=state.data.rows.filter(r=>c.id==='tiktok'?r.platform==='tiktok':r.platform==='amazon'&&r.category===c.id).length;return '<button type="button" data-tab="'+c.id+'">'+c.name+'<small>'+n+' 条</small></button>';}).join('');
 el('tabs').addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;state.tab=b.dataset.tab;render();});
 ['winter-only','threshold'].forEach(id=>el(id).addEventListener('change',render));el('search').addEventListener('input',render);
 el('view-toggle').addEventListener('click',()=>{state.view=state.view==='bars'?'grid':'bars';render();});render();
}
init().catch(()=>{el('results').className='error';el('results').textContent='数据加载失败，请刷新或查看平台原页。';});
