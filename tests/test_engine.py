import unittest
from unittest.mock import patch
from decimal import Decimal as D
from datetime import date
import engine

class Integrity(unittest.TestCase):
 def test_visual_sum_and_residual(self):
  r=engine.derive({'date':'2026-11-23','port':'Paranaguá','fx':'5.9708','cbot':'12.2875','premium':'1.60','physical_brl_raw':'170.74'})
  self.assertEqual(r['sum'],'182.80');self.assertEqual(r['residual'],'-12.06')
 def test_missing_fx_does_not_create_brl(self):
  r=engine.derive({'date':'2026-11-20','port':'Santos','cbot':'12.075','premium':'1.6','physical_usd_raw':'13.8'})
  self.assertIsNone(r['sum']);self.assertIsNone(r['physical'])
 def test_published_santos_cents(self):
  s={'markets':{'Santos':[]},'warnings':[]}
  payload=b'{"gerado_em":"2026-11-14T01:30:06-03:00","cotacoes":[{"id":"indice-523a846c","data":"2026-11-13","valor":1388.4784124563964,"unidade":"cents/bushel"},{"id":"premio-santos","data":"2026-11-13","valor":156.22841245639643,"unidade":"cents/bushel"}]}'
  with patch('engine.fetch',return_value=payload):engine.fetch_santos(s)
  r=s['markets']['Santos'][0];self.assertEqual(r['date'],'2026-11-13');self.assertEqual(D(r['premium']),D('1.5622841245639643'))
 def test_incompatible_base_blocks_sum(self):
  r=engine.derive({'fx':'5.9','cbot':'12','premium':'1','incompatible_base':True})
  self.assertIsNone(r['sum']);self.assertIsNotNone(r['chicago_brl'])
 def test_revision_trail(self):
  s={'markets':{'Paranaguá':[]}}
  src=engine.source('https://example.org','2026-11-23')
  engine.record(s,'Paranaguá','2026-11-23',{'fx':'5.9'},src);engine.record(s,'Paranaguá','2026-11-23',{'fx':'5.97'},src)
  self.assertEqual(len(s['markets']['Paranaguá']),1);self.assertEqual(s['revisions'][0]['previous'],'5.9')
 def test_b3_record_scope(self):
  xml=b'<root><PricRpt><FinInstrmId><TckrSymb>SJCH27</TckrSymb></FinInstrmId><AdjstdQt Ccy="USD">27.144</AdjstdQt><PrvsAdjstdQt>27.1825</PrvsAdjstdQt></PricRpt></root>'
  self.assertEqual(next(engine.instrument_nodes(xml))['AdjstdQt'],'27.144')
if __name__=='__main__':unittest.main()
