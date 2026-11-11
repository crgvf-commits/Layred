#!/usr/bin/env python3
"""Reproducible audit of MC-44E9.zip; Python standard library only.
Reads OOXML as XML because the original empirical workbook fails artifact_tool import.
Does not change source data, reclassify records, or infer N2/N3 actions.
Usage: python gerar_evidencias.py /path/to/MC-44E9.zip /path/to/output
"""
import csv, hashlib, io, json, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def workbook_sheets(z):
    root=ET.fromstring(z.read('xl/workbook.xml'))
    rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    targets={r.attrib['Id']:r.attrib['Target'] for r in rels}
    for entry in root.findall('.//'+NS+'sheet'):
        target=targets[entry.attrib[REL+'id']]
        if target.startswith('/'): target=target.lstrip('/')
        elif not target.startswith('xl/'): target='xl/'+target
        yield entry.attrib['name'],target

def iter_rows(z, path):
    with z.open(path) as stream:
        for _, element in ET.iterparse(stream,events=('end',)):
            if element.tag==NS+'row':
                data={}
                for cell in element.findall(NS+'c'):
                    address=cell.attrib.get('r','')
                    column=''.join(ch for ch in address if ch.isalpha())
                    if cell.attrib.get('t')=='inlineStr':
                        value=''.join(x.text or '' for x in cell.iter(NS+'t'))
                    else:
                        val=cell.find(NS+'v')
                        value='' if val is None else (val.text or '')
                    data[column]=value
                yield int(element.attrib['r']),data
                element.clear()

def get_sheets(z, names):
    paths=dict(workbook_sheets(z))
    results={}
    for name in names:
        rows=list(iter_rows(z,paths[name]))
        header_idx=1 if name=='Events' else 4
        header=next(x for i,x in rows if i==header_idx)
        results[name]=[{v:r.get(k,'') for k,v in header.items() if v} for i,r in rows if i>header_idx]
    return results

def write_csv(path, data, columns):
    with open(path,'w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore')
        wr.writeheader()
        wr.writerows(data)

def sha256(path):
    dig=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            dig.update(b)
    return dig.hexdigest()

def main(source, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with ZipFile(source) as root:
        source_files=root.namelist()
        with ZipFile(io.BytesIO(root.read('corpus_inventory.xlsx'))) as zi:
            inventory=get_sheets(zi,['Events'])['Events']
        with ZipFile(io.BytesIO(root.read('empirical_sector_classification.xlsx'))) as zs:
            d=get_sheets(zs,['Routing','N1_Sectors','Pending_N1','N2_Tactical','N3_Operational'])
    n1=d['N1_Sectors'];pending=d['Pending_N1'];n2=d['N2_Tactical'];n3=d['N3_Operational'];routing=d['Routing']
    all_ids={x['Record_ID'] for x in inventory}
    assigned_ids={x['Record_ID'] for x in n1}
    pending_ids={x['Record_ID'] for x in pending}
    n1_key={(x['Record_ID'],x['N1_Domain_Code']) for x in n1}
    n2_key={(x['Record_ID'],x['N1_Domain_Code']) for x in n2}
    n3_key={(x['Record_ID'],x['N1_Domain_Code']) for x in n3}
    domains=['GOV','FIN','EDU','HLT','ENE','TEL','TRA','INV']
    by_domain=Counter(x['N1_Domain_Code'] for x in n1)
    by_method=Counter(x['Classification_Method'] for x in n1)
    per_record=Counter(x['Record_ID'] for x in n1)
    multi=sum(1 for k,v in per_record.items() if v>1)
    meta={(x['Record_ID'],x['N1_Domain_Code']):x for x in n1}
    n0map={x['Record_ID']:x for x in routing}
    invmap={x['Record_ID']:x for x in inventory}
    check=[]
    def test(label, actual, expected, detail=''):
        check.append(dict(Test=label,Actual=str(actual),Expected=str(expected),Status='PASS' if actual==expected else 'FAIL',Notes=detail))
    test('Records in inventory',len(inventory),7854)
    test('Unique record IDs in inventory',len(all_ids),7854)
    test('Routing records',len(routing),7854)
    test('Unique routing record IDs',len(n0map),7854)
    test('N1 sector associations',len(n1),214)
    test('Unique N1 pairs',len(n1_key),214)
    test('N1 classified records',len(assigned_ids),181)
    test('N1 unresolved records',len(pending),7673)
    test('Unique unresolved IDs',len(pending_ids),7673)
    test('Classified/pending disjoint',len(assigned_ids&pending_ids),0)
    test('Classified/pending exhaustive',len(assigned_ids|pending_ids),7854)
    test('All N1 IDs in corpus',len(assigned_ids-all_ids),0)
    test('All pending IDs in corpus',len(pending_ids-all_ids),0)
    test('Records with multiple sectors',multi,21)
    test('Classified by sector tags',by_method['Explicit sector tag'],89)
    test('Classified by direct title',by_method['Direct title match'],125)
    test('Unrecognized classification methods',sum(v for k,v in by_method.items() if k not in ('Explicit sector tag','Direct title match')),0)
    test('N1 associations with evidence field',sum(bool(x['Explicit_Evidence'].strip()) for x in n1),214)
    test('N2 records',len(n2),214)
    test('N3 records',len(n3),214)
    test('N2 keyset equals N1',n2_key==n1_key,True,'Same record–domain assignments: not evidence of additional filtering')
    test('N3 keyset equals N1',n3_key==n1_key,True,'Same record–domain assignments: N3 operational actions are prospective')
    test('Inventory IDs equal routing IDs',all_ids==set(n0map),True)
    test('Routing status matches N1 classified set',sum(1 for x in routing if (x['N1_Status']=='Supported sector assignment')==(x['Record_ID'] in assigned_ids)),7854)
    test('Assignment event IDs agree with inventory',sum(1 for x in n1 if x['Event_ID']==invmap[x['Record_ID']]['Event_ID']),214)
    test('N1 title agrees with inventory',sum(1 for x in n1 if x['Title']==invmap[x['Record_ID']]['Title']),214)
    test('N2 assignment keys unique',len(n2_key),len(n2))
    test('N3 assignment keys unique',len(n3_key),len(n3))
    expected_domains=dict(FIN=81,GOV=47,ENE=24,TEL=17,HLT=12,TRA=12,INV=11,EDU=10)
    for k,v in expected_domains.items():test('N1 '+k,by_domain[k],v)
    lexical=[]
    semantic_review=[]
    for x in n1:
        evidence=x['Explicit_Evidence']
        title_terms=re.findall(r'Title: "([^\"]+)"',evidence)
        tag_terms=re.findall(r'Explicit sector tag: ([^|]+)',evidence)
        title_hit=any(term.casefold() in x['Title'].casefold() for term in title_terms)
        tag_hit=any(term.strip().casefold() in x['Original_Tags'].casefold() for term in tag_terms)
        expected_method=x['Classification_Method']
        verified=(expected_method=='Direct title match' and title_hit) or (expected_method=='Explicit sector tag' and tag_hit)
        lexical.append({'Record_ID':x['Record_ID'],'N1_Domain_Code':x['N1_Domain_Code'],
                        'Classification_Method':expected_method,'Literal_Evidence_Reproduced':int(verified),
                        'Title_Evidence_Reproduced':int(title_hit),'Tag_Evidence_Reproduced':int(tag_hit),
                        'Explicit_Evidence':evidence,'Title':x['Title']})
        if x['N1_Domain_Code']=='ENE' and expected_method=='Direct title match' and re.search(r'black\s*energy|blackenergy',x['Title'],re.I):
            semantic_review.append({'Record_ID':x['Record_ID'],'Domain':'ENE','Title':x['Title'],
              'Evidence':evidence,'Reason':'Term Energy may refer to BlackEnergy malware name instead of energy-sector target; requires human semantic review','Status':'Not adjudicated'})
    write_csv(output/'08_auditoria_evidencia_lexical.csv',lexical,list(lexical[0]))
    write_csv(output/'09_casos_revisao_semantica.csv',semantic_review,
              ['Record_ID','Domain','Title','Evidence','Reason','Status'])
    test('Title-method evidence literally present',sum(x['Literal_Evidence_Reproduced'] for x in lexical if x['Classification_Method']=='Direct title match'),125)
    test('Sector-tag evidence literally present',sum(x['Literal_Evidence_Reproduced'] for x in lexical if x['Classification_Method']=='Explicit sector tag'),89)
    write_csv(output/'01_testes_integridade.csv',check,['Test','Actual','Expected','Status','Notes'])
    details=[]
    for x in n1:
        details.append({
            'Record_ID':x['Record_ID'],'Event_ID':x['Event_ID'],
            'N1_Domain_Code':x['N1_Domain_Code'],'Classification_Method':x['Classification_Method'],
            'Explicit_Evidence':x['Explicit_Evidence'],'Confidence_declared':x['Confidence'],
            'Title':x['Title'],'Original_Tags':x['Original_Tags'],'TLP':x['TLP'],
            'Feed':x['Feed'],'Source_File':x['Source_File'], 'Source_URL':x['Source_URL']
        })
    write_csv(output/'02_associacoes_n1_auditaveis.csv',details,list(details[0]))
    per_domain=[]
    for dom in domains:
        per_domain.append(dict(Domain=dom,All_records=len(inventory),C1_full_distribution=len(inventory),
                               C2_central_filtered=by_domain[dom],F1_federated_N1=by_domain[dom],
                               Not_assigned_pairs=len(inventory)-by_domain[dom],
                               Assigned_pair_fraction=round(by_domain[dom]/len(inventory),8)))
    write_csv(output/'03_comparacao_por_dominio.csv',per_domain,list(per_domain[0]))
    comparison=[]
    for record in inventory:
        rid=record['Record_ID']
        for dom in domains:
            x=meta.get((rid,dom))
            comparison.append(dict(Record_ID=rid,Event_ID=record['Event_ID'],Domain=dom,
                    C1_full_distribution=1,C2_central_filtered=int(x is not None),
                    F1_federated_N1=int(x is not None),
                    Explicit_Evidence_Source=(''+x['Classification_Method']) if x else 'Unresolved by selected fields'))
    write_csv(output/'04_matriz_comparativa_n1.csv',comparison,list(comparison[0]))
    examples=[]
    for dom in domains:
        candidates=[x for x in details if x['N1_Domain_Code']==dom]
        for x in candidates[:2]: examples.append(x)
    write_csv(output/'05_exemplos_rastreaveis.csv',examples,list(details[0]))
    tlp=Counter(x['TLP'] for x in n1)
    tlp_list=[{'TLP_Marking_as_recorded':k if k else '(absent)','N1_Associations':v} for k,v in sorted(tlp.items(),key=lambda a:(-a[1],a[0]))]
    write_csv(output/'06_marcacoes_tlp_n1.csv',tlp_list,['TLP_Marking_as_recorded','N1_Associations'])
    summary={
      'source_zip':str(source), 'source_zip_sha256':sha256(source),'source_files':source_files,
      'inventory_records':len(inventory),'domains':domains,'n1_assigned_records':len(assigned_ids),
      'n1_associations':len(n1),'n1_unresolved_records':len(pending_ids),
      'n1_multi_domain_records':multi,'n1_associations_by_domain':dict(by_domain),
      'n1_classification_method':dict(by_method),
      'c1_full_distribution_N1_pairs':len(inventory)*len(domains),
      'c2_central_filtered_N1_pairs':len(n1_key),
      'f1_federated_N1_pairs':len(n1_key),
      'excluded_pairs_by_explicit_evidence_policy':len(inventory)*len(domains)-len(n1_key),
      'not_assigned_fraction_of_full_pairs':round(1-len(n1_key)/(len(inventory)*len(domains)),10),
      'assigned_record_fraction':round(len(assigned_ids)/len(inventory),10),
      'n2_assignments':len(n2),'n3_assignments':len(n3),
      'n2_extra_selectivity_observed':False,'n3_extra_selectivity_observed':False,
      'tests_run':len(check),'tests_passed':sum(x['Status']=='PASS' for x in check),
      'tests_failed':[x for x in check if x['Status']=='FAIL']
    }
    (output/'07_resumo_evidencias.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    for key in ['inventory_records','n1_assigned_records','n1_associations','n1_unresolved_records','n1_multi_domain_records','c1_full_distribution_N1_pairs','c2_central_filtered_N1_pairs','f1_federated_N1_pairs','excluded_pairs_by_explicit_evidence_policy','not_assigned_fraction_of_full_pairs','tests_run','tests_passed']:
        print(key,summary[key])
    if summary['tests_failed']:
        print('FAILED',summary['tests_failed']);sys.exit(2)

if __name__=='__main__':
    inp=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/MC-44E9.zip')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/evidencias_worldcist/resultado')
    main(inp,out)
