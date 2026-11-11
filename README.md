# Reproducibility package — A Layered Federated Architecture for CTI Sharing

Supplementary **code and evidence for peer review**, provided in English so reviewers can inspect the work without relying on the paper's diagrams alone. Intended for anonymous review; publication of these artifacts or licensing remains the responsibility of the author(s).

## Status and exact scientific scope

This package contains three **different** evaluations. They must not be conflated:

| Evaluation | Inputs | Verifiable result | What it does not establish |
|---|---|---|---|
| CTI corpus audit | Original public-feed inventory and N1 classification workbooks | 7,854 records, 181 classified records, 214 N1 associations, 7,673 unresolved | Independent semantic precision or observed N2/N3 deliveries |
| Controlled synthetic routing (Experiment 02, corrected) | Seven declared scenarios, eight scenario–recipient cases, shared eligibility rules | 20 vs. 17 path-edge occurrences for centralized selective and federated; both permit four modeled N3 deliveries; difference 15% | Real-world traffic, latency or universal superiority over all centralized configurations |
| Lean 4 formal model | Explicit propositions for C2/F1 eligibility, N0 ingress, direct routes, N2/N3 conditions | Ten theorem statements, including preservation of C2-admissible deliveries and conditional N0-load decomposition | Empirical validation of these policy assumptions or a Lean proof of the Experiment 02 path-edge totals |

**Historical results excluded:** old Monte Carlo utility rankings and the superseded 24 vs. 17 (29.17%) experiment. They are not the results used for this revised study.

**Important Lean verification note:** source was assembled from the author's audited ten-theorem file. We cannot claim a fresh compiler run on this machine if Lean is not installed. See `lean/README.md` for exact instructions, and check all `#print axioms` output for `sorryAx` yourself. The `.lean` file must pass without errors for a verified claim.

## Repository layout

```text
README.md
requirements-plot.txt
lean/
  lean-toolchain
  Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean
  README.md
experiment02/
  data/                  # scenarios, routing assumptions, audited N1 data
  scripts/               # reproducible experiment + independent CSV assertions
  reference/             # expected reported results
  README.md
evidence/
  input/cti_workbooks_original.zip   # two original .xlsx files, unchanged bytes
  scripts/gerar_evidencias.py        # stdlib OOXML extraction and integrity audit
  reference/             # generated CSV evidence used in paper
  README.md
figures/                  # corrected single line chart, no internal title
formal_checks/            # separate 4,096-case Boolean check of Lean-type rules
scripts/verify_all.py     # temporary-workspace reproduction and comparison
scripts/build_manifest.py # verify archive file integrity after publication
audit/SHA256SUMS.txt     # file hashes
```

## Quick reproduction

Requires Python 3.10+; for figure generation install NumPy and Matplotlib (in a fresh Python environment):

```sh
python -m pip install -r requirements-plot.txt
python scripts/verify_all.py
```

This will regenerate the N1 evidence, the corrected controlled experiment and the figure in a temporary workspace, run independent assertions, and compare reproducible CSV outputs against the included reference files. Expected outcome: `ALL PYTHON REPRODUCIBILITY CHECKS PASSED`. It will exit nonzero if any required check fails.

For formal verification, install Lean 4 (with the toolchain listed in `lean/lean-toolchain`) and run:

```sh
cd lean
lean Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean
```

Alternatively, from the repository root, run `python scripts/verify_lean.py`. It requires a locally installed Lean executable and exits nonzero on compile errors or `sorryAx`.

No `sorryAx` is acceptable in the `#print axioms` audit. Other standard Lean axioms (e.g., `propext`, `Classical.choice`, `Quot.sound`) may be reported.

**Do not infer measured MISP exchanges from either path-edge counts or the finite Boolean checks.** The corpus classification only supports record–domain eligibility; the synthetic scenarios and their route choices are separate artifacts.

## Reproducibility contract

- The original Excel input workbooks are included byte-for-byte in `evidence/input/cti_workbooks_original.zip`. The legacy Monte Carlo scripts are intentionally excluded.
- The Python corpus audit and the finite formal-policy check use only the standard library. The routing script uses standard library for its logic and Matplotlib/NumPy for re-creating the image.
- Sensitivity: eight configurations of eligible direct paths (three binary assumptions) show a range from 0 to 3 fewer path-edge occurrences.
- Negative control: when direct international paths are disabled, both policies use 20 modeled path-edge occurrences.
- Finite Boolean cross-check (Experiment 02): 2,048 configurations and 18,432 assertions with zero reported failures; additional *formal-policy* cross-check: 4,096 configurations, 40,960 assertions, and 80 list-level aggregations. Neither substitutes for Lean compilation.
- Reference outputs are snapshots and are compared byte-for-byte where reproducible. The evidence generator's JSON summary contains the source archive path, so that field is deliberately excluded from byte comparison.
- The N1 classification is a conservative title/tag rule, *not* a manually adjudicated ground truth dataset.

## Integrity, provenance and versions

`audit/SHA256SUMS.txt` contains the cryptographic digest for every included source, reference output and graphic file, excluding the manifest itself. Run `python scripts/build_manifest.py --check` to confirm the files have not changed.

The formalization pin `leanprover/lean4:v4.30.0` was copied from the project's existing toolchain specification. Installation and actual compilation must be independently confirmed by the reproducing researcher.

## Manuscript mapping

- Section 4.1: definition of the controlled central/selective policies and the shared eight N1 domains.
- Section 4.2: 7,854 public CTI records and 214 supported N1 associations.
- Section 4.3: N0 routing property formalized in Lean; corrected controlled model (20 versus 17 path-edge occurrences, four modeled N3 outcomes).
- Figure 2: `figures/enlaces_c2_f1_revisado_sem_titulo.png`.

The word *link* means a directed edge of a **conceptual routing path**, not a physical network connection. A selective centralized policy different from C2 could produce other totals; the experiment tests this declared C2 policy only.
