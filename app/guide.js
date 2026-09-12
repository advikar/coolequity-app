const articles=[...document.querySelectorAll('article')];
const search=document.getElementById('search');let category='all';
function filter(){const q=search.value.trim().toLowerCase();let n=0;articles.forEach(a=>{a.hidden=!((category==='all'||a.dataset.tag===category)&&q.split(/\s+/).every(term=>a.textContent.toLowerCase().split(/[^a-z0-9/]+/).some(word=>word.startsWith(term))));if(!a.hidden)n++;});document.getElementById('count').textContent=`${n} of ${articles.length} topics`;document.getElementById('empty').hidden=n>0;syncExpand();}
search.addEventListener('input',filter);
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{category=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',x===b));filter();});
document.getElementById('expand').onclick=()=>{const visible=articles.filter(a=>!a.hidden);const open=visible.some(a=>!a.querySelector('details').open);visible.forEach(a=>a.querySelector('details').open=open);document.getElementById('expand').textContent=open?'Collapse visible topics':'Expand visible topics';};
function openHash(){const a=articles.find(a=>'#'+a.id===location.hash);if(!a)return;category='all';search.value='';document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.filter==='all'));filter();a.querySelector('details').open=true;requestAnimationFrame(()=>{a.scrollIntoView({block:'start'});a.querySelector('summary').focus({preventScroll:true});});}
addEventListener('hashchange',openHash);filter();openHash();

function syncExpand(){const visible=articles.filter(a=>!a.hidden);const b=document.getElementById('expand');b.disabled=!visible.length;b.textContent=visible.some(a=>!a.querySelector('details').open)?'Expand visible topics':'Collapse visible topics';}
articles.forEach(a=>a.querySelector('details').addEventListener('toggle',syncExpand));
