import unittest
from decimal import Decimal as D
from confronto import interval,scenario

class ComparisonIntegrity(unittest.TestCase):
 def pair(self):
  a={'date':'2026-11-20','source':'Binance','btc_brl':'100','fx':'5'}
  b={'date':'2026-11-23','source':'Binance','btc_brl':'120','fx':'5.5'}
  return a,b
 def test_equal_notional_long_short(self):
  a,b=self.pair();r=interval(a,b)
  self.assertEqual(r['long_btc_short_usd_brl'],'100.00')
  self.assertEqual(r['leader'],'Bitcoin');self.assertEqual(r['days'],3)
  self.assertEqual(D(r['spread_pp']),D('10'))
 def test_usd_denomination_is_not_spread(self):
  a,b=self.pair();r=interval(a,b)
  self.assertNotEqual(r['btc_in_usd_return_pct'],r['spread_pp'])
  self.assertAlmostEqual(float(r['btc_in_usd_return_pct']),9.0909090909,places=8)
 def test_dollar_can_lead_with_both_assets_down(self):
  a,b=self.pair();b.update(btc_brl='80',fx='4.75')
  r=interval(a,b);self.assertEqual(r['leader'],'Dólar');self.assertEqual(r['long_btc_short_usd_brl'],'-150.00')
 def test_tie(self):
  a,b=self.pair();b.update(btc_brl='110',fx='5.5')
  self.assertEqual(interval(a,b)['leader'],'Empate')
 def test_no_return_across_provider_change(self):
  a,b=self.pair();b['source']='Bipa';self.assertIsNone(interval(a,b))
 def test_premium_is_only_initial_capital(self):
  a,b=self.pair();r=scenario('21.06',a,b)
  self.assertEqual(r['initial_brl'],'21.06');self.assertEqual(r['difference_brl'],'2.10');self.assertEqual(r['direct_difference_brl'],'2.11')
  self.assertIsNone(scenario('0',a,b));self.assertIsNone(scenario('-1',a,b));self.assertIsNone(scenario(None,a,b))
 def test_date_order(self):
  a,b=self.pair()
  with self.assertRaises(ValueError):interval(b,a)
