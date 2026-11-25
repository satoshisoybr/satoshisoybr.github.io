from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'codigo-aberto.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in sorted(ROOT.rglob('*')):
  rel=p.relative_to(ROOT)
  if not p.is_file() or p==target or any(x in rel.parts for x in ['.git','.openai','__pycache__','node_modules','.venv']):continue
  if p.name.startswith('.env') or p.suffix=='.pyc':continue
  z.write(p,'satoshisoybr/'+str(rel))
print(target)
