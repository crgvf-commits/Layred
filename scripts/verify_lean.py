#!/usr/bin/env python3
"""Compile ten-theorem Lean source and reject any sorryAx in the axiom audit."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

R=Path(__file__).resolve().parents[1]
L=R/'lean'
model=L/'Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean'
src=model.read_text(encoding='utf-8')
expected=[
 'centralized_vs_federated',
 'federated_operational_path_when_n0_unavailable',
 'single_request_decomposition',
 'n0_load_decomposition',
 'federated_n0_not_greater',
 'federated_n0_strictly_less_if_bypass',
 'strictly_less_with_eligible_direct_request',
 'no_direct_same_route',
 'no_direct_same_n0_work',
 'route_available_without_n0'
]
for name in expected:
    assert re.search(r'\btheorem\s+'+name+r'\b',src), f'Missing theorem: {name}'
    assert '#print axioms WorldCIST27.'+name in src, f'Missing axiom audit: {name}'
lean=shutil.which('lean')
if lean is None:
    print('LEAN NOT RUN: executable not installed. Install elan/Lean and pinned toolchain from lean/lean-toolchain.',file=sys.stderr)
    sys.exit(2)
version=subprocess.run([lean,'--version'],capture_output=True,text=True,check=True).stdout.strip()
expected_pin=(L/'lean-toolchain').read_text(encoding='utf-8').strip().split(':')[-1].lstrip('v')
print('Compiler:',version)
print('Project toolchain pin:',expected_pin)
if expected_pin not in version:
    print('WARNING: compiler version does not match project pin; results may not be reproducible.',file=sys.stderr)
p=subprocess.run([lean,model.name],cwd=L,text=True,capture_output=True)
print(p.stdout)
if p.stderr: print(p.stderr,file=sys.stderr)
if p.returncode!=0:
    print('Lean compilation FAILED',file=sys.stderr);sys.exit(p.returncode)
if 'sorryAx' in p.stdout or 'sorryAx' in p.stderr:
    print('Lean axiom audit FAILED: sorryAx found',file=sys.stderr);sys.exit(1)
for name in expected:
    if name not in p.stdout:
        print(f'WARNING: no output from axiom check {name}',file=sys.stderr)
print(f'LEAN CHECK PASSED: {len(expected)} theorem declarations; compilation successful; no sorryAx in output')
