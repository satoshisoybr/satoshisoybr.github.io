 'use strict';
let report,port='Paranaguá';
const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const fmt=(v,n=2)=>v===null||v===undefined?'N/D':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:n,maximumFractionDigits:n});
const date=v=>v?new Date(v+'T12:00:00Z').toLocaleDateString('pt-BR'):'N/D';
const safe=url=>{try{const u=new URL(url);return u.protocol==='https:'?u.href:'#';}catch{return '#';}};
const signed=(v,n=4)=>v==null?'N/D':(Number(v)>0?'+':'')+fmt(v,n);
const dual=(a,b,sign=false)=>esc(fmt(a))+'<small>('+esc(sign?signed(b):fmt(b,4))+' US$/bu)</small>';
const bitcoinCell=(sats,ref)=>fmt(sats)+'<small>('+fmt(sats==null?null:Number(sats)/1e8,10)+' BTC/sc)</small>'+(ref?'<small>'+esc(ref.source)+' · '+date(ref.date)+'</small>':'');
function age(d){return Math.floor((new Date(report.edition+'T12:00:00Z')-new Date(d+'T12:00:00Z'))/86400000);}
function render(){
 $('bitcoin-status').textContent=report.bitcoin.status;
 $('edition').textContent=date(report.edition);
 $('cutoff').textContent='Dados consolidados em '+(report.cutoff?new Date(report.cutoff).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'}):'data não informada')+' · Brasília';
 const old=Object.entries(report.latest).filter(([,r])=>r&&age(r.date)>3).map(([p,r])=>p+': última referência '+date(r.date)+' ('+age(r.date)+' dias de defasagem).');
 $('availability').textContent=[...old,...report.warnings.slice(0,3),report.automation.active?'Publicação gerada por uma execução do GitHub Actions.':'Checkpoint preservado; confira as datas efetivas das fontes.'].join(' ');
 $('quotes').innerHTML=Object.entries(report.latest).map(([name,r])=>{
  if(!r)return `<article class="quote"><h2>${esc(name)}</h2><p>Referência física não disponível.</p></article>`;
  const previous=[...report.rows[name]].reverse().find(x=>x.date<r.date&&x.physical!=null);
  return `<article class="quote"><div class="quote-top"><h2>${esc(name)}</h2><span class="tag ${age(r.date)>3?'stale':''}">${date(r.date)}${age(r.date)>3?' · defasado':''}</span></div><div class="price">R$ ${fmt(r.physical)} <small>/ saca de 60 kg</small></div><p><b>${fmt(r.bitcoin?.physical)} sats/sc</b> · ${fmt(r.physical_usd,4)} US$/bu</p><p>${name==='Santos'?'Índice FOB convertido pela PTAX da mesma data':'Físico CEPEA/ESALQ · referência de Paranaguá'}</p><div class="decomp"><div><span>Chicago</span><b>R$ ${fmt(r.chicago_brl)}</b><small>${fmt(r.cbot,4)} US$/bu</small></div><div><span>Prêmio</span><b>R$ ${fmt(r.premium_brl)}</b><small>${signed(r.premium)} US$/bu</small></div><div><span>SOMA indicativa</span><b>R$ ${fmt(r.sum)}</b></div></div><p>Chicago R$ ${fmt(r.chicago_brl)}/sc + prêmio R$ ${fmt(r.premium_brl)}/sc = R$ ${fmt(r.sum)}/sc; dólar utilizado R$ ${fmt(r.fx,4)}/US$.</p><p>PTAX R$ ${fmt(r.fx,4)}/US$ · ${esc(r.contract||'Contrato N/D')} · Residual R$ ${fmt(r.residual)}/sc</p><p class="secondary">Últimas duas datas físicas: <b>${date(r.date)}</b> · ${previous?date(previous.date)+' (R$ '+fmt(previous.physical)+'/sc)':'anterior N/D'}. BTC: ${esc(r.bitcoin?.reference?.source||'N/D')}.</p></article>`;
 }).join('');
 renderPort();renderBitcoin();renderFreight();renderBattle();
 $('futures').innerHTML=report.futures.map(r=>`<tr><td><b>${esc(r.ticker)}</b><small>${date(r.date)} · ${esc(r.reference_month||'vencimento N/D')}</small></td><td>${fmt(r.settlement,4)}<small>${esc(r.unit||'')}</small></td><td>${fmt(r.brl_sc)}<small>PTAX ${fmt(r.fx,4)}</small></td><td class="btc-cell">${bitcoinCell(r.bitcoin?.reference_sc,r.bitcoin?.reference)}</td><td>${fmt(r.pct)}%</td><td>${fmt(r.flow_usd,3)}</td><td>${fmt(r.flow_brl_estimate)}</td><td>${fmt(r.volume,0)}<small>${fmt(r.number_of_trades,0)} negócios</small></td><td>${fmt(r.bid,4)} / ${fmt(r.ask,4)}<small>captura datada; não é livro ao vivo</small></td></tr>`).join('');
 $('options').innerHTML=report.options.length?report.options.slice(0,2).map((r,i)=>`<tr><td>${i===0?'Próxima do futuro':'Aproximadamente R$ 5 abaixo'}<small>${esc(r.ticker)} · cadastro ${date(r.verified_date)}</small></td><td>${fmt(r.strike)} US$/sc${r.expired?'<small>Expirada</small>':''}</td><td class="btc-cell">${bitcoinCell(r.bitcoin?.strike,r.bitcoin?.reference)}</td><td>Não disponível<small>requer cotação</small></td><td>Não disponível<small>requer cotação</small></td><td>${date(r.expiration)}<small>${r.days} dias</small></td></tr>`).join(''):'<tr><td colspan="6">Duas puts: instrumentos e preços não disponíveis — requer cotação.</td></tr>';
 $('five').innerHTML=report.five.length?report.five.map(r=>`<tr><td>${esc(r.label)}</td><td>${date(r.from)} a ${date(r.to)}</td><td>${fmt(r.delta)}</td><td>${fmt(r.pct)}%</td><td class="btc-cell">${fmt(r.bitcoin?.delta)}<small>${fmt(r.bitcoin?.pct)}% em sats</small></td></tr>`).join(''):'<tr><td colspan="5">Não disponível: faltam seis fechamentos homogêneos.</td></tr>';
 const sources=[];for(const [name,rs] of Object.entries(report.rows)){for(const [key,label] of [['fx','PTAX / BCB'],['cbot','Chicago / CME via Notícias Agrícolas'],['premium',name+' / prêmio'],[name==='Santos'?'physical_usd_raw':'physical_brl_raw',name+' / físico']]){const r=[...rs].reverse().find(r=>r[key]!=null);if(!r)continue;const src=r.sources?.[key];const id=label==='PTAX / BCB'||label.startsWith('Chicago')?label:label+name;if(sources.some(s=>s.id===id))continue;sources.push({id,label,date:r.date,url:src?.url});}}
 $('sources').innerHTML=sources.map(s=>`<li><a href="${esc(safe(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.label)}</a><span>Referência ${date(s.date)}${age(s.date)>3?' · defasada':''}</span></li>`).join('');
 $('news').innerHTML=report.news.map(n=>`<p><b>${date(n.date)}</b> · <a href="${esc(safe(n.url))}" target="_blank" rel="noopener noreferrer">${esc(n.summary)}</a></p>`).join('')+'<p class="secondary">Notícias preservadas com a data original; o coletor não faz pesquisa editorial automática.</p>';
}
function renderPort(){
 document.querySelectorAll('[data-port]').forEach(b=>{b.classList.toggle('active',b.dataset.port===port);b.setAttribute('aria-pressed',String(b.dataset.port===port));});
 const rs=report.rows[port];
 $('window').textContent=date(report.window_start)+' a '+date(report.window_end)+' · 30 dias corridos';
 $('caption').textContent='Soja — Paranaguá | composição completa + Bitcoin';$('chart-title').textContent=port+' · Físico observado em R$/saca';
 const tableRows=rows=>[...rows].reverse().map(r=>`<tr><td>${date(r.date)}<small>${esc(r.contract||'')}</small></td><td>${fmt(r.fx,4)}</td><td>${dual(r.chicago_brl,r.cbot)}</td><td>${dual(r.premium_brl,r.premium,true)}<small>${esc(r.premium_condition||'condição N/D')}</small></td><td>${fmt(r.sum)}</td><td>${dual(r.physical,r.physical_usd)}</td><td>${fmt(r.residual)}</td><td class="btc-cell" title="${esc(r.bitcoin?.reference?.observed_at||'Referência BTC não disponível')}">${bitcoinCell(r.bitcoin?.physical,r.bitcoin?.reference)}</td></tr>`).join('');
 $('history').innerHTML=tableRows(report.rows['Paranaguá']);$('history-santos').innerHTML=tableRows(report.rows['Santos']);
 const values=rs.map((r,i)=>({i,v:r.physical==null?null:Number(r.physical)})),valid=values.filter(x=>x.v!==null);
 if(!valid.length){$('chart').innerHTML='<p class="secondary">Sem observações físicas nesta janela.</p>';return;}
 const w=1080,h=190,left=55,right=35,top=20,bottom=34,min=Math.min(...valid.map(v=>v.v))-1,max=Math.max(...valid.map(v=>v.v))+1,x=i=>left+i*(w-left-right)/29,y=v=>h-bottom-(v-min)*(h-top-bottom)/(max-min);
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Observações físicas em ${esc(port)}. Tabela completa abaixo.">`;
 for(let i=0;i<3;i++){const v=min+(max-min)*i/2,yy=y(v);svg+=`<line x1="${left}" x2="${w-right}" y1="${yy}" y2="${yy}" stroke="#dfe9e2"/><text x="0" y="${yy+4}">${fmt(v)}</text>`;}
 valid.forEach(p=>{const prev=values[p.i-1];if(prev&&prev.v!==null)svg+=`<path d="M${x(prev.i)},${y(prev.v)} L${x(p.i)},${y(p.v)}" stroke="#2f6b4a" stroke-width="2" fill="none"/>`;svg+=`<circle cx="${x(p.i)}" cy="${y(p.v)}" r="3.5" fill="#2f6b4a"><title>${date(rs[p.i].date)}: R$ ${fmt(p.v)}/sc</title></circle>`;});
 svg+=`<text x="${left}" y="${h-7}">${date(rs[0].date)}</text><text text-anchor="end" x="${w-right}" y="${h-7}">${date(rs[29].date)}</text></svg>`;$('chart').innerHTML=svg;
}
async function load(){try{const r=await fetch('data/report.json',{cache:'no-cache'});if(!r.ok)throw Error('HTTP '+r.status);report=await r.json();render();}catch(e){$('availability').textContent='Não foi possível carregar o checkpoint. Tente recarregar ou baixe o PDF.';$('availability').classList.add('error');}}
document.querySelectorAll('[data-port]').forEach(b=>b.addEventListener('click',()=>{port=b.dataset.port;if(report){renderPort();renderBitcoin();renderFreight();renderBattle();}}));$('reload').addEventListener('click',load);load();

function graph(id,rows,series,title){
 const present=rows.filter(r=>series.some(s=>r[s.key]!=null));
 if(present.length<2){$(id).innerHTML='<div class="empty-chart">Não disponível — requer ao menos duas referências diárias BTC compatíveis. Nenhuma curva foi simulada.</div>';return;}
 const w=1080,h=220,l=75,rr=25,t=20,b=35;
 const vals=present.flatMap(r=>series.map(s=>r[s.key]==null?null:Number(r[s.key])).filter(v=>v!==null));
 const lo=Math.min(...vals),hi=Math.max(...vals),pad=Math.max((hi-lo)*.1,Math.abs(hi)*.005,.01),min=lo-pad,max=hi+pad;
 const first=new Date(present[0].date+'T12:00:00Z'),last=new Date(present[present.length-1].date+'T12:00:00Z');
 const x=d=>l+(new Date(d+'T12:00:00Z')-first)/(last-first)*(w-l-rr),y=v=>h-b-(v-min)/(max-min)*(h-t-b);
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}">`;
 for(let i=0;i<3;i++){const v=min+(max-min)*i/2;svg+=`<line x1="${l}" x2="${w-rr}" y1="${y(v)}" y2="${y(v)}" stroke="#dfe9e2"/><text x="0" y="${y(v)+4}">${fmt(v)}</text>`;}
 series.forEach(s=>{let prev=null;for(const row of present){if(row[s.key]==null){prev=null;continue;}const v=Number(row[s.key]);if(prev&&prev.source===row.source&&(s.key!=='premium_index'||prev.premium_condition===row.premium_condition)&&(new Date(row.date+'T12:00:00Z')-new Date(prev.date+'T12:00:00Z'))===86400000)svg+=`<path d="M${x(prev.date)},${y(Number(prev[s.key]))} L${x(row.date)},${y(v)}" stroke="${s.color}" stroke-width="2" fill="none"/>`;svg+=`<circle cx="${x(row.date)}" cy="${y(v)}" r="3" fill="${s.color}"><title>${date(row.date)} · ${esc(s.label)} · ${esc(row.source||'')}: ${fmt(v)}</title></circle>`;prev=row;}});
 svg+=`<text x="${l}" y="${h-7}">${date(present[0].date)}</text><text text-anchor="end" x="${w-rr}" y="${h-7}">${date(present[present.length-1].date)}</text></svg>`;
 $(id).innerHTML=svg+'<div class="legend">'+series.map(s=>`<span style="color:${s.color}">${esc(s.label)}</span>`).join('')+'</div>';
}
function renderBitcoin(){
 const b=report.bitcoin,rs=b.comparison,last=rs[rs.length-1];
 $('comparison-status').textContent=rs.length>=2?'Base '+date(b.base_date)+' · '+rs.length+' datas comuns · '+[...new Set(rs.map(r=>r.source))].join(' / ')+' · Último descolamento '+fmt(last.divergence_pct)+'% em '+date(last.date)+'.':'Histórico BTC não disponível para comparar. Dólar e bitcoin não foram considerados iguais nem independentes.';
 graph('btc-chart',b.observations,[{key:'price_brl',label:'BTC/BRL · fonte por data',color:'#a45c14'}],'Bitcoin em reais, referência de fonte identificada');
 graph('comparison-chart',rs,[{key:'btc_index',label:'Bitcoin · base 100',color:'#a45c14'},{key:'usd_index',label:'Dólar PTAX · base 100',color:'#2f6b4a'}],'Bitcoin e dólar, base 100');
 graph('premium-chart',b.soy[port]||[],[{key:'premium_index',label:port+' · prêmio em sats · base 100',color:'#70408a'}],'Prêmio de exportação em satoshis, base 100');
 graph('soy-chart',b.soy[port]||[],[{key:'sats_index',label:port+' · soja em sats · base 100',color:'#a45c14'},{key:'usd_index',label:port+' · soja em USD · base 100',color:'#2f6b4a'}],'Soja em satoshis e dólar, base 100');
 $('bitcoin-table').innerHTML=rs.length?[...rs].reverse().map(r=>`<tr><td>${date(r.date)}</td><td>${fmt(r.btc_brl)}<small>${esc(r.source)}</small></td><td>${fmt(r.fx,4)}</td><td>${fmt(r.sats_usd)}</td><td>${fmt(r.divergence_pct)}%</td></tr>`).join(''):'<tr><td colspan="5">Não disponível — histórico diário BTC não disponível.</td></tr>';
}

function renderFreight(){
 const f=report.freight;
 if($('calc-freight').dataset.originPort&&$('calc-freight').dataset.originPort!==port){$('calc-freight').value='';delete $('calc-freight').dataset.origin;delete $('calc-freight').dataset.originPort;}
 $('freight-status').textContent='Conab · referência '+f.period.split('-').reverse().join('/')+' · publicação '+date(f.publication_date)+'. Grãos, não exclusivamente soja. Referências históricas; não são ofertas atuais.';
 const groups=f.groups.filter(g=>g.port===port);
 $('freight-groups').innerHTML=groups.map(g=>`<tr><td>${esc(g.region)}<small>${esc(g.port)}</small></td><td>${esc(g.period)}</td><td>${fmt(g.mean_brl_t)}</td><td>${fmt(g.mean_brl_sc)}</td><td>${g.n===1?'1 rota · referência única':g.n+' rotas'}<small>${fmt(g.min_brl_t)} a ${fmt(g.max_brl_t)}</small></td><td><button type="button" data-freight="${esc(Number(g.mean_brl_t).toFixed(2))}">Usar referência</button></td></tr>`).join('')||'<tr><td colspan="6">Não disponível para esta praça.</td></tr>';
 $('freight-method').textContent=f.method;
 $('freight-routes').innerHTML=f.routes.filter(r=>r.port===port).map(r=>`<tr><td>${esc(r.origin)} · ${esc(r.uf)}</td><td>${esc(r.port)}</td><td>${fmt(r.km,0)}</td><td>${fmt(r.brl_t)}</td><td><a href="${esc(safe(f.source_url))}" target="_blank" rel="noopener noreferrer">${esc(r.period)} · p. ${r.page}</a></td></tr>`).join('');
 document.querySelectorAll('[data-freight]').forEach(b=>b.addEventListener('click',()=>{$('calc-freight').value=b.dataset.freight;$('calc-freight').dataset.origin='Conab · '+f.period;$('calc-freight').dataset.originPort=port;calculate();}));
 calculate();
}
function centsInput(value){
 let s=String(value).trim();if(!s)return null;
 if(s.includes(','))s=s.replace(/\./g,'').replace(',','.');
 if(!/^\d+(\.\d{1,2})?$/.test(s))throw Error('Use valores positivos com até duas casas decimais.');
 const [a,b='']=s.split('.');const result=BigInt(a)*100n+BigInt(b.padEnd(2,'0'));
 if(result>100000000000n)throw Error('Valor acima do limite de entrada.');return result;
}
function roundDivide(a,b){if(b<=0n)throw Error('Divisor inválido');return a<0n?-roundDivide(-a,b):(a+b/2n)/b;}
function asCentsString(v){const sign=v<0n?'-':'';const a=v<0n?-v:v;return sign+(a/100n).toLocaleString('pt-BR')+','+(a%100n).toString().padStart(2,'0');}
function satsForCents(cents,price){
 if(!price)return null;
 const [whole,frac='']=String(price).split('.');
 if(!/^\d+$/.test(whole)||!/^\d*$/.test(frac))throw Error('Referência BTC inválida');
 const scale=10n**BigInt(frac.length),p=BigInt(whole)*scale+BigInt(frac||'0');
 return roundDivide(cents*100000000n*scale,p);
}
function calculate(){
 if(!report)return;
 const r=report.latest[port],key=$('calc-reference').value;
 $('calc-base').textContent=r?port+' · referência '+date(r.date)+' · '+(key==='physical'?'físico observado':'SOMA indicativa, base do prêmio não confirmada')+' · BTC '+(r.bitcoin?.reference?.source||'N/D')+' da mesma data. Entradas locais não são salvas nem enviadas.':'';
 try{
  const freight=centsInput($('calc-freight').value),costs=centsInput($('calc-costs').value),production=centsInput($('calc-production').value);
  if(!r||r[key]==null){$('calc-result').textContent='Referência da praça não disponível.';return;}
  if(freight===null||costs===null){$('calc-result').textContent='Preencha frete e outros custos, inclusive zero quando aplicável. Campos vazios não valem zero.';return;}
  const base=centsInput(r[key]),freightSc=roundDivide(freight*6n,100n),result=base-freightSc-costs,sat=satsForCents(result,r.bitcoin?.btc_brl);
  let text='Cenário: R$ '+asCentsString(result)+'/sc · '+(sat===null?'satoshis N/D':asCentsString(sat)+' sats/sc')+'. Frete: R$ '+asCentsString(freightSc)+'/sc.';
  if(production!==null){const margin=result-production,ms=satsForCents(margin,r.bitcoin?.btc_brl);text+=' Margem simulada: R$ '+asCentsString(margin)+'/sc'+(ms===null?'':' · '+asCentsString(ms)+' sats/sc')+'.';}
  text+=' Valores arredondados a centavos, depois convertidos em sats. '+($('calc-freight').dataset.origin||'Frete informado pelo usuário')+'.';
  $('calc-result').textContent=text;
 }catch(e){$('calc-result').textContent=e.message;}
}
['calc-freight','calc-costs','calc-production'].forEach(id=>$(id).addEventListener('input',()=>{if(id==='calc-freight'){delete $('calc-freight').dataset.origin;delete $('calc-freight').dataset.originPort;}calculate();}));
$('calc-reference').addEventListener('change',calculate);

function renderBattle(){
 const model=report.bitcoin.confronto,mode=$('battle-mode').value;
 const rs=model.rows.map(r=>({...r,scenario:mode==='benchmark'?r.scenarios.benchmark:r.scenarios[mode]?.[port]}));
 const valid=rs.filter(r=>r.scenario);const last=valid[valid.length-1];
 $('battle-limits').textContent=model.limits;
 $('battle-summary').textContent=last?port+' · '+valid.length+' intervalos disponíveis. Último: '+date(last.from)+' a '+date(last.to)+' ('+last.days+' dias corridos); '+last.leader+' teve maior variação. Diferença teórica R$ '+fmt(last.scenario.difference_brl)+'.':'Não disponível: faltam referências iniciais positivas e compatíveis para esta comparação.';
 $('battle-table').innerHTML=[...rs].reverse().map(r=>`<tr><td>${date(r.from)} a ${date(r.to)}<small>${r.days} dias corridos · ${esc(r.source)}</small></td><td>${fmt(r.scenario?.initial_brl)}</td><td>${fmt(r.btc_return_pct)}</td><td>${fmt(r.usd_return_pct)}</td><td>${esc(r.leader)}<small>${signed(r.spread_pp,2)} p.p.</small></td><td>${fmt(r.scenario?.btc_final_brl)}</td><td>${fmt(r.scenario?.usd_final_brl)}</td><td>${fmt(r.scenario?.difference_brl)}${r.scenario?'':'<small>valor inicial indisponível</small>'}</td></tr>`).join('')||'<tr><td colspan="8">Sem intervalos compatíveis.</td></tr>';
 if(!valid.length){$('battle-chart').innerHTML='<div class="empty-chart">Sem valor inicial positivo publicado nesta praça e data. Nenhuma barra foi inventada.</div>';return;}
 const w=1080,h=255,l=75,rr=25,t=20,b=45,max=Math.max(...valid.map(r=>Math.abs(Number(r.scenario.difference_brl))),.01)*1.1;
 const y=v=>t+(max-v)/(2*max)*(h-t-b),step=(w-l-rr)/rs.length,bar=Math.min(step*.72,42);
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Resultado teórico por intervalo, comprado em Bitcoin e vendido em dólar, mesmo valor inicial em reais. Datas e valores completos na tabela.">`;
 [-max,0,max].forEach(v=>{svg+=`<line x1="${l}" x2="${w-rr}" y1="${y(v)}" y2="${y(v)}" stroke="${v===0?'#586b60':'#dfe9e2'}"/><text x="0" y="${y(v)+4}">${fmt(v)}</text>`;});
 rs.forEach((r,i)=>{if(!r.scenario)return;const v=Number(r.scenario.difference_brl),x=l+step*(i+.5);svg+=`<rect x="${x-bar/2}" y="${Math.min(y(0),y(v))}" width="${bar}" height="${Math.max(Math.abs(y(v)-y(0)),1)}" fill="${v>=0?'#a45c14':'#2f6b4a'}"><title>${date(r.from)} a ${date(r.to)} · ${r.days} dias · ${esc(r.leader)} · N R$ ${fmt(r.scenario.initial_brl)} · diferença R$ ${fmt(v)}</title></rect>`;if(i%Math.max(1,Math.ceil(rs.length/8))===0)svg+=`<text x="${x}" y="${h-12}" text-anchor="middle">${date(r.to).slice(0,5)}</text>`;});
 $('battle-chart').innerHTML=svg+'</svg>';
}
$('battle-mode').addEventListener('change',renderBattle);

async function loadReportPrompt(){
 try{const response=await fetch('PROMPT_RELATORIO_DIARIO.txt',{cache:'no-cache'});if(!response.ok)throw Error('Arquivo indisponível');const value=await response.text();$('report-prompt').value=value;$('copy-report-prompt').disabled=false;}
 catch(error){$('report-prompt').value='Não foi possível carregar o texto. Use o link para baixar as instruções em TXT.';$('prompt-copy-status').textContent='Instruções disponíveis no link de download.';}
}
$('copy-report-prompt').addEventListener('click',async()=>{
 try{await navigator.clipboard.writeText($('report-prompt').value);$('prompt-copy-status').textContent='Copiado. Cole no seu ChatGPT e confira a primeira edição antes de confiar na rotina.';}
 catch(error){$('report-prompt').focus();$('report-prompt').select();$('prompt-copy-status').textContent='Texto selecionado. Use a opção Copiar do seu aparelho ou baixe o TXT.';}
});
$('select-report-prompt').addEventListener('click',()=>{$('report-prompt').focus();$('report-prompt').select();$('prompt-copy-status').textContent='Texto selecionado para copiar.';});
loadReportPrompt();
