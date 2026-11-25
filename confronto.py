"""Comparação descritiva de duas exposições iguais em BRL, sem execução.

Cada intervalo reinicia o valor inicial. Não soma percentuais nem transforma
PTAX em preço executável de venda de dólar ou BTC spot em derivativo.
"""
from datetime import date
from decimal import Decimal as D, ROUND_HALF_UP

def q(value):return str(value.quantize(D('.01'),rounding=ROUND_HALF_UP))

def interval(a,b):
 if b['date']<=a['date']:raise ValueError('Datas fora de ordem')
 if a['source']!=b['source']:return None
 btc=D(b['btc_brl'])/D(a['btc_brl'])-1
 usd=D(b['fx'])/D(a['fx'])-1
 spread=btc-usd
 out={'from':a['date'],'to':b['date'],'days':(date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days,'source':a['source'],'btc_return_pct':str(btc*100),'usd_return_pct':str(usd*100),'spread_pp':str(spread*100),'btc_in_usd_return_pct':str(((1+btc)/(1+usd)-1)*100),'leader':'Bitcoin' if spread>0 else 'Dólar' if spread<0 else 'Empate','btc_brl_start':a['btc_brl'],'btc_brl_end':b['btc_brl'],'fx_start':a['fx'],'fx_end':b['fx']}
 # Benchmark explícito. Resultado = duas quantidades fixas, não um retorno líquido.
 n=D('1000');out['benchmark_brl']='1000';out['btc_value_brl']=q(n*(1+btc));out['usd_value_brl']=q(n*(1+usd));out['long_btc_short_usd_brl']=q(n*spread)
 # Visual difference uses separately rounded asset values; raw full precision kept.
 out['difference_presented_brl']=q(D(out['btc_value_brl'])-D(out['usd_value_brl']))
 assert abs(D(out['difference_presented_brl'])-D(out['long_btc_short_usd_brl']))<=D('.01')
 return out

def scenario(n,a,b):
 if n is None or D(str(n))<=0:return None
 n=D(str(n));qb=n/D(a['btc_brl']);qu=n/D(a['fx'])
 raw_btc=qb*D(b['btc_brl']);raw_usd=qu*D(b['fx'])
 bv,uv=D(q(raw_btc)),D(q(raw_usd))
 direct=qb*(D(b['btc_brl'])-D(a['btc_brl']))-qu*(D(b['fx'])-D(a['fx']))
 return {'initial_brl':str(n),'btc_quantity':str(qb),'usd_quantity':str(qu),'btc_final_brl':str(bv),'usd_final_brl':str(uv),'difference_brl':q(bv-uv),'direct_difference_brl':q(direct)}

def attach(report):
 common=report['bitcoin']['comparison'];rows=[];checks=0
 physical={port:{r['date']:r for r in rs} for port,rs in report['rows'].items()}
 for a,b in zip(common,common[1:]):
  r=interval(a,b)
  if r is None:continue
  r['initial_by_port']={}
  r['scenarios']={'benchmark':scenario('1000',a,b),'premium':{},'physical':{}}
  for port,byday in physical.items():
   original=byday.get(a['date'],{})
   values={}
   for key,label in [('premium_brl','premium'),('physical','physical')]:
    raw=original.get(key)
    values[label]=raw if raw is not None and D(raw)>0 else None
   r['initial_by_port'][port]=values
   for mode,n in values.items():
    result=scenario(n,a,b);r['scenarios'][mode][port]=result
    if result:
     assert abs(D(result['difference_brl'])-D(result['direct_difference_brl']))<=D('.01');checks+=1
  # Independent fixed-quantity check of hypothetical equal-notional long/short.
  n=D(r['benchmark_brl'])
  direct=(n/D(a['btc_brl']))*(D(b['btc_brl'])-D(a['btc_brl']))-(n/D(a['fx']))*(D(b['fx'])-D(a['fx']))
  assert abs(direct-D(r['long_btc_short_usd_brl']))<=D('.0050000001');checks+=1
  rows.append(r)
 report['bitcoin']['confronto']={'rows':rows,'benchmark_brl':'1000','mode':'intervalos entre fechamentos comuns; base reiniciada em cada intervalo','method':'rBTC = BTC_t/BTC_0 - 1; rUSD = PTAX_t/PTAX_0 - 1; resultado teórico em BRL = N × (rBTC - rUSD). Quantidades fixas iniciais N/BTC_0 e N/PTAX_0, mesmo valor inicial em BRL. Comparação de referências, sem spread, tarifas, impostos, financiamento, margem ou ajustes de instrumento. Não é hedge contratado nem teste de eficácia da proteção da soja.','limits':'Dias sem PTAX não ganham preço artificial. Intervalos podem abranger fins de semana e feriados; datas e duração são mostradas. Não atravessa troca de fornecedor BTC. Prêmio é parcela do preço da soja, não aplicação com rendimento próprio; só usamos seu valor inicial como tamanho da simulação. Vender soja em BTC ou USD requer oferta comercial e condições de liquidação, não provadas por esta comparação.'}
 report['quality']['checks']+=checks;report['quality']['passed']+=checks
 return report
