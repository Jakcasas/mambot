"""Compare operation history with the PR base. Existing operation bytes are immutable."""
import pathlib,subprocess,sys
base=sys.argv[1]
root=pathlib.Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'--','registry'],cwd=root,text=True).splitlines()
for name in files:
    if name.endswith('.json') and not name.endswith('/lock.json'):
        old=subprocess.check_output(['git','show',f'{base}:{name}'],cwd=root)
        path=root/name
        if not path.exists() or path.read_bytes()!=old:
            raise SystemExit(f'Immutable operation modified/deleted: {name}. Add a new version.')
print('PASS: immutable operation history')
