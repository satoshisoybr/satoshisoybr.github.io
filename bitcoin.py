"""SATOSHISOYBR: unidades de medição, sem execução de operações.

A série Bipa é importada de exportação autorizada. Nenhum dado de conta,
credencial ou saldo integra a base pública. Não há substituição de fornecedor.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal as D, ROUND_HALF_UP
from urllib.parse import urlparse

SATS = D('100000000')
PRECISION = D('.01')

def rounded(x):
 return str(x.quantize(PRECISION, rounding=ROUND_HALF_UP))

def sats(brl, btc_brl):
 if brl is None or btc_brl is None: return None
 price = D(str(btc_brl))
 if not price.is_finite() or price <= 0: raise ValueError('BTC/BRL deve ser positivo e finito')
 value = D(str(brl))
 if not value.is_finite(): raise ValueError('Valor não finito')
 return rounded(value / price * SATS)

def validate_observation(item, today, provider='Bipa'):
 """Somente referências diárias concluídas e datadas; não promove live a fechamento."""
 required = ['date','price_brl','source_url','observed_at','consulted_at','nature','method']
 if any(not item.get(k) for k in required): raise ValueError('Metadados Bipa incompletos')
 day = date.fromisoformat(item['date'])
 if day >= today: raise ValueError('Referência diária deve ser anterior à edição; intradiário fica separado')
 allowed=['bipa.app','www.bipa.app','agents.bipa.app','mcp.bipa.app'] if provider=='Bipa' else ['data-api.binance.vision']
 url=urlparse(item['source_url'])
 if url.scheme!='https' or url.username or url.password or url.fragment:raise ValueError('URL de mercado insegura')
 if url.hostname not in allowed:
  raise ValueError('Fonte deve ser Bipa, sem substituição silenciosa')
 if item['nature'] not in ['daily_close','daily_reference']: raise ValueError('Natureza diária não confirmada')
 observed = datetime.fromisoformat(item['observed_at'])
 consulted = datetime.fromisoformat(item['consulted_at'])
 if observed.utcoffset() is None or consulted.utcoffset() is None: raise ValueError('Horários precisam de fuso')
 from zoneinfo import ZoneInfo
 if observed.astimezone(ZoneInfo('America/Sao_Paulo')).date() != day: raise ValueError('Data Bipa e horário incompatíveis')
 sats('1',item['price_brl'])
 return {k:deepcopy(item[k]) for k in required} | {'source':provider}

def enrich(report, observations, fallback=None):
 """Nenhum carry-forward; toda conversão exige BTC/BRL da própria data."""
 byday = {}
 for item in fallback or []:
  clean=validate_observation(item,date.fromisoformat(report['edition']),'Binance')
  byday[clean['date']]=clean
 bipa_dates=set()
 for item in observations:
  clean = validate_observation(item,date.fromisoformat(report['edition']))
  if clean['date'] in bipa_dates: raise ValueError('Referência Bipa duplicada por data')
  bipa_dates.add(clean['date'])
  byday[clean['date']] = clean
 checks = 0
 fields = ['chicago_brl','premium_brl','physical','residual']
 for rows in report['rows'].values():
  for row in rows:
   obs = byday.get(row['date']); price = obs['price_brl'] if obs else None
   out = {key:sats(row.get(key),price) for key in fields}
   out['sum'] = rounded(D(out['chicago_brl'])+D(out['premium_brl'])) if row.get('sum') is not None and out['chicago_brl'] is not None and out['premium_brl'] is not None else None
   out['residual'] = rounded(D(out['physical'])-D(out['sum'])) if out['physical'] is not None and out['sum'] is not None else None
   out['usd'] = sats(row.get('fx'),price)
   out['btc_brl'] = price; out['reference'] = obs
   row['bitcoin'] = out
   if out['sum'] is not None:
    assert D(out['sum']) == D(out['chicago_brl'])+D(out['premium_brl']); checks += 1
   if out['residual'] is not None:
    assert D(out['residual']) == D(out['physical'])-D(out['sum']); checks += 1
 for port, rows in report['rows'].items():
  latest = report['latest'][port]
  if latest: report['latest'][port] = next(r for r in rows if r['date']==latest['date'])
 for r in report['futures']:
  obs = byday.get(r.get('date')); price=obs['price_brl'] if obs else None
  r['bitcoin']={'reference':obs,'reference_sc':sats(r.get('brl_sc'),price),'flow_estimate':sats(r.get('flow_brl_estimate'),price),'usd':sats(r.get('fx'),price)}
 fx = {r['date']:r.get('fx') for r in report['rows']['Paranaguá']}
 for r in report['options']:
  day=r.get('verified_date');obs=byday.get(day);price=obs['price_brl'] if obs else None
  strike=D(r['strike'])*D(fx[day]) if r.get('strike') and fx.get(day) else None
  r['bitcoin']={'strike':sats(strike,price),'reference':obs,'date':day}
 for r in report['five']:
  # Engine keeps endpoint prices: no fabricated BTC return from a BRL percentage.
  a,b=byday.get(r['from']),byday.get(r['to'])
  homogeneous=bool(a and b and a['source']==b['source'] and all(x['source']==a['source'] for day,x in byday.items() if r['from']<=day<=r['to']))
  first=sats(r.get('first_brl'),a['price_brl']) if homogeneous else None
  last=sats(r.get('last_brl'),b['price_brl']) if homogeneous else None
  r['bitcoin']={'delta':rounded(D(last)-D(first)) if first is not None and last is not None else None,'pct':str((D(last)/D(first)-1)*100) if first and last and D(first)!=0 else None}
 common=[]
 for day in sorted(byday):
  if not (report['window_start']<=day<=report['window_end']) or not fx.get(day):continue
  common.append({'date':day,'source':byday[day]['source'],'btc_brl':byday[day]['price_brl'],'fx':fx[day],'sats_usd':sats(fx[day],byday[day]['price_brl'])})
 if common:
  bases={}
  for r in common:
   first=bases.setdefault(r['source'],r)
   r['base_date']=first['date']
   br=D(r['btc_brl'])/D(first['btc_brl']);fr=D(r['fx'])/D(first['fx'])
   r.update(btc_index=str(br*100),usd_index=str(fr*100),divergence_pct=str((br/fr-1)*100));checks+=1
 soy={}
 for port,rows in report['rows'].items():
  series=[]
  for r in rows:
   if r['bitcoin']['physical'] is None or not r.get('physical_usd'):continue
   series.append({'date':r['date'],'source':r['bitcoin']['reference']['source'],'sats_sc':r['bitcoin']['physical'],'usd_bu':r['physical_usd'],'premium_sats':r['bitcoin']['premium_brl'],'premium_condition':r.get('premium_condition')})
  if series:
   bases={};premium_bases={}
   for r in series:
    a=bases.setdefault(r['source'],r)
    pa=premium_bases.setdefault((r['source'],r['premium_condition']),r) if r['premium_sats'] is not None else r
    r.update(base_date=a['date'],sats_index=str(D(r['sats_sc'])/D(a['sats_sc'])*100),usd_index=str(D(r['usd_bu'])/D(a['usd_bu'])*100),premium_index=str(D(r['premium_sats'])/D(pa['premium_sats'])*100) if r['premium_sats'] is not None and pa['premium_sats'] is not None and D(pa['premium_sats'])>0 else None)
  soy[port]=series
 report['bitcoin']={'name':'SATOSHISOYBR','unit':'sats/sc','dollar_unit':'sats/US$','provider':'Bipa; Binance na ausência por data','status':('Fontes diárias: '+', '.join(sorted({x['source'] for x in byday.values()}))+'. Binance é alternativa identificada; não é cotação Bipa.') if byday else 'não disponível — sem referência Bipa ou Binance verificada','observations':[byday[d] for d in sorted(byday) if report['window_start']<=d<=report['window_end']],'comparison':common,'soy':soy,'base_date':common[0]['date'] if common else None,'method':'sats/sc = BRL/sc ÷ BTC/BRL × 100.000.000; sats/US$ = PTAX venda ÷ BTC/BRL × 100.000.000. Mesma data civil; horários podem diferir. Arredondamento HALF_UP a 0,01 sat apenas na apresentação. SOMA e residual fecham sobre parcelas apresentadas.'}
 report['quality']['checks']+=checks;report['quality']['passed']+=checks
 from confronto import attach
 return attach(report)
