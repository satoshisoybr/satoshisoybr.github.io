"""Soja Aberta: dados públicos, Decimal, publicação sem identificação pessoal."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,os,urllib.request,zipfile,xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import date,datetime,timedelta
from decimal import Decimal as D,ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent;STATE=ROOT/'data/state.json';DIST=ROOT;TZ=ZoneInfo('America/Sao_Paulo');K=D('2.20462')
CENT=D('.01');MONTHS={'janeiro':1,'fevereiro':2,'março':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12};CODES='FGHJKMNQUVXZ'
def quant(x):return D(str(x)).quantize(CENT,rounding=ROUND_HALF_UP)
def stamp():return datetime.now(TZ).isoformat()
def save(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n');tmp.replace(path)
def number(text):
 s=re.sub(r'[^0-9,.+\-]','',str(text))
 if ',' in s:s=s.replace('.','').replace(',','.')
 return str(D(s))
def source(url,effective,published=None,consulted=None):return {'url':url,'date':effective,'published_at':published,'consulted_at':consulted or stamp()}
def fetch(url,limit=60_000_000):
 req=urllib.request.Request(url,headers={'User-Agent':'SojaAberta/1.0 (+public-price-observatory)'})
 with urllib.request.urlopen(req,timeout=35) as r:
  raw=r.read(limit+1)
  if len(raw)>limit:raise ValueError('Resposta excede limite')
 return raw
def record(state,port,day,fields,origin):
 date.fromisoformat(day)
 if day>datetime.now(TZ).date().isoformat():raise ValueError('Cotação futura rejeitada')
 market=state['markets'][port];r=next((x for x in market if x['date']==day),None)
 if r is None:r={'date':day,'port':port,'sources':{}};market.append(r)
 for key,value in fields.items():
  old=r.get(key)
  if old is not None and old!=value:
   state.setdefault('revisions',[]).append({'at':stamp(),'port':port,'date':day,'field':key,'previous':old,'new':value,'source':origin,'reason':'nova captura publicada; revisão explícita'})
  r[key]=value;r.setdefault('sources',{})[key]=origin
 return r

def derive(row):
 """Combina apenas valores pertencentes à mesma linha/data, sem preenchimento."""
 r=deepcopy(row)
 for key in ['chicago_brl','premium_brl','sum','physical','physical_usd','residual']:r[key]=None
 fx=D(r['fx']) if r.get('fx') is not None else None
 if fx is not None and fx<=0:raise ValueError('PTAX não positiva')
 cb=D(r['cbot']) if r.get('cbot') is not None else None;pr=D(r['premium']) if r.get('premium') is not None else None
 if fx is not None and cb is not None:r['chicago_brl']=str(quant(fx*cb*K))
 if fx is not None and pr is not None:r['premium_brl']=str(quant(fx*pr*K))
 if r['chicago_brl'] is not None and r['premium_brl'] is not None and not r.get('incompatible_base',False):r['sum']=str(D(r['chicago_brl'])+D(r['premium_brl']))
 physical=D(r['physical_brl_raw']) if r.get('physical_brl_raw') is not None else D(r['physical_usd_raw'])*fx*K if r.get('physical_usd_raw') is not None and fx is not None else None
 if physical is not None:r['physical']=str(quant(physical))
 if physical is not None and fx is not None:r['physical_usd']=str(physical/fx/K)
 if r['sum'] is not None and r['physical'] is not None:r['residual']=str(D(r['physical'])-D(r['sum']))
 r['sum_status']='estimativa indicativa, base do prêmio não confirmada' if r['sum'] is not None else 'não disponível'
 return r

def fetch_ptax(state):
 today=datetime.now(TZ).date();start=(today-timedelta(days=10)).strftime('%m-%d-%Y');end=today.strftime('%m-%d-%Y')
 url=f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@i,dataFinalCotacao=@f)?@i='{start}'&@f='{end}'&$format=json"
 data=json.loads(fetch(url),parse_float=D)
 for x in data.get('value',[]):
  # Endpoint reports official closing PTAX, never a live commercial quote.
  day=x['dataHoraCotacao'][:10];meta=source(url,day,x['dataHoraCotacao']+' Brasília')
  for port in state['markets']:record(state,port,day,{'fx':str(x['cotacaoVenda'])},meta)
 return f"BCB: {len(data.get('value',[]))} fechamentos consultados"

def fetch_agricultural(state):
 from bs4 import BeautifulSoup
 url='https://www.noticiasagricolas.com.br/cotacoes/soja';html=fetch(url);soup=BeautifulSoup(html,'html.parser');count=0
 config=json.loads((ROOT/'config.json').read_text());today=datetime.now(TZ).date().isoformat()
 for h in soup.find_all(['h2','h3']):
  title=h.get_text(' ',strip=True);table=h.find_next('table')
  if not table:continue
  rows=[[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'])] for tr in table.find_all('tr')]
  if not rows:continue
  chunks=[]
  for item in table.next_elements:
   if getattr(item,'name',None) in ['h2','h3']:break
   if isinstance(item,str):chunks.append(item)
  match=re.search(r'Atualizado em:\s*(\d{2})/(\d{2})/(\d{4})',' '.join(chunks));day=f'{match[3]}-{match[2]}-{match[1]}' if match else None
  if 'ESALQ/B3' in title and 'Paranaguá' in title:
   for cells in rows[1:]:
    if len(cells)<2:continue
    m=re.fullmatch(r'(\d{2})/(\d{2})/(\d{4})',cells[0])
    if m and f'{m[3]}-{m[2]}-{m[1]}'<today:record(state,'Paranaguá',f'{m[3]}-{m[2]}-{m[1]}',{'physical_brl_raw':number(cells[1])},source(url,f'{m[3]}-{m[2]}-{m[1]}'));count+=1
  elif 'Bolsa de Chicago' in title and 'Farelo' not in title and day and day<today:
   for cells in rows[1:]:
    if len(cells)<2:continue
    m=re.search(r'([A-Za-zçÇ]+)/(\d{2,4})',cells[0]);month=MONTHS.get(m[1].lower()) if m else None
    if not month:continue
    year=int(m[2]);year=year+2000 if year<100 else year;ticker='ZS'+CODES[month-1]+str(year)[-2:];verified=config['cbot_contracts'].get(ticker)
    if not verified or day>verified['last_trade'] or today>verified['last_trade']:continue
    # Follow only the configured live series. Other contracts are not spliced in.
    if ticker!=config['active_cbot']:continue
    for port in state['markets']:record(state,port,day,{'cbot':number(cells[1]),'contract':ticker,'contract_last_trade':verified['last_trade']},source(url,day))
    count+=1
  elif title.startswith('Prêmio Soja Paranaguá') and day and day<today:
   for cells in rows[1:]:
    if len(cells)<2:continue
    if cells[0].lower()==config['paranagua_shipment'].lower():record(state,'Paranaguá',day,{'premium':number(cells[1]),'premium_condition':'embarque '+cells[0]+'; base CBOT não confirmada'},source(url,day));count+=1
 if count==0:raise ValueError('Estrutura/data das tabelas não reconhecida; captura anterior preservada')
 current=config['cbot_contracts'].get(config['active_cbot'],{})
 if today>current.get('last_trade','0000-00-00'):state['warnings'].append('Contrato CBOT configurado encerrado; confirmar sucessor e calendário oficial antes de continuar. Sem rolagem automática não verificada.')
 return f'Notícias Agrícolas: {count} referências capturadas'

def fetch_santos(state):
 url='https://www.theagribiz.com/wp-content/cotacoes/dados.json';raw=json.loads(fetch(url),parse_float=D);count=0
 for x in raw.get('cotacoes',[]):
  if x.get('id') not in ['indice-523a846c','premio-santos']:continue
  if 'bushel' not in x.get('unidade',''):raise ValueError('Unidade de Santos não confirmada')
  day=x['data']
  if day>=datetime.now(TZ).date().isoformat():raise ValueError('Índice do dia sem fechamento confirmado; preservar referência anterior')
  key='physical_usd_raw' if x['id']=='indice-523a846c' else 'premium';fields={key:str(D(str(x['valor']))/100),'premium_condition':'spot Santos; embarque/base CBOT não confirmados'}
  record(state,'Santos',day,fields,source(url,day,raw.get('gerado_em')));count+=1
 if count!=2:raise ValueError('Índice FOB e prêmio spot não encontrados juntos')
 return 'Santos: captura publicada preservada com data dos itens'

def flatten(element):
 out={}
 for x in element.iter():
  if len(x)==0 and x.text:out.setdefault(x.tag.rsplit('}',1)[-1],x.text.strip())
 return out
def zipxml(raw):
 z=zipfile.ZipFile(io.BytesIO(raw));xml=sorted(n for n in z.namelist() if n.endswith('.xml'))
 if not xml:
  nested=next((n for n in z.namelist() if n.endswith('.zip')),None)
  if nested:return zipxml(z.read(nested))
  raise ValueError('XML não encontrado')
 return z.read(xml[-1]),xml[-1]
def instrument_nodes(xml):
 # Parse a bounded complete instrument rather than independently matching leaf tags.
 root=ET.fromstring(xml)
 for e in root.iter():
  if e.tag.rsplit('}',1)[-1] in ['PricRpt','FinInstrm','FinInstrmRptgAddtlInf','Instrm']:
   vals=flatten(e)
   if vals.get('TckrSymb'):yield vals

def fetch_b3(state):
 today=datetime.now(TZ).date();existing=max((r['date'] for r in state['b3']),default=(today-timedelta(days=3)).isoformat());count=0
 days=[today-timedelta(days=i) for i in range(5,-1,-1)]
 for d in days:
  day=d.isoformat()
  if day<=existing or d>=today or d.weekday()>4:continue
  url=f'https://www.b3.com.br/pesquisapregao/download?filelist=PR{d:%y%m%d}.zip'
  try:raw=fetch(url);xml,entry=zipxml(raw)
  except Exception as exc:state['warnings'].append(f'B3 {day}: {type(exc).__name__}; não apaga captura anterior');continue
  found=[]
  for v in instrument_nodes(xml):
   ticker=v['TckrSymb']
   if not re.fullmatch(r'(SJC|SOY)[FGHJKMNQUVXZ]\d{2}',ticker) or not v.get('AdjstdQt'):continue
   found.append({'date':day,'ticker':ticker,'family':ticker[:3],'settlement':v['AdjstdQt'],'previous_settlement':v.get('PrvsAdjstdQt'),'unit':'USD/sc 60kg' if ticker.startswith('SJC') else 'USD/t','volume':v.get('FinInstrmQty'),'number_of_trades':v.get('TradQty'),'bid':v.get('BestBidPric'),'ask':v.get('BestAskPric'),'source_url':url,'publication_time':None,'consulted_at':stamp(),'archive_entry':entry})
  if not found:state['warnings'].append(f'B3 {day}: formato sem ajustes reconhecidos; conferir adaptador');continue
  for r in found:
   prior=next((x for x in state['b3'] if x['ticker']==r['ticker'] and x['date']==day),None)
   if prior is None:state['b3'].append(r);count+=1
 return f'B3: {count} ajustes novos; puts sem pesquisa automática de ask'

def fetch_binance(state,captured=None):
 from urllib.parse import urlencode
 from bitcoin import validate_observation
 now=datetime.now(TZ);today=now.date();prior=state.get('bitcoin_binance',[])
 last=max((r['date'] for r in prior),default=None)
 start=date.fromisoformat(last)+timedelta(days=1) if last else today-timedelta(days=34)
 if start>=today:return 'Binance: sem novo fechamento diário'
 startms=int(datetime.combine(start,datetime.min.time(),TZ).timestamp()*1000)
 endms=int(datetime.combine(today,datetime.min.time(),TZ).timestamp()*1000)-1
 url='https://data-api.binance.vision/api/v3/klines?'+urlencode({'symbol':'BTCBRL','interval':'1d','timeZone':'-3','startTime':startms,'endTime':endms,'limit':1000})
 if captured:
  url=captured['url'];raw=captured['raw'];now=datetime.fromisoformat(captured['consulted_at'])
 else:raw=fetch(url)
 data=json.loads(raw)
 if not isinstance(data,list):raise ValueError('Resposta Binance não é lista de candles')
 found=[]
 for k in data:
  if not isinstance(k,list) or len(k)<12:raise ValueError('Candle Binance incompleto')
  opened=datetime.fromtimestamp(int(k[0])/1000,TZ);closed=datetime.fromtimestamp(int(k[6])/1000,TZ)
  if closed>=now or closed.date()>=today:continue
  if opened.hour!=0 or opened.minute!=0 or closed.date()!=opened.date() or int(k[6])-int(k[0])!=86399999:raise ValueError('Janela diária Binance incompatível com Brasília')
  obs={'date':opened.date().isoformat(),'price_brl':str(k[4]),'source_url':url,'observed_at':closed.isoformat(),'consulted_at':now.isoformat(),'nature':'daily_close','method':'BTCBRL spot; fechamento do candle diário 00:00–23:59:59,999 Brasília (timeZone=-3), último negócio; não é ask, Bipa ou cotação simultânea à PTAX'}
  clean=validate_observation(obs,today,'Binance');clean['evidence']={'response_sha256':hashlib.sha256(raw).hexdigest(),'open_time_ms':k[0],'close_time_ms':k[6],'close':k[4],'symbol':'BTCBRL','interval':'1d'};found.append(clean)
 existing={r['date']:r for r in prior}
 for r in found:
  if r['date'] not in existing:existing[r['date']]=r
 state['bitcoin_binance']=[existing[d] for d in sorted(existing)]
 return f'Binance: {len(found)} fechamentos BTCBRL consultados; dados públicos, sem chave de conta'

def build(state,today=None):
 today=today or datetime.now(TZ).date();start=today-timedelta(days=29);rows={};latest={};checks=0
 for port,raw in state['markets'].items():
  byday={r['date']:r for r in raw};rs=[]
  for i in range(30):
   d=(start+timedelta(days=i)).isoformat();r=derive(byday.get(d,{'date':d,'port':port}));checks+=1
   for key in ['fx','cbot','premium','physical_brl_raw','physical_usd_raw']:
    origin=r.get('sources',{}).get(key)
    if origin and origin.get('date')!=d:raise ValueError('Origem com data incompatível')
   if r.get('sum') is not None:assert D(r['sum'])==D(r['chicago_brl'])+D(r['premium_brl']);checks+=1
   if r.get('residual') is not None:assert D(r['residual'])==D(r['physical'])-D(r['sum']);checks+=1
   rs.append(r)
  rows[port]=rs;latest[port]=next((r for r in reversed(rs) if r['physical'] is not None),None)
 futures=[];five=[];flows=[]
 fx={r['date']:r.get('fx') for r in state['markets']['Paranaguá'] if r.get('fx')}
 for ticker in state['config']['b3_contracts']:
  values=sorted((x for x in state['b3'] if x['ticker']==ticker),key=lambda x:x['date']);r=deepcopy(values[-1]) if values else {'ticker':ticker};a=D(r['settlement']) if r.get('settlement') else None;b=D(r['previous_settlement']) if r.get('previous_settlement') else None;x=D(fx[r['date']]) if r.get('date') in fx else None;fac=D(1) if ticker.startswith('SJC') else D('.06')
  r.update({'brl_sc':str(quant(a*x*fac)) if a is not None and x else None,'pct':str((a/b-1)*100) if a is not None and b else None,'flow_usd':str(-(a-b)*450*fac) if a is not None and b is not None else None,'flow_brl_estimate':str(quant(-(a-b)*450*fac*x)) if a is not None and b is not None and x else None,'fx':str(x) if x else None,'actual_brl':None});futures.append(r)
  if len(values)>=6:
   seq=values[-6:]
   if all(v['date'] in fx for v in seq):
    first,last=seq[0],seq[-1];aa=quant(D(first['settlement'])*D(fx[first['date']])*fac);bb=quant(D(last['settlement'])*D(fx[last['date']])*fac)
    five.append({'label':ticker,'from':first['date'],'to':last['date'],'first_brl':str(aa),'last_brl':str(bb),'delta':str(bb-aa),'pct':str((bb-aa)/aa*100)})
 for port,rs in rows.items():
  for key,label in [('physical','Físico'),('premium_brl','Prêmio')]:
   valid=[r for r in rs if r.get(key) is not None]
   if len(valid)>=6:
    a,b=valid[-6],valid[-1]
    if key=='premium_brl' and a.get('premium_condition')!=b.get('premium_condition'):continue
    aa,bb=D(a[key]),D(b[key]);five.append({'label':port+' · '+label,'from':a['date'],'to':b['date'],'first_brl':str(aa),'last_brl':str(bb),'delta':str(bb-aa),'pct':str((bb-aa)/aa*100)})
 options=[]
 for o in state.get('options',[]):
  r=deepcopy(o);r['cost_status']='não disponível — requer cotação';r['premium_brl']=None;r['cost450']=None
  r['expired']=bool(r.get('expiration') and r['expiration']<today.isoformat());r['days']=(date.fromisoformat(r['expiration'])-today).days if r.get('expiration') else None
  options.append(r)
 report={'edition':today.isoformat(),'cutoff':state.get('updated_at'),'window_start':start.isoformat(),'window_end':today.isoformat(),'rows':rows,'latest':latest,'futures':futures,'options':options,'five':five,'warnings':state.get('warnings',[]),'news':state.get('news',[])[:2],'automation':{'active':os.environ.get('GITHUB_ACTIONS')=='true','schedule':'segunda a sexta,12h Brasília','status':'Execução GitHub Actions' if os.environ.get('GITHUB_ACTIONS')=='true' else 'Workflow preparado; ativação no GitHub pendente'},'quality':{'checks':checks,'passed':checks,'failed':0},'config':state['config']}
 from bitcoin import enrich
 report['freight']=json.loads((ROOT/'data/freight.json').read_text())
 from freight import groups
 report['freight']['groups']=groups(report['freight']['routes'])
 return enrich(report,json.loads((ROOT/'data/bipa_prices.json').read_text()),state.get('bitcoin_binance',[]))

def fmt(x,n=2):return 'N/D' if x is None else f'{D(str(x)):,.{n}f}'.replace(',','|').replace('.',',').replace('|','.')
def pdf_report(report):
 from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer,PageBreak
 from reportlab.lib import colors
 from reportlab.lib.styles import ParagraphStyle
 from reportlab.lib.pagesizes import A4,landscape
 path=DIST/'Soja_Composicao_Preco.pdf';style=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=13);head=ParagraphStyle('head',parent=style,fontSize=16,leading=20,textColor=colors.HexColor('#163e33'));story=[]
 for idx,(port,rs) in enumerate(report['rows'].items()):
  for part in range(2):
   if story:story.append(PageBreak())
   story += [Paragraph('Soja - Composição de preços | '+port,head),Spacer(1,8),Paragraph(f"Edição {report['edition']} | Corte {report['cutoff']} | 1 sc = 60 kg; 1 bu = 60 lb; 1 sc = 2,20462 bu",style),Spacer(1,10)]
   headers=['Data','PTAX venda','Chicago R$/sc\n(US$/bu)','Prêmio R$/sc\n(US$/bu)','SOMA','Físico R$/sc\n(US$/bu)','Residual','Bitcoin físico\nsats/sc (BTC/sc)'];data=[headers]
   for r in rs[part*15:(part+1)*15]:
    data.append([r['date']+'\n'+r.get('contract',''),fmt(r.get('fx'),4),fmt(r['chicago_brl'])+'\n('+fmt(r.get('cbot'),4)+')',fmt(r['premium_brl'])+'\n('+(('+' if r.get('premium') is not None and D(r['premium'])>0 else '')+fmt(r.get('premium'),4))+')',fmt(r['sum']),fmt(r['physical'])+'\n('+fmt(r['physical_usd'],4)+')',fmt(r['residual']),fmt(r['bitcoin']['physical'])+'\n('+fmt(D(r['bitcoin']['physical'])/D('100000000'),10)+' BTC)' if r['bitcoin']['physical'] is not None else 'N/D'])
   t=Table(data,colWidths=[65,64,109,109,65,109,65,145],rowHeights=[35]+[24]*15)
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#163e33')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),10),('LEADING',(0,0),(-1,-1),10.5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#eff4f0')]),('ALIGN',(1,1),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,0),'CENTER')]))
   story.extend([t,Spacer(1,8),Paragraph('SOMA: estimativa indicativa; base do prêmio não confirmada. Residual é diferença entre referências, não despesa. Datas não são preenchidas. Fontes e metadados completos no site e na base JSON. Chicago vigente: '+report['config']['active_cbot']+'.',style)])
 story.append(PageBreak());story.extend([Paragraph('Futuros em dólar + Bitcoin, proteção e método',head),Spacer(1,12)])
 for r in report['futures']:
  story.append(Paragraph(f"{r['ticker']} | {r.get('date','N/D')} | Ajuste {fmt(r.get('settlement'),4)} {r.get('unit','')} | Fluxo vendido450sc {fmt(r.get('flow_usd'))} USD | Estimativa PTAX {fmt(r.get('flow_brl_estimate'))} BRL. Caixa BRL real: N/D.",style));story.append(Paragraph('Bitcoin equivalente: '+fmt(r.get('bitcoin',{}).get('reference_sc'))+' sats/sc. Conversão indicativa da referência em reais, fonte BTC da mesma data; não é liquidação B3 em BTC.',style));story.append(Spacer(1,8))
 for o in report['options']:story.append(Paragraph(o.get('ticker','Put')+' | ExercícioUSD/sc '+fmt(o.get('strike'))+' | Expiração '+o.get('expiration','N/D')+' | Prêmio e desembolso: não disponível - requer cotação.',style))
 story.extend([Spacer(1,12),Paragraph('Chicago e prêmio emUSD/bu multiplicam PTAX da mesma data e2,20462. SOMA usa parcelas arredondadas a centavos(HALF_UP). Físico emUSD/bu é convertido pela mesma PTAX. Fontes: BCB, CME/CEPEA via NotíciasAgrícolas, B3 e Grainsights/TheAgriBiz. Ajuste não é oferta executável; put não é prêmio de exportação. Sem operações contratadas ou recomendações de entrada/saída.',style)])
 story.extend([PageBreak(),Paragraph('SATOSHISOYBR | Confronto BTC e dólar',head),Spacer(1,10),Paragraph('Simulação descritiva com R$ 1.000 no início de cada intervalo. Mesma base inicial em reais; comprado em BTC e vendido em dólar. Sem custos ou operação executada. Não é teste de eficácia de hedge da soja.',style),Spacer(1,10)])
 data=[['Intervalo','Dias','BTC %','USD %','Maior variação','Diferença R$']]
 for r in report['bitcoin']['confronto']['rows'][-18:]:
  data.append([r['from']+' a '+r['to'],str(r['days']),fmt(r['btc_return_pct']),fmt(r['usd_return_pct']),r['leader'],fmt(r['scenarios']['benchmark']['difference_brl'])])
 t=Table(data,colWidths=[210,55,100,100,135,131],rowHeights=[27]+[18]*(len(data)-1));t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),10),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#163e33')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#eff4f0')]),('ALIGN',(1,1),(-1,-1),'RIGHT')]))
 story.extend([t,Spacer(1,10),Paragraph('Equação: N x (variação BTC/BRL - variação PTAX). A tabela apresenta a diferença entre valores finais arredondados. Cada intervalo reinicia N; não somar como saldo de posição contínua. Dias sem PTAX não foram preenchidos; o intervalo pode abranger feriados e fins de semana. Prêmio só dimensiona o capital na opção disponível no site; não é aplicação com rendimento próprio. Veja fonte, horários e hipóteses completas na base pública e no site.',style)])
 SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=35,rightMargin=35,topMargin=30,bottomMargin=28,title='Soja - Composição de preços',author='').build(story)

def publish(state):
 report=build(state);(DIST/'data').mkdir(parents=True,exist_ok=True);save(DIST/'data/report.json',report);save(DIST/'data/state.json',state)
 cols=['port','date','contract','fx','cbot','premium','chicago_brl','premium_brl','sum','physical','physical_usd','residual','sum_status','sats_sc','sats_usd','btc_brl']
 with (DIST/'data/observacoes.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader()
  for rs in report['rows'].values():w.writerows([{**r,'sats_sc':r['bitcoin']['physical'],'sats_usd':r['bitcoin']['usd'],'btc_brl':r['bitcoin']['btc_brl']} for r in rs])
 save(DIST/'data/bipa_prices.json',json.loads((ROOT/'data/bipa_prices.json').read_text()));save(DIST/'data/freight.json',report['freight']);pdf_report(report);return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--collect',action='store_true');a=p.parse_args();state=json.loads(STATE.read_text());state['config']=json.loads((ROOT/'config.json').read_text())
 if a.collect:
  state['warnings']=[];results=[]
  for fn in [fetch_ptax,fetch_agricultural,fetch_santos,fetch_b3,fetch_binance]:
   checkpoint=deepcopy(state)
   try:results.append({'source':fn.__name__,'status':'ok','message':fn(state)})
   except Exception as exc:state=checkpoint;state['warnings'].append(f'{fn.__name__}: {type(exc).__name__}; captura anterior preservada');results.append({'source':fn.__name__,'status':'failed','error_type':type(exc).__name__})
  state['last_attempt_at']=stamp();state['collection_results']=results
  if any(r['status']=='ok' for r in results):state['updated_at']=stamp()
 report=publish(state);save(STATE,state);print(json.dumps({'edition':report['edition'],'checks':report['quality'],'warnings':state.get('warnings',[]),'latest':{p:(r['date'] if r else None) for p,r in report['latest'].items()}},ensure_ascii=False))
if __name__=='__main__':main()
