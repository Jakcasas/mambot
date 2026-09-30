"""Run release gates, including frontend lifecycle tests. Node 20+ is required."""
import os
import pathlib
import shutil
import subprocess
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
env=dict(os.environ);env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH','');env['PYTHONUTF8']='1'
commands=[[sys.executable,'scripts/check_architecture.py'],[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v']]
node=shutil.which('node')
if not node:
    raise SystemExit('Node.js 20+ is required to verify frontend contracts. Python alone can run the app.')
commands.append([node,'tests/frontend.test.mjs'])
for command in commands:
    result=subprocess.run(command,env=env)
    if result.returncode:raise SystemExit(result.returncode)
print('PASS: all Mambot release gates')
