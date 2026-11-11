#!/usr/bin/env python3
"""Auditoria independente dos CSVs gerados (sem importar o roteador)."""
import csv, json
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parent

def read(filename):
    with (R/'resultado'/filename).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

cases=read('02_comparacao_controlada_revisada.csv')
assert len(cases)==8
assert [(r['scenario_id'],r['target_domain']) for r in cases]==[
  ('S1','TRA'),('S2','TRA'),('S3','TEL'),('S4','FIN'),('S5','TRA'),('S5','TEL'),('S6','GOV'),('S7','HLT')]
assert [int(x['C2_path_edges']) for x in cases]==[4,0,3,2,4,4,0,3]
assert [int(x['F1_path_edges']) for x in cases]==[3,0,2,2,3,4,0,3]
assert sum(int(x['C2_path_edges']) for x in cases)==20
assert sum(int(x['F1_path_edges']) for x in cases)==17
assert sum(int(x['path_difference']) for x in cases)==3
assert sum(int(x['C2_N3_delivery']) for x in cases)==4
assert sum(int(x['F1_N3_delivery']) for x in cases)==4
assert all(x['C2_N3_delivery']==x['F1_N3_delivery'] for x in cases)
assert all(x['C2_path_edges']==x['F1_path_edges'] for x in cases if x['source_type']=='domestic')

unique=read('03_enlaces_unicos_por_cenario.csv')
assert len(unique)==7
assert sum(int(r['C2_unique_directed_edges']) for r in unique)==19
assert sum(int(r['F1_unique_directed_edges']) for r in unique)==16

variants=read('04_sensibilidade_disponibilidade_rota_direta.csv')
assert len(variants)==8
assert [(int(r['C2_path_edges']),int(r['F1_path_edges']),int(r['F1_fewer_edges'])) for r in variants]==[
    (20,20,0),(20,19,1),(20,19,1),(20,18,2),
    (20,19,1),(20,18,2),(20,18,2),(20,17,3)]
assert all(int(r['C2_N3_delivery'])==int(r['F1_N3_delivery'])==4 for r in variants)

summary=json.loads((R/'resultado/05_resultados_consolidados.json').read_text(encoding='utf-8'))
assert summary['finite_enumeration']['configurations']==2048
assert summary['finite_enumeration']['assertions_checked']==18432
assert summary['finite_enumeration']['assertions_failed']==0
print('AUDITORIA INDEPENDENTE DOS RESULTADOS: PASSOU')
print('C2=20, F1=17, entregas modeladas=4, sensibilidade=8, enumeração=2048')
