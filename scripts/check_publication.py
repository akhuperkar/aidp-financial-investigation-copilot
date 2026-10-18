"""Offline public-package checks. No credentials, network or cloud calls."""
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
errors = []
checks = []

def check(name, condition, detail=''):
    checks.append({'check':name,'passed':bool(condition),'detail':detail})
    if not condition: errors.append(name + (': '+detail if detail else ''))

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        for k,v in attrs:
            if k in ('src','href') and v: self.links.append(v)

def local_target(source, target):
    target = target.strip().strip('<>')
    if target.startswith(('#','data:','mailto:','http:','https:','tel:','javascript:')): return
    target=unquote(urlparse(target).path)
    if not target: return
    if not (source.parent/target).exists(): errors.append(f'Broken local link in {source.relative_to(ROOT)}: {target}')

public_files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git','__pycache__','.venv'))]
notebooks=sorted((ROOT/'notebooks').glob('*.ipynb'))
check('Four runnable notebooks',len(notebooks)==4)
nb={p.name:json.loads(p.read_text()) for p in notebooks}
code_count=0
for p in notebooks:
    for i,c in enumerate(nb[p.name]['cells'],1):
        if c['cell_type']=='code':
            ast.parse(''.join(c['source']),filename=f'{p.name}:cell{i}')
            code_count+=1
            check(f'{p.name}:cell{i}:outputs cleared',c.get('outputs')==[] and c.get('execution_count') is None)
original=nb['financial_services_medallion_architecture_demo.ipynb']
revised=nb['financial_services_medallion_architecture_demo_ailh.ipynb']
check('Original 29 cells preserved in AILH notebook',len(original['cells'])==29 and revised['cells'][:29]==original['cells'])

manifest=json.loads((ROOT/'config/rag_manifest.json').read_text())
check('Eight RAG source documents',len(manifest)==8)
for item in manifest:
    content=(ROOT/'rag_corpus'/item['filename']).read_bytes()
    check(f'RAG hash: {item["filename"]}',hashlib.sha256(content).hexdigest()==item['sha256'])
    check(f'RAG length: {item["filename"]}',len(content)==item['bytes'])
tools=json.loads((ROOT/'config/sql_tools.json').read_text())
check('Seven parameterized SQL tools',len(tools)==7)
for item in tools:
    sql=(ROOT/'sql'/(item['tool_name']+'.sql')).read_text()
    check('SQL file matches registry: '+item['tool_name'],item['query'].strip() in sql)

for p in public_files:
    if p.suffix=='.json': json.loads(p.read_text())
    if p.suffix=='.py': ast.parse(p.read_text(),filename=str(p.relative_to(ROOT)))
    if p.suffix=='.md':
        text=re.sub(r'```[\s\S]*?```','',p.read_text())
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text): local_target(p,target)
    if p.suffix=='.html':
        parser=Links();parser.feed(p.read_text())
        for target in parser.links: local_target(p,target)
    if p.suffix=='.svg':
        svg=ET.fromstring(p.read_text())
        for el in svg.iter():
            for key,value in el.attrib.items():
                if key.rsplit('}',1)[-1]=='href':local_target(p,value)
    if p.name=='secrets.toml':errors.append('Populated secrets file in package')
    if p.suffix in ('.pem','.key','.sqlite','.sqlite3','.db'):errors.append('Private/runtime artifact: '+str(p.relative_to(ROOT)))
    if p.suffix in ('.md','.html','.json','.ipynb','.py','.txt','.toml'):
        text=p.read_text()
        for pattern in [r'/Users/[^/\s]+/', r'https://gateway\.aidp\.[^/\s]+/agentendpoint/(?!00000000)[0-9a-f-]{36}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']:
            # This scanner's own deny-list is allowed; it contains no credentials.
            if p!=Path(__file__).resolve() and re.search(pattern,text):errors.append('Private reference in '+str(p.relative_to(ROOT)))

snapshot=json.loads((ROOT/'data/reference-snapshot.json').read_text())['december_2024']
check('Reference flag-rate arithmetic',abs(snapshot['rule_flags']/snapshot['transactions']*100-snapshot['flag_rate_pct'])<1e-10)
check('Reference concentration arithmetic',abs(snapshot['top10_flagged_gross']/snapshot['flagged_gross']*100-snapshot['top10_share_pct'])<1e-10)
check('Reference gross/net bounds',0<=snapshot['flagged_gross']<=snapshot['gross_activity'] and abs(snapshot['net_activity'])<=snapshot['gross_activity'])
slides=ROOT/'slides/aidp-financial-investigation-copilot.pptx'
check('PowerPoint present',slides.exists())
if slides.exists():
    with ZipFile(slides) as z:
        slide_xml=[x for x in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',x)]
        check('PowerPoint has 10 slides',len(slide_xml)==10)
        a={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
        texts=[]
        for n in slide_xml:
            root=ET.fromstring(z.read(n));texts.extend(x.text or '' for x in root.findall('.//a:t',a))
        check('No template confidentiality residue',not any('confidential - internal' in x.lower() for x in texts))
        check('Native table on slide 5',b'<a:tbl>' in z.read('ppt/slides/slide5.xml'))
        for number in (3,7):
            root=ET.fromstring(z.read(f'ppt/slides/slide{number}.xml'))
            ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
            check(f'Editable diagram on slide {number}',len(root.findall('.//p:sp',ns))>=15 and len(root.findall('.//p:cxnSp',ns))>=4)

video=ROOT/'video/final/aidp-financial-investigation-copilot.mp4'
check('Video delivery state',not video.exists() or (video.stat().st_size>1024 and b'ftyp' in video.open('rb').read(32)),'Pending recording is valid; a supplied master must have a real MP4 header. Use ffprobe for final media acceptance.')
package_manifest=ROOT/'data/package-manifest.json'
if package_manifest.exists():
    for item in json.loads(package_manifest.read_text())['files']:
        p=ROOT/item['path']
        check('Packaged file hash: '+item['path'],p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'])
report={'scope':'offline artifact structure, links, public hygiene and metric contracts; no hosted execution',
        'status':'PASS' if not errors else 'FAIL','files_checked':len(public_files),'code_cells_compiled':code_count,
        'checks':checks,'errors':errors}
destination=ROOT/'validation/structure-checks.json'
destination.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','files_checked','code_cells_compiled','errors')},indent=2))
sys.exit(bool(errors))
