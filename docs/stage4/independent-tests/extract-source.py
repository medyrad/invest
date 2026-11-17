"""Independent static extraction from the original ZIP; no reference code execution."""
import hashlib,json,re,zipfile,pathlib
root=pathlib.Path(__file__).resolve().parents[3]
archive=pathlib.Path('/home/mehdirad/Documents/product-management/Investment_Advisor-main.zip')
with zipfile.ZipFile(archive) as z:
 def read(tail):
  names=[n for n in z.namelist() if n.endswith('/'+tail)]
  assert len(names)==1,(tail,len(names))
  return z.read(names[0]).decode()
 def array(text,name):
  tail=re.split(r'export const '+name+r'[^=]*=',text,maxsplit=1)[1].lstrip()
  if name=='provinces':tail=re.sub(r',\s*\]',']',tail,count=1)
  return json.JSONDecoder().raw_decode(tail)[0]
 groups=array(read('src/data/taxonomy.ts'),'projectGroups');names=array(read('src/data/provinces.ts'),'provinces');provinces=[]
 for i,name in enumerate(names):
  counties=array(read(f'src/data/counties/c{i:02d}.ts'),'counties')
  provinces.append({'id':f'province-{i:02d}','name':name,'counties':[{'id':f'county-{i:02d}-{j:03d}','name':c['name'],'cities':[{'id':f'county-{i:02d}-{j:03d}.city-{k}','name':city} for k,city in enumerate(c['cities'])]} for j,c in enumerate(counties)]})
expected={'groups':groups,'provinces':provinces}
(root/'docs/stage4/independent-evidence/source-expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
summary={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'counts':{'groups':len(groups),'subtypes':sum(len(g['subtypes']) for g in groups),'provinces':len(provinces),'counties':sum(len(p['counties']) for p in provinces),'city_links':sum(len(c['cities']) for p in provinces for c in p['counties'])}}
(root/'docs/stage4/independent-evidence/source-extraction.json').write_text(json.dumps(summary,indent=2));print(summary)
