#!/usr/bin/env python3
"""Reexecuta o Experimento 02 com baseline centralizado conservador.

C2: ingresso internacional por N0, com encaminhamento direto N0->N1:destino;
    ingresso domestico direto ao N1 de entrada, sem exigir N0;
    mesmas autorizacoes e criterios em C2 e F1.
F1: rotas iguais a C2 quando nao houver ingresso internacional direto elegivel;
    nos cenarios que o admitem, Source->N1:entrada e, se autorizado,
    N1:entrada->N1:destino. N0 permanece como fallback.

Metricas: ocorrencias de arestas nos caminhos logicos por destinatario;
          arestas unicas dentro de cada cenario, como verificacao complementar.
Nao sao trafego MISP nem medidas operacionais.
"""
from __future__ import annotations
import csv, hashlib, json, itertools, shutil, zipfile
from pathlib import Path
from collections import defaultdict, Counter

DEST = Path(__file__).resolve().parent
SOURCE = DEST
DATA = DEST / 'dados'; RESULTS = DEST / 'resultado'; FIGS = DEST / 'figuras'; MANUSCRIPT = DEST / 'manuscrito'
for p in (DATA, RESULTS, FIGS, MANUSCRIPT): p.mkdir(parents=True,exist_ok=True)
for name in ('cenarios_controlados.json','matriz_n1_auditada.csv','associacoes_n1_auditadas.csv'):
    original = SOURCE/'dados'/name
    target = DATA/name
    if original.resolve() != target.resolve():
        shutil.copy2(original, target)

scenarios = json.loads((DATA/'cenarios_controlados.json').read_text(encoding='utf-8'))
assert len(scenarios)==7 and len({s['id'] for s in scenarios})==7

# As mesmas rotas internacionais diretas assumidas anteriormente para F1, agora
# declaradas explicitamente e testadas tambem na condicao de AUSENCIA de rota.
assumptions = {
    'description': 'Disponibilidade/autorizacao de rota direta internacional no ENSAIO SINTETICO (nao observada em MISP).',
    'direct_available_default': {'S1':True,'S2':False,'S3':True,'S4':False,'S5':True,'S6':False,'S7':False},
    'central_domestic_can_enter_N1_directly': True,
    'central_international_forwards_from_N0_to_authorized_target_N1': True,
    'central_cross_sector_permission_same_as_federated': True,
    'federated_prefers_direct_international_when_eligible': True,
    'fallback_to_N0_if_no_direct': True,
    'comparison_scope': 'centralized selective C2 with mandatory N0 only for international ingress; not every possible centralized policy',
    'meaning_of_link': 'one directed edge on one modeled source-to-target conceptual path, including unsuccessful N2 qualification if N1 accepted',
    'what_is_not_measured': ['MISP operational forwarding', 'traffic bytes', 'latency', 'CPU', 'actual authorization', 'independent N2/N3 correctness']
}
(DATA/'hipoteses_de_roteamento.json').write_text(json.dumps(assumptions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Audit only the original N1 eligibility counts, not independent ground truth.
with (DATA/'matriz_n1_auditada.csv').open(encoding='utf-8',newline='') as fh:
    reader=csv.DictReader(fh)
    counts=Counter(); record_ids=set(); domains=set(); mismatches=0
    for row in reader:
        counts['pairs']+=1
        record_ids.add(row['Record_ID']); domains.add(row['Domain'])
        counts['c2']+=int(row['C2_central_filtered'])
        counts['f1']+=int(row['F1_federated_N1'])
        mismatches+=row['C2_central_filtered']!=row['F1_federated_N1']
assert (counts['pairs'],len(record_ids),len(domains),counts['c2'],counts['f1'],mismatches)==(62832,7854,8,214,214,0)


def make_result(s, target, policy, direct_available, n0_available=True):
    source = 'InternationalSource' if s['international'] else 'DomesticSource'
    entry=s['entry_domain']
    cross=target != entry
    evidence=target in s['evidence_domains']
    entry_auth=bool(s['entry_authorized'])
    recipient_auth=target in s['authorized_domains']
    horiz=(not cross) or bool(s['horizontal_authorized'])
    n1_eligible=evidence and entry_auth and recipient_auth and horiz
    n2_eligible=n1_eligible and (target in s['n2_qualified_domains'])
    n3_eligible=n2_eligible and (target in s['n3_authorized_domains']) and (target in s['n3_applicable_domains'])

    if not n1_eligible:
        path=[source]
        selected='REJECTED_BY_N1_POLICY'
        n3_delivery=False
    else:
        if not s['international']:
            # Avoid making a domestic event go through N0 just because it is centralized.
            path=[source,f'N1:{entry}']
            if cross: path.append(f'N1:{target}')
            selected='DOMESTIC_N1'
        elif policy=='F1' and direct_available:
            path=[source,f'N1:{entry}']
            if cross: path.append(f'N1:{target}')
            selected='DIRECT_INTERNATIONAL'
        elif n0_available:
            # Fairer C2: N0 forwards to the ALREADY AUTHORIZED destination domain.
            # It need not traverse N1:entry and return to N0 before N1:target.
            path=[source,'N0',f'N1:{target}']
            selected='CENTRAL_N0'
        else:
            path=[source]
            selected='BLOCKED_N0_UNAVAILABLE'

        if len(path)>1:
            path.append(f'N2:{target}')
            if n3_eligible: path.append(f'N3:{target}')
            n3_delivery=n3_eligible
        else:
            n3_delivery=False

    return dict(scenario_id=s['id'], target_domain=target,
                source_type='international' if s['international'] else 'domestic',
                policy=policy,direct_available_assumed=int(bool(direct_available)),
                n0_available=int(n0_available),
                n1_eligible=int(n1_eligible), n2_eligible=int(n2_eligible),
                n3_delivery=int(n3_delivery),
                selected_route=selected,path=' > '.join(path),
                path_nodes=path, path_edges=max(0,len(path)-1))


def write_csv(path, data, cols):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader(); writer.writerows(data)


def compare_scenarios(direct_flags, n0_available=True):
    routes=[]; comparisons=[]
    for s in scenarios:
        flag=bool(direct_flags.get(s['id'], False)) and bool(s['international'])
        for target in s['target_domains']:
            c=make_result(s,target,'C2',False,n0_available)
            f=make_result(s,target,'F1',flag,n0_available)
            routes.extend([c,f])
            assert c['n1_eligible']==f['n1_eligible']
            assert c['n2_eligible']==f['n2_eligible']
            if n0_available:
                assert c['n3_delivery']==f['n3_delivery']
                assert f['path_edges']<=c['path_edges']
            comparisons.append({'scenario_id':s['id'],'target_domain':target,
                'source_type':c['source_type'],
                'direct_available_assumed':int(flag),
                'C2_path_edges':c['path_edges'], 'F1_path_edges':f['path_edges'],
                'C2_N3_delivery':c['n3_delivery'], 'F1_N3_delivery':f['n3_delivery'],
                'path_difference':c['path_edges']-f['path_edges']})
    return routes, comparisons

routes, comps = compare_scenarios(assumptions['direct_available_default'])
comparison_fields=list(comps[0])
route_fields=[k for k in routes[0] if k!='path_nodes']
write_csv(RESULTS/'01_rotas_c2_f1_revisadas.csv',routes,route_fields)
write_csv(RESULTS/'02_comparacao_controlada_revisada.csv',comps,comparison_fields)

sums={k:sum(row[k] for row in comps) for k in ('C2_path_edges','F1_path_edges','C2_N3_delivery','F1_N3_delivery','path_difference')}
assert sums=={'C2_path_edges':20,'F1_path_edges':17,'C2_N3_delivery':4,'F1_N3_delivery':4,'path_difference':3}, sums

# Unique directed edges per scenario, preventing S5 shared ingress from being counted twice.
unique=[]
for s in scenarios:
    row={'scenario_id':s['id']}
    for policy in ('C2','F1'):
        edges=set()
        for r in routes:
            if r['scenario_id'] !=s['id'] or r['policy'] !=policy: continue
            edges.update(zip(r['path_nodes'],r['path_nodes'][1:]))
        row[f'{policy}_unique_directed_edges']=len(edges)
    row['difference']=row['C2_unique_directed_edges']-row['F1_unique_directed_edges']
    unique.append(row)
write_csv(RESULTS/'03_enlaces_unicos_por_cenario.csv',unique,list(unique[0]))
assert sum(x['C2_unique_directed_edges'] for x in unique)==19
assert sum(x['F1_unique_directed_edges'] for x in unique)==16

# Sensitivity: all 2^3 assumptions regarding available direct ingress, not arbitrary %.
flags=['S1','S3','S5']
sensitivity=[]
for bits in itertools.product((False,True),repeat=3):
    f=dict(zip(flags,bits))
    _, c=compare_scenarios(f)
    total_c=sum(v['C2_path_edges'] for v in c)
    total_f=sum(v['F1_path_edges'] for v in c)
    sensitivity.append({'S1_direct':int(bits[0]),'S3_direct':int(bits[1]),'S5_direct':int(bits[2]),
                        'C2_path_edges':total_c,'F1_path_edges':total_f,
                        'F1_fewer_edges':total_c-total_f,
                        'C2_N3_delivery':sum(v['C2_N3_delivery'] for v in c),
                        'F1_N3_delivery':sum(v['F1_N3_delivery'] for v in c)})
assert sensitivity[0]['F1_fewer_edges']==0 and sensitivity[-1]['F1_fewer_edges']==3
assert all(r['C2_path_edges']==20 and r['C2_N3_delivery']==4 and r['F1_N3_delivery']==4 for r in sensitivity)
write_csv(RESULTS/'04_sensibilidade_disponibilidade_rota_direta.csv',sensitivity,list(sensitivity[0]))

# Independent finite enumeration: 9 original booleans PLUS a 10th explicit
# direct international ingress flag, for N0 available and unavailable.
passes=Counter(); failures=[]; mode_effect=Counter()
for n0_available in (True,False):
    for bitset in itertools.product((False,True),repeat=10):
        intl, cross, evidence, entry_auth, recipient_auth, horizontal_auth, n2q, n3auth, n3app, direct=bitset
        entry='TRA'; target='TEL' if cross else 'TRA'
        scenario={'id':'E','international':intl,'entry_domain':entry,'target_domains':[target],
            'evidence_domains':[target] if evidence else [],'entry_authorized':entry_auth,
            'authorized_domains':[target] if recipient_auth else [],
            'horizontal_authorized':horizontal_auth,
            'n2_qualified_domains':[target] if n2q else [],
            'n3_authorized_domains':[target] if n3auth else [],
            'n3_applicable_domains':[target] if n3app else []}
        c=make_result(scenario,target,'C2',False,n0_available)
        f=make_result(scenario,target,'F1',direct,n0_available)
        base_n1=evidence and entry_auth and recipient_auth and (not cross or horizontal_auth)
        expected_n3=base_n1 and n2q and n3auth and n3app
        checks={'same_policy_gates':(c['n1_eligible']==f['n1_eligible']==int(base_n1)),
            'no_unauthorized_delivery':(not c['n3_delivery'] or expected_n3) and (not f['n3_delivery'] or expected_n3),
            'central_delivery_subset_federated':(not c['n3_delivery']) or bool(f['n3_delivery']),
            'n0_fallback_same_without_direct':(not intl or not direct) is False or c['path']==f['path'],
            'domestic_same_path':intl or c['path']==f['path'],
            'N0_available_same_delivery':(not n0_available) or (c['n3_delivery']==f['n3_delivery']),
            'N0_available_F1_no_more_edges':(not n0_available) or f['path_edges']<=c['path_edges'],
            'N0_unavailable_central_no_international_delivery':(n0_available or not intl) or c['n3_delivery']==0,
            'direct_not_selected_without_authorization':(not f['n1_eligible']) is False or f['selected_route']!='DIRECT_INTERNATIONAL',
        }
        mode_effect['all_cases']+=1
        if f['path_edges'] < c['path_edges']: mode_effect['shorter_federated']+=1
        if f['n3_delivery'] and not c['n3_delivery']:mode_effect['fed_extra_deliveries_when_n0_down']+=1
        for check,passed in checks.items():
            passes['assertions_total']+=1
            if passed: passes['assertions_passed']+=1
            else: failures.append({'case':str(bitset),'n0_available':n0_available,'check':check,'c':c,'f':f})
assert not failures, failures[:2]
assert passes['assertions_total']==2*1024*len(checks)
assert mode_effect['all_cases']==2048

results={
 'experiment':'Reanalise conservadora do Experimento 02 WorldCIST27',
 'date':'2026-11-11', 'model':'controlled synthetic routing paths; no operational measurements',
 'corpus_audit':{'records':7854,'n1_domains':8,'potential_pairs':62832,'C2_selected':214,'F1_selected':214,'observed_n3_deliveries':None},
 'scenario_cases':{'scenarios':7,'scenario_recipient_pairs':8,'modelled_allowed_n3_deliveries_per_policy':4},
 'original_comparison':{'C2_path_edges':24,'F1_path_edges':17,'difference':7},
 'corrected_fair_comparison':{'C2_path_edges':20,'F1_path_edges':17,'difference':3,'reduction_percentage_vs_C2':15.0},
 'count_of_unique_directed_links_per_scenario':{'C2':19,'F1':16,'difference':3,'reduction_percentage_vs_C2':round(300/19,4)},
 'direct_availability_sensitivity':{'configuration_count':8,'min_difference':0,'max_difference':3,
                                  'negative_control_no_direct': 'C2=F1=20 path-edge occurrences'},
 'finite_enumeration':{'boolean_variables':10,'n0_states':2,'configurations':mode_effect['all_cases'],
    'assertions_checked':passes['assertions_total'],'assertions_passed':passes['assertions_passed'],
    'assertions_failed':len(failures),'fed_extra_deliveries_when_n0_down_configs':mode_effect['fed_extra_deliveries_when_n0_down']},
 'controls':['identical eligibility and downstream gates','domestic ingress not forced through N0 for either policy',
   'no forced N1(entry)->N0->N1(target) detour in centralized policy',
   'central source->N0->authorized N1 target permitted','federated falls back to N0 without eligible direct route',
   'centralized can match federated when direct paths not available'],
 'warnings':['C2 assumes mandatory international N0 ingress, not an arbitrary centralization.',
    'All routes, authorizations, technical qualification and N3 delivery outcomes are synthetic inputs; no observed MISP traffic.',
    '15 percent is the difference in modeled per-target path-edge occurrences, not a measured performance advantage.',
    'The direct availability variables are explicit scenario assumptions, not derived from the 7,854 records.',
    'Shared path edges are counted per target in the primary metric; a complementary per-scenario deduplicated edge count is also provided.',
    'Finite Boolean enumeration is independent of the separately reported Lean 4 proof but does not establish independent operational validity.']
}
(RESULTS/'05_resultados_consolidados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Explicit negative control on unavailable N0. This is a scenario, not deployment.
no_n0, no_n0_comp=compare_scenarios(assumptions['direct_available_default'],n0_available=False)
write_csv(RESULTS/'06_controle_N0_indisponivel.csv',no_n0_comp,list(no_n0_comp[0]))

# Export plot and preserve visual style of user-chosen graph: no headline.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
x=np.arange(1,len(comps)+1)
cum_c=np.cumsum([r['C2_path_edges'] for r in comps]);cum_f=np.cumsum([r['F1_path_edges'] for r in comps])
assert (int(cum_c[-1]),int(cum_f[-1]))==(20,17)
fig,ax=plt.subplots(figsize=(6.0,3.55),dpi=180)
ax.plot(x,cum_c,'-s',lw=2.4,markersize=5.1,label='Centralized selective (C2)',color='#416b97')
ax.plot(x,cum_f,'-o',lw=2.5,markersize=5.3,label='Federated (F1)',color='#db6b18')
ax.set_xlim(0.82,8.62);ax.set_ylim(0,23);ax.set_xticks(x)
ax.set_xlabel('Scenario–recipient case (1–8)')
ax.set_ylabel('Cumulative modeled logical links')
ax.set_yticks([0,5,10,15,20])
ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
ax.spines[['top','right']].set_visible(False)
ax.legend(frameon=False,loc='upper left',fontsize=9.2)
ax.annotate('20',(8,20),xytext=(8,1),textcoords='offset points',fontweight='bold',fontsize=11)
ax.annotate('17',(8,17),xytext=(8,-1),textcoords='offset points',fontweight='bold',fontsize=11)
fig.tight_layout()
fig.savefig(FIGS/'enlaces_c2_f1_revisado_sem_titulo.png',dpi=300,bbox_inches='tight',pad_inches=.13)
fig.savefig(FIGS/'enlaces_c2_f1_revisado_sem_titulo.svg',bbox_inches='tight',pad_inches=.13)
plt.close(fig)

textlatex=r'''% Inserir na Secao 4.3, substituindo o experimento sintético 24 vs. 17.
% Ao incorporar, conferir o label de figura ja existente no artigo.
We compared centralized selective routing and the proposed federated policy
under identical sector-evidence, authorization, N2 qualification, and N3
applicability conditions. Seven declared synthetic scenarios yield eight
scenario--recipient cases. To avoid an unfavorable baseline by construction,
the centralized policy permits domestic ingress directly to N1 and forwards
international intelligence from N0 to the authorized destination N1 without
requiring an additional return through N0. Federated routing uses an eligible
authorized international--N1 path when available and otherwise falls back to
the same N0-mediated path as the centralized policy. The metric counts logical
path-edge occurrences per scenario--recipient case, not measured traffic.

Figure~\ref{fig:controlled-routing-comparison} shows 20 cumulative logical
links for centralized routing and 17 for federation, with four modeled
authorized N3 deliveries in each policy. The difference is three links
(15\% relative to the centralized policy); it is attributable to the declared
direct international paths in the controlled cases. Counting each directed
link only once per scenario gives 19 and 16 links, respectively. When all
direct international paths are disabled, both policies require 20 logical
path-edge occurrences. Thus the comparison demonstrates a conditional
structural property under declared routing assumptions, not a measured
operational advantage.

\begin{figure}[t]
    \centering
    \includegraphics[width=0.72\textwidth]{figures/enlaces_c2_f1_revisado_sem_titulo.png}
    \caption{Cumulative logical path-edge occurrences in eight synthetic
    scenario--recipient cases under an identical selective policy.
    Both configurations allow four modeled N3 deliveries; federated routing
    uses three fewer links when direct international ingress is eligible.}
    \label{fig:controlled-routing-comparison}
\end{figure}
'''
(MANUSCRIPT/'secao_4_3_experimento02_corrigido.tex').write_text(textlatex,encoding='utf-8')

readme=f'''# Experimento 02 — revisão comparativa conservadora (WorldCIST'27)

**Resultado reexecutado:** C2 = 20; F1 = 17 ocorrências de enlaces lógicos
(15,00% a menos) em oito casos cenário–destinatário derivados de sete
cenários sintéticos. Ambos mantêm quatro entregas N3 **modeladas**.

**Resultado anterior substituído:** C2 = 24; F1 = 17 (29,17%). A implementação
anterior exigia N0 nos casos domésticos S4/S7 e, no caso S5→TEL, impunha um
retorno artificial N1:TRA→N0→N1:TEL à política centralizada. Isso favorecia F1.

## Baseline corrigido e hipóteses

1. Ambas as políticas aplicam os mesmos predicados N1, N2 e N3.
2. C2, por definição **deste baseline**, mantém entrada internacional obrigatória
   em N0; N0 pode encaminhar diretamente ao domínio N1 autorizado, sem
   passar pelo N1 de entrada em outro domínio.
3. C2 também permite ingresso doméstico direto ao N1 pertinente; a comparação
   não força N0 em eventos domésticos.
4. Para F1, a disponibilidade/autorização das rotas internacionais diretas foi
   explicitamente **assumida** nos cenários S1, S3 e S5, como já acontecia
   implicitamente no ensaio original; não foi medida nos eventos públicos.
5. Quando rota direta não está disponível, F1 utiliza o mesmo caminho N0 de C2.
6. Ambos os modelos exigem os mesmos critérios para autorizar comunicação
   multissetorial, qualificação N2 e aplicação N3.

## Análises e controles

- **Contagem primária:** ocorrências acumuladas de enlaces por caminho e por
  destinatário: C2=20, F1=17; redução condicional 15,00%.
- **Contagem alternativa:** enlaces dirigidos únicos **dentro de cada cenário**,
  sem dupla contagem de um tronco compartilhado em S5: C2=19, F1=16;
  diferença = 3 (15,79% do primeiro total).
- **Controle negativo:** com rotas internacionais diretas indisponíveis,
  as duas políticas coincidem em C2=F1=20 ocorrências.
- **Sensibilidade:** todas as oito configurações de disponibilidade dos
  caminhos diretos declarados de S1, S3 e S5, reduzindo de 0 a 3 enlaces.
- **Verificação finita independente:** 10 variáveis booleanas × dois estados
  de disponibilidade N0 = 2.048 configurações e {passes['assertions_total']:,}
  verificações; {len(failures)} falhas. Não substitui Lean 4.
- **N0 indisponível:** teste de controle sintético separado (arquivo `06_...csv`),
  sem alegação de disponibilidade operacional medida.

## Estrutura dos artefatos

- `dados/cenarios_controlados.json`: cenários originais, **inalterados**.
- `dados/hipoteses_de_roteamento.json`: novas hipóteses explicitadas.
- `dados/matriz_n1_auditada.csv` e `dados/associacoes_n1_auditadas.csv`:
  cópias dos dados originais, não reclassificados.
- `rodar_experimento_revisado.py`: execução reproduzível.
- `resultado/01_rotas_c2_f1_revisadas.csv`: cada caminho modelado.
- `resultado/02_comparacao_controlada_revisada.csv`: oito casos comparados.
- `resultado/03_enlaces_unicos_por_cenario.csv`: contagem deduplicada por cenário.
- `resultado/04_sensibilidade_disponibilidade_rota_direta.csv`: 8 controles.
- `resultado/05_resultados_consolidados.json`: totais e avisos.
- `resultado/06_controle_N0_indisponivel.csv`: cenário de disponibilidade.
- `figuras/enlaces_c2_f1_revisado_sem_titulo.*`: PNG/SVG sem cabeçalho.
- `manuscrito/secao_4_3_experimento02_corrigido.tex`: parágrafos e figura.

## Reprodutibilidade

Python 3, sem bibliotecas externas para lógica e contagem; matplotlib e numpy
são necessários apenas para recriar a figura.

```bash
python rodar_experimento_revisado.py
```

## Limites da interpretação

A melhora porcentual refere-se somente às **ocorrências de enlaces lógicos
modelados** sob a política especificada (ingresso internacional obrigatório
por N0 em C2 e direto elegível em F1). O resultado não autoriza alegar ganho
medido em tempo, taxa de entrega, precisão, CPU, exposição informacional
ou segurança operacional. As quatro entregas finais decorrem dos mesmos
predicados sintéticos em ambas as políticas; não são observações MISP.

Uma política centralizada com regras e topologia diferentes pode apresentar
outros resultados. O exercício testa esta referência C2, não toda arquitetura
centralizada possível. A prova Lean existente concerne às propriedades
formais condicionais de intermediação N0 e não verifica automaticamente
as contagens de enlaces deste script.
'''
(DEST/'README.md').write_text(readme,encoding='utf-8')

# Manifest (the script is copied into the package by shell after creation).
print(json.dumps({'revised_per_recipient':sums,'unique_C2':19,'unique_F1':16,
                  'sensitivity':len(sensitivity),'enumeration_configurations':mode_effect['all_cases'],
                  'assertions_checked':passes['assertions_total'],'failures':len(failures)},ensure_ascii=False,indent=2))
