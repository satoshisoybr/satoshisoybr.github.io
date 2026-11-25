"""Amostras regionais: média simples de rotas publicadas, sem peso inventado."""
from decimal import Decimal as D,ROUND_HALF_UP

def groups(routes):
 grouped={}
 for r in routes:
  if r.get('brl_t') is None:continue
  value=D(r['brl_t'])
  if not value.is_finite() or value<0:raise ValueError('Frete inválido')
  grouped.setdefault((r['region'],r['port'],r['period']),[]).append(r)
 out=[]
 for (region,port,period),rows in grouped.items():
  values=[D(r['brl_t']) for r in rows];mean=sum(values)/len(values)
  out.append({'region':region,'port':port,'period':period,'n':len(values),'mean_brl_t':str(mean),'mean_brl_sc':str((mean*D('.06')).quantize(D('.01'),rounding=ROUND_HALF_UP)),'min_brl_t':str(min(values)),'max_brl_t':str(max(values))})
 return out
