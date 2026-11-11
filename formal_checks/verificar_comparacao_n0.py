"""Teste exaustivo INDEPENDENTE das regras booleanas C2/F1 com contagem de N0.
Nao executa Lean e nao mede trafego MISP nem carga computacional real.
"""
from pathlib import Path
import itertools, csv, json
from collections import Counter

FIELDS = [
    'n0_available','n0_intake_authorized','n0_forward_authorized',
    'sector_relevant','n1_available',
    'international_authorized','international_link_available',
    'n2_available','technically_qualified','n3_available',
    'recipient_authorized','operationally_applicable',
]

out_dir = Path(__file__).resolve().parent / 'resultado'
out_dir.mkdir(exist_ok=True)
rows=[]
assertions=0
stats=Counter()
for values in itertools.product([False,True], repeat=len(FIELDS)):
    q = dict(zip(FIELDS,values))
    central=all(q[k] for k in ('n0_available','n0_intake_authorized',
                'n0_forward_authorized','sector_relevant','n1_available'))
    direct=all(q[k] for k in ('international_authorized',
               'international_link_available','sector_relevant','n1_available'))
    downstream=all(q[k] for k in ('n2_available','technically_qualified',
                  'n3_available','recipient_authorized','operationally_applicable'))
    c2_route='viaN0' if central else 'none'
    f1_route='directN1' if direct else c2_route
    c2_load=int(c2_route=='viaN0')
    f1_load=int(f1_route=='viaN0')
    bypass=int(c2_route=='viaN0' and f1_route=='directN1')
    c2_delivery=central and downstream
    f1_delivery=(central or direct) and downstream
    checks={
      'conservacao_carga_n0':c2_load==f1_load+bypass,
      'f1_nao_aumenta_n0':f1_load<=c2_load,
      'ganho_estrito_com_bypass':not(central and direct) or (c2_load>f1_load),
      'sem_direto_mesma_rota':direct or f1_route==c2_route,
      'preserva_entrega_c2':not c2_delivery or f1_delivery,
      'entrega_f1_exige_qualificacao':not f1_delivery or downstream,
      'n0_indisponivel_sem_rota_c2':q['n0_available'] or not central,
      'n0_down_e_direto_tem_f1':not(not q['n0_available'] and direct) or
               (f1_route=='directN1' and c2_route=='none'),
      'bypass_somente_se_duas_rotas':not bypass or (central and direct),
      'sem_bypass_cargas_iguais':bool(bypass) or f1_load==c2_load,
    }
    assert all(checks.values()), (q, [x for x,v in checks.items() if not v])
    assertions+=len(checks)
    stats['configs']+=1
    if central:stats['c2_routes']+=1
    if direct:stats['direct_eligible']+=1
    if central and direct:stats['eligible_bypasses']+=1
    if not q['n0_available'] and direct:stats['direct_with_n0_down']+=1
    rows.append({**{k:int(v) for k,v in q.items()},
                 'C2_route':c2_route,'F1_route':f1_route,
                 'C2_N0_units':c2_load,'F1_N0_units':f1_load,
                 'N0_avoided_units':bypass,'C2_N3_eligible':int(c2_delivery),
                 'F1_N3_eligible':int(f1_delivery)})

assert stats['configs']==2**len(FIELDS)
with (out_dir/'comparacao_4096_casos.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f, fieldnames=list(rows[0]))
  writer.writeheader(); writer.writerows(rows)

# Independently verify aggregation over finite lists, with different candidate sets.
aggregated_cases=0
for n in range(1,81):
    # sample deterministic, not random or measured MISP flows
    qs=rows[::max(1,4096//n)][:n]
    assert sum(q['C2_N0_units'] for q in qs) == (
        sum(q['F1_N0_units'] for q in qs)+sum(q['N0_avoided_units'] for q in qs))
    aggregated_cases+=1

# External dataset reconciliation: count class assignments in existing matrix.
ref=Path(__file__).resolve().parents[1] / 'evidence' / 'reference' / '04_matriz_comparativa_n1.csv'
if ref.exists():
    c=Counter()
    with ref.open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            c['pairs']+=1
            c['c1']+=int(row['C1_full_distribution'])
            c['c2']+=int(row['C2_central_filtered'])
            c['f1']+=int(row['F1_federated_N1'])
            if row['C2_central_filtered']!=row['F1_federated_N1']:
                c['disagreements']+=1
    assert (c['pairs'],c['c1'],c['c2'],c['f1'],c['disagreements'])==(62832,62832,214,214,0)
    source_counts=dict(c)
else:
    source_counts=None
summary={
 'status':'PYTHON EXECUTADO; LEAN REQUER VERIFICACAO SEPARADA',
 'configuracoes_booleanas':stats['configs'],
 'asserciones_aprovadas':assertions,
 'contraexemplos':0,
 'listas_finitas_agregadas_conferidas':aggregated_cases,
 'distribuicao_no_espaco_de_configuracoes':dict(stats),
 'dados_n1_reconciliados':source_counts,
 'limites':[
   'Enumeracao verifica um modelo declarado, nao transmissao real no MISP.',
   'Contagem de passagens N0, nao CPU, bytes, latencia ou tempo de processamento.',
   'Sem logs de roteamento, quantidade de bypasses reais permanece desconhecida.',
   'Lean 4 precisa compilar o teorema antes de ser citado como prova verificada.'
 ]}
(out_dir/'resumo_validacao.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2), encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
