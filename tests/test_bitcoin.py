import unittest,json
from datetime import date
from decimal import Decimal as D
from copy import deepcopy
import bitcoin,engine

class BitcoinIntegrity(unittest.TestCase):
 def observation(self,day,price):
  return {'date':day,'price_brl':price,'source_url':'https://mcp.bipa.app/mcp','observed_at':day+'T23:59:00-03:00','consulted_at':'2026-11-24T12:00:00-03:00','nature':'daily_reference','method':'FIXTURE sintética de teste; não é cotação'}
 def report(self):
  rows=[engine.derive({'date':'2026-11-23','physical_brl_raw':'170.74','fx':'5.9708','cbot':'12.2875','premium':'1.60'})]
  return {'edition':'2026-11-24','window_start':'2026-10-26','window_end':'2026-11-24','rows':{'Paranaguá':rows},'latest':{'Paranaguá':rows[0]},'futures':[],'options':[],'five':[],'quality':{'checks':0,'passed':0,'failed':0}}
 def test_dimensions(self):
  self.assertEqual(bitcoin.sats('150','500000'),'30000.00')
  self.assertEqual(bitcoin.sats('5','500000'),'1000.00')
 def test_same_date_required(self):
  r=bitcoin.enrich(self.report(),[self.observation('2026-11-22','500000')])
  self.assertIsNone(r['rows']['Paranaguá'][0]['bitcoin']['physical'])
 def test_visual_sum_closes(self):
  r=bitcoin.enrich(self.report(),[self.observation('2026-11-23','567891.123')])['rows']['Paranaguá'][0]['bitcoin']
  self.assertEqual(D(r['sum']),D(r['chicago_brl'])+D(r['premium_brl']))
  self.assertEqual(D(r['residual']),D(r['physical'])-D(r['sum']))
 def test_bipa_validation(self):
  obs=self.observation('2026-11-23','500000')
  for key,value in [('price_brl','0'),('price_brl','NaN'),('source_url','https://example.org'),('observed_at','2026-11-22T23:59:00-03:00'),('nature','intraday')]:
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):bitcoin.validate_observation({**obs,key:value},date(2026,11,24))
 def test_no_fabricated_bitcoin_history(self):
  r=bitcoin.enrich(self.report(),[])
  self.assertEqual(r['bitcoin']['comparison'],[]);self.assertEqual(r['bitcoin']['soy']['Paranaguá'],[])
  json.dumps(r)
 def test_divergence(self):
  r=self.report();row=engine.derive({'date':'2026-11-22','fx':'5','physical_brl_raw':'150'})
  r['rows']['Paranaguá'].insert(0,row)
  out=bitcoin.enrich(r,[self.observation('2026-11-22','500000'),self.observation('2026-11-23','600000')])
  expected=(D('1.2')/(D('5.9708')/5)-1)*100
  self.assertEqual(D(out['bitcoin']['comparison'][-1]['divergence_pct']),expected)
if __name__=='__main__':unittest.main()

class FallbackIntegrity(unittest.TestCase):
 def test_bipa_preferred_without_erasing_binance(self):
  base=BitcoinIntegrity();r=base.report();a=base.observation('2026-11-23','500000');b={**a,'price_brl':'600000','source_url':'https://data-api.binance.vision/api/v3/klines?symbol=BTCBRL'}
  out=bitcoin.enrich(r,[a],[b]);self.assertEqual(out['rows']['Paranaguá'][0]['bitcoin']['btc_brl'],'500000');self.assertEqual(out['rows']['Paranaguá'][0]['bitcoin']['reference']['source'],'Bipa')
 def test_binance_keeps_its_name(self):
  base=BitcoinIntegrity();a={**base.observation('2026-11-23','500000'),'source_url':'https://data-api.binance.vision/api/v3/klines?symbol=BTCBRL'}
  out=bitcoin.enrich(base.report(),[],[a]);self.assertEqual(out['bitcoin']['observations'][0]['source'],'Binance')
 def test_monthly_freight_mean_and_units(self):
  from freight import groups
  rs=[{'region':'R','port':'Santos','period':'2026-09','brl_t':'200'},{'region':'R','port':'Santos','period':'2026-09','brl_t':'300'},{'region':'R','port':'Paranaguá','period':'2026-09','brl_t':'500'}]
  a=groups(rs);self.assertEqual(a[0]['n'],2);self.assertEqual(a[0]['mean_brl_sc'],'15.00');self.assertEqual(a[1]['n'],1)
 def test_binance_closed_candle_only(self):
  from unittest.mock import patch
  from datetime import datetime,timedelta
  now=datetime.now(engine.TZ);today=now.date();yday=today-timedelta(days=1)
  def candle(d):
   start=int(datetime.combine(d,datetime.min.time(),engine.TZ).timestamp()*1000)
   return [start,'500000','500000','500000','500000','1',start+86399999,'1',1,'1','1','0']
  payload=json.dumps([candle(yday),candle(today)]).encode();state={}
  with patch('engine.fetch',return_value=payload):engine.fetch_binance(state)
  self.assertEqual([r['date'] for r in state['bitcoin_binance']],[yday.isoformat()])
