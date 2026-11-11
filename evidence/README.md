# Corpus and sector-association audit

Contains the two original, unmodified source `.xlsx` workbooks repacked into `input/cti_workbooks_original.zip` (legacy Monte Carlo analysis files excluded). The script `scripts/gerar_evidencias.py` reads the zipped Excel workbooks with the Python standard library, regenerates reference CSV files, and runs integrity/lexical checks.

```sh
python evidence/scripts/gerar_evidencias.py evidence/input/cti_workbooks_original.zip resultados_local
```

Expected: 7,854 records; 181 records with explicit sector evidence; 214 N1 associations; 7,673 unresolved records; 21 multi-domain records; 62,832 full-distribution reference pairs. N2/N3 assignments are proposed mappings; not observed downstream deliveries. The conservative evidence method does not establish independently adjudicated classification precision. Read `reference/09_casos_revisao_semantica.csv` for lexical cases flagged for future expert review.

`reference/` includes CSV snapshots that can be regenerated from the source workbooks. The driver `scripts/verify_all.py` compares the reproducible CSV files with these snapshots.
