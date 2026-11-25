"""Importe somente preços de mercado exportados da Bipa, sem dados pessoais."""
import argparse,json,sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bitcoin import validate_observation
from engine import save

def main():
 p=argparse.ArgumentParser();p.add_argument('input');args=p.parse_args()
 today=datetime.now(ZoneInfo('America/Sao_Paulo')).date()
 incoming=json.loads(Path(args.input).read_text())
 if not isinstance(incoming,list):raise ValueError('Esperada lista de observações')
 clean=[validate_observation(x,today) for x in incoming]
 if len({x['date'] for x in clean})!=len(clean):raise ValueError('Datas duplicadas no lote')
 target=ROOT/'data/bipa_prices.json';revision=ROOT/'data/bipa_revisions.json'
 existing={x['date']:x for x in json.loads(target.read_text())}
 changes=json.loads(revision.read_text()) if revision.exists() else []
 for item in clean:
  old=existing.get(item['date'])
  if old is not None and old!=item:changes.append({'at':datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),'previous':old,'new':item,'reason':'nova exportação Bipa, revisão documentada'})
  existing[item['date']]=item
 # Save revision trail first: an interrupted import cannot erase its evidence.
 save(revision,changes);save(target,[existing[d] for d in sorted(existing)])
 print(f'{len(clean)} referências validadas; {len(changes)} revisões preservadas')
if __name__=='__main__':main()
