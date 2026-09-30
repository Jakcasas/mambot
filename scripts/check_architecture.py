"""Release gate for the concrete LTX boundaries used in this repository.

Static checks are defense in depth, not a sandbox for arbitrary hostile Python/JS.
"""
import ast
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def violations(root=ROOT):
    errors=[]
    def fail(path,reason): errors.append(f'{path.relative_to(root)}: {reason}')
    front=root/'static'
    for path in front.rglob('*'):
        if path.suffix not in ('.js','.html'): continue
        text=path.read_text(encoding='utf-8')
        relative=path.relative_to(front).as_posix()
        if relative!='js/shared/http.js' and re.search(r'\b(fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|axios)\b',text):
            fail(path,'Transport is allowed only in shared/http.js')
        if re.search(r'[\'\"][^\'\"\s]*\bapi/',text) and not path.name.endswith('.api.js'):
            fail(path,'Endpoint definitions belong to feature API modules')
        if re.search(r'MongoClient|ObjectId|\$vectorSearch|huit_kb|mongodb\+srv',text):
            fail(path,'Database implementation leaked to frontend')
        if path.suffix=='.html' and re.search(r'<script(?![^>]*\bsrc=)[^>]*>\s*\S',text,re.I):
            fail(path,'Inline executable scripts are not allowed')
        if path.suffix!='.js': continue
        imports=re.findall(r'\bfrom\s*[\'\"]([^\'\"]+)[\'\"]',text)
        if re.search(r'\bimport\s*\(|\beval\s*\(|new\s+Function\b',text): fail(path,'Dynamic code loading requires review')
        for spec in imports:
            resolved=(path.parent/spec).resolve()
            if not resolved.is_relative_to(front.resolve()): fail(path,'Import leaves frontend boundary'); continue
            if not resolved.is_file(): fail(path,'Import target is missing'); continue
            if path.name.endswith('.view.js') and not spec.endswith('.controller.js'):
                fail(path,'View may import domain controllers only')
            elif path.name.endswith('.controller.js') and (not spec.endswith('.api.js') or resolved.parent!=path.parent):
                fail(path,'Controller may import its domain API only')
            elif path.name.endswith('.api.js') and resolved!=(front/'js/shared/http.js').resolve():
                fail(path,'Feature API must point to shared HTTP')
            elif '/shared/' in path.as_posix(): fail(path,'Shared transport cannot import features')
        if path.name.endswith(('.controller.js','.api.js')) and re.search(r'\bdocument\b|querySelector|innerHTML',text):
            fail(path,'Domain/API layer cannot access the DOM')
    allowed={
        'routes':{'services','errors'}, 'services':{'operations','domain','infrastructure','errors','config'},
        'operations':{'db','infrastructure','errors','config'}, 'db':{'db','errors','config'},
        'domain':{'domain','errors'}, 'infrastructure':{'infrastructure','errors','config'}
    }
    forbidden_calls={'find','find_one','aggregate','insert_one','update_one','update_many','delete_many','collection'}
    for path in (root/'backend').rglob('*.py'):
        text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
        layer=path.relative_to(root/'backend').parts[0]
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[node.module or ''] if isinstance(node,ast.ImportFrom) else [n.name for n in node.names]
                for name in names:
                    if name.startswith('backend.') and layer in allowed and name.split('.')[1] not in allowed[layer]:
                        fail(path,f'Forbidden dependency: {layer} -> {name}')
                    if name.startswith('pymongo') and path!=(root/'backend/db/store.py'):
                        fail(path,'Driver imports belong to db/store.py')
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                if name in ('eval','exec','__import__'): fail(path,'Dynamic execution is forbidden')
                if layer in ('routes','services') and name in forbidden_calls:
                    fail(path,'Route/service reaches through data boundary')
        if layer in ('routes','services') and re.search(r'MongoClient|ObjectId|huit_kb|\$(?:match|project|group|lookup|vectorSearch)',text):
            fail(path,'Database implementation in route/service')
    return errors

if __name__=='__main__':
    found=violations()
    print('\n'.join(found) if found else 'PASS: LTX architecture boundaries')
    raise SystemExit(bool(found))
