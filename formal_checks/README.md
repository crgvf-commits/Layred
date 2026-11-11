# Finite model cross-check (distinct from Lean 4)

This standard-library Python script was adapted from the project's earlier independent 4,096-configuration Boolean routing audit. Only the input matrix path and status label were changed to fit this self-contained repository. The 12 Boolean inputs are exhaustively enumerated (`2^12 = 4,096`), with ten checks each (`40,960` assertions), and 80 deterministic list-level aggregation checks.

```sh
python formal_checks/verificar_comparacao_n0.py
```

The script also checks 62,832 record-domain rows from `evidence/reference/04_matriz_comparativa_n1.csv`. Output appears in `formal_checks/resultado/`, which is generated (not tracked as reference). It must not be misrepresented as a compilation of the Lean file or as live MISP routing.
