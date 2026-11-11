#!/usr/bin/env python3
"""Reproduce corpus and experiment outputs in fresh temporary folders.

Independent from the plotting/experiment implementation in its output checks.
A successful Python run does NOT certify the Lean file: compile it separately.
"""
from pathlib import Path
import tempfile
import subprocess
import shutil
import csv
import json
import hashlib
import sys

ROOT=Path(__file__).resolve().parents[1]

def run(*cmd):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd],check=True)

def rows(path):
    with open(path,encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def assert_equal_csvs(regenerated, reference):
    expected = sorted(p.name for p in reference.glob('*.csv'))
    assert expected, f'No CSV outputs found in {reference}'
    for name in expected:
        actual=regenerated/name
        assert actual.exists(), f'Missing regenerated {name}'
        assert sha(actual)==sha(reference/name), f'CSV mismatch: {name}'
    return len(expected)

with tempfile.TemporaryDirectory(prefix='worldcist27-repro-') as td:
    t=Path(td)
    print('\n=== 1. Reproduce corpus evidence ===',flush=True)
    ev_out=t/'evidence_output'
    run(sys.executable,ROOT/'evidence/scripts/gerar_evidencias.py',
        ROOT/'evidence/input/cti_workbooks_original.zip',ev_out)
    ev_csvs=assert_equal_csvs(ev_out,ROOT/'evidence/reference')
    summary=json.loads((ev_out/'07_resumo_evidencias.json').read_text(encoding='utf-8'))
    evidence_facts={'inventory_records':7854,'n1_assigned_records':181,
                    'n1_associations':214,'n1_unresolved_records':7673,
                    'n1_multi_domain_records':21,
                    'c1_full_distribution_N1_pairs':62832,
                    'c2_central_filtered_N1_pairs':214,
                    'f1_federated_N1_pairs':214}
    for key,expected in evidence_facts.items():
        assert summary[key]==expected, f'Corpus result {key}={summary[key]} != {expected}'
    assert summary['tests_failed']==[], f"Corpus integrity check failed: {summary['tests_failed']}"
    print(f'PASS: {ev_csvs} corpus CSV snapshots; {summary["tests_passed"]} integrity assertions',flush=True)

    print('\n=== 2. Reproduce corrected controlled experiment ===',flush=True)
    exp=t/'experiment02'
    shutil.copytree(ROOT/'experiment02/data',exp/'dados')
    for f in (ROOT/'experiment02/scripts').glob('*.py'):
        shutil.copy2(f,exp/f.name)
    run(sys.executable,exp/'rodar_experimento_revisado.py')
    run(sys.executable,exp/'testar_resultados.py')
    ex_csvs=assert_equal_csvs(exp/'resultado',ROOT/'experiment02/reference')
    actual=json.loads((exp/'resultado/05_resultados_consolidados.json').read_text(encoding='utf-8'))
    expected=json.loads((ROOT/'experiment02/reference/05_resultados_consolidados.json').read_text(encoding='utf-8'))
    assert actual==expected,'Corrected experiment JSON summary does not match the archived reference'
    key=actual['corrected_fair_comparison']
    assert (key['C2_path_edges'],key['F1_path_edges'],key['difference'])==(20,17,3)
    assert actual['scenario_cases']['modelled_allowed_n3_deliveries_per_policy']==4
    finite=actual['finite_enumeration']
    assert (finite['configurations'],finite['assertions_checked'],finite['assertions_failed'])==(2048,18432,0)
    print(f'PASS: {ex_csvs} experiment CSV snapshots, 20 vs 17 and finite model cross-check',flush=True)

    print('\n=== 3. Independent finite cross-check of the Lean-type policy ===',flush=True)
    formal=t/'formal_checks'
    (formal/'resultado').mkdir(parents=True)
    shutil.copy2(ROOT/'formal_checks/verificar_comparacao_n0.py',formal/'verificar_comparacao_n0.py')
    # Preserve the checked-out relative layout used by the original standalone script.
    (t/'evidence/reference').mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'evidence/reference/04_matriz_comparativa_n1.csv',
                 t/'evidence/reference/04_matriz_comparativa_n1.csv')
    run(sys.executable,formal/'verificar_comparacao_n0.py')
    formal_summary=json.loads((formal/'resultado/resumo_validacao.json').read_text(encoding='utf-8'))
    assert (formal_summary['configuracoes_booleanas'],formal_summary['asserciones_aprovadas'],
            formal_summary['contraexemplos'],formal_summary['listas_finitas_agregadas_conferidas'])==(4096,40960,0,80)
    assert sha(formal/'resultado/comparacao_4096_casos.csv')==sha(ROOT/'formal_checks/reference/comparacao_4096_casos.csv')
    print('PASS: 4,096 configurations; 40,960 assertions; 80 list-level aggregates',flush=True)

print('\nALL PYTHON REPRODUCIBILITY CHECKS PASSED.',flush=True)
print('Lean 4 is a separate compiler check: see lean/README.md.',flush=True)
