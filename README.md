
# Reproducibility Package — A Layered Federated Architecture for CTI Sharing

Supplementary code and evidence for peer review, provided in English to support independent examination and reproduction of the reported results.

This package is intended for anonymous review. Publication and licensing of the artifacts remain the responsibility of the authors.

## Status and Exact Scientific Scope

This package contains three complementary evaluations with distinct objectives and evidence.

| Evaluation | Inputs | Verifiable result | What it does not establish |
|---|---|---|---|
| CTI corpus audit | Original public-feed inventory and N1 classification workbooks | 7,854 records, 181 classified records, 214 N1 associations, and 7,673 unresolved records | Independent semantic precision or observed N2/N3 deliveries |
| Controlled synthetic routing (Experiment 02) | Seven declared scenarios, eight scenario–recipient cases, and shared eligibility rules | 20 versus 17 path-edge occurrences for centralized selective and federated routing; four modeled N3 deliveries under each policy; 15% fewer logical links under F1 | Real-world traffic, latency, or universal superiority over all centralized configurations |
| Lean 4 formal model | Explicit definitions of C2/F1 eligibility, N0 ingress, direct routes, and N2/N3 conditions | Ten theorems checked in Lean 4, including preservation of C2-admissible deliveries and conditional N0-load decomposition; no `sorryAx` dependencies reported | Empirical validation of policy assumptions or a Lean proof of the Experiment 02 path-edge totals |

**Historical results excluded:** Earlier Monte Carlo utility rankings and the superseded 24 versus 17 (29.17%) experiment are not used in the revised study.

### Lean 4 Verification Status

The ten-theorem source file was executed in Lean 4.

The `#print axioms` audit reported only standard Lean axioms (`propext`, `Classical.choice`, and `Quot.sound`) for eight theorems. The remaining two theorems reported no axiom dependencies.

No `sorryAx` dependencies were reported.

The theorem audit covers:

1. `centralized_vs_federated`
2. `federated_operational_path_when_n0_unavailable`
3. `single_request_decomposition`
4. `n0_load_decomposition`
5. `federated_n0_not_greater`
6. `federated_n0_strictly_less_if_bypass`
7. `strictly_less_with_eligible_direct_request`
8. `no_direct_same_route`
9. `no_direct_same_n0_work`
10. `route_available_without_n0`

The formal results establish properties of the specified routing policies under their explicit assumptions. They do not constitute measurements of operational network performance.

See `lean/README.md` for the verification procedure.

## Repository Layout

```text
README.md
requirements-plot.txt
lean/
  lean-toolchain
  Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean
  README.md
experiment02/
  data/                  # Scenarios, routing assumptions, audited N1 data
  scripts/               # Reproducible experiment and CSV assertions
  reference/             # Expected experimental results
  README.md
evidence/
  input/
    cti_workbooks_original.zip
  scripts/
    gerar_evidencias.py
  reference/             # Generated CTI evidence used in the paper
  README.md
figures/
  enlaces_c2_f1_revisado_sem_titulo.png
formal_checks/            # 4,096-case Boolean verification
scripts/
  verify_all.py
  verify_lean.py
  build_manifest.py
audit/
  SHA256SUMS.txt
```

## Quick Reproduction

### Python Requirements

Python 3.10 or later is required.

For figure generation, install NumPy and Matplotlib in a fresh Python environment:

```sh
python -m pip install -r requirements-plot.txt
```

### Reproduce the Experimental Results

From the repository root, run:

```sh
python scripts/verify_all.py
```

The script regenerates the N1 evidence, the controlled routing experiment, and the figure in a temporary workspace.

It also runs the implemented assertions and compares reproducible CSV outputs against the reference files.

Expected output:

```text
ALL PYTHON REPRODUCIBILITY CHECKS PASSED.
```

The script returns a nonzero exit status if a required verification fails.

### Lean 4 Formal Verification

Install Lean 4 using the toolchain specified in:

```text
lean/lean-toolchain
```

Then run:

```sh
cd lean
lean Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean
```

Alternatively, from the repository root:

```sh
python scripts/verify_lean.py
```

The verification script requires an installed Lean executable and returns a nonzero exit status on compilation errors or detected `sorryAx` dependencies.

The source contains ten `#print axioms` commands, allowing reviewers to inspect the logical dependencies of each theorem.

The recorded audit reports the standard Lean axioms `propext`, `Classical.choice`, and `Quot.sound` for eight theorems. Two theorems report no axiom dependencies.

No `sorryAx` dependencies were reported.

## Experimental Design

### CTI Corpus Classification

The corpus contains 7,854 processable public CTI records, including 7,850 MISP events and four CISA STIX advisories.

Records are associated with an N1 domain only when their original titles or sectoral tags provide explicit evidence of sector relevance.

The analysis identifies:

- 181 records supporting at least one sector assignment.
- 214 evidence-supported N1 associations.
- 89 associations derived from sectoral tags.
- 125 associations derived from record titles.
- 7,673 unresolved records.

Unresolved records are not considered irrelevant. They lack sufficient explicit title/tag evidence for automatic sector assignment under the adopted rule.

The classification is not a manually adjudicated ground-truth dataset.

### Routing Policies

Three analytical policies are distinguished:

- **C1 — Centralized complete distribution:** all records are potentially available to all eight N1 domains.
- **C2 — Centralized selective routing:** records are assigned using the same sector-evidence rule as F1, with mandatory N0 mediation for international ingress.
- **F1 — Federated selective routing:** preserves the same eligibility and downstream requirements as C2 while permitting authorized direct international communication with relevant N1 domains.

The comparison between C2 and F1 uses identical sector-evidence, authorization, N2 qualification, and N3 applicability conditions.

Domestic ingress may reach the relevant N1 domain directly under both selective policies.

### Controlled Routing Scenarios

Experiment 02 uses seven synthetic scenarios producing eight scenario–recipient cases.

The scenarios cover authorized and unauthorized international ingress, technical qualification, dissemination restrictions, cross-sector cooperation, insufficient sector evidence, and domestic ingress.

The three cases producing the observed reduction are:

- **S1–TRA:** authorized international CTI for transportation.
- **S3–TEL:** telecommunications intelligence rejected during N2 qualification.
- **S5–TRA:** transportation recipient in an authorized cross-sector exchange.

Each case requires one fewer logical path-edge occurrence under F1 than under C2.

The remaining five cases require the same number of logical links under both policies.

The resulting comparison is:

| Metric | C2 | F1 |
|---|---:|---:|
| Cumulative logical path-edge occurrences | 20 | 17 |
| Modeled authorized N3 deliveries | 4 | 4 |

The reduction in logical path-edge occurrences is:

```text
(20 - 17) / 20 * 100 = 15%
```

The metric includes selected routing paths terminated during N2 qualification, not only completed N3 deliveries.

A logical link represents a directed edge in a conceptual routing path, not a physical network connection.

### Sensitivity Analysis

The analysis considers all eight combinations of three binary direct-route availability assumptions.

Depending on the availability of eligible direct paths, F1 saves between zero and three logical links relative to C2.

When all direct international routes are disabled, both policies require 20 logical path-edge occurrences.

The modeled authorized N3 delivery outcomes remain unchanged across these configurations.

### Boolean Verification

Two complementary Python checks are included:

| Verification | Configurations | Assertions |
|---|---:|---:|
| Experiment 02 Boolean cross-check | 2,048 | 18,432 |
| Formal-policy Boolean cross-check | 4,096 | 40,960 |

The formal-policy cross-check evaluates all 4,096 combinations of 12 Boolean routing conditions.

These conditions cover node availability, authorization, sector relevance, technical qualification, and operational applicability.

Ten routing properties are checked per configuration, totaling 40,960 assertions. The verification also includes 80 list-level aggregations.

All reported assertions passed without violations.

These finite checks complement the Lean 4 proofs but do not replace theorem verification.

## Reproducibility Contract

- The original Excel input workbooks are included byte-for-byte in `evidence/input/cti_workbooks_original.zip`.
- Legacy Monte Carlo scripts are intentionally excluded.
- The Python corpus audit and the finite formal-policy check use only the standard library.
- The routing experiment uses the standard library for its logic and NumPy/Matplotlib for figure generation.
- Reference CSV outputs are compared byte-for-byte when reproducible.
- The evidence generator's JSON summary contains the source archive path; that field is excluded from byte comparison.
- The N1 classification is based on explicit title/tag evidence rather than independently adjudicated semantic relevance.
- The synthetic routing scenarios are separate from the empirical CTI corpus classification.
- The modeled N2/N3 outcomes do not represent observed MISP exchanges.

## Integrity, Provenance, and Versions

The file `audit/SHA256SUMS.txt` contains cryptographic SHA-256 digests for the included source files, reference outputs, and graphics, excluding the manifest itself.

To verify file integrity, run:

```sh
python scripts/build_manifest.py --check
```

The Lean toolchain is specified as:

```text
leanprover/lean4:v4.30.0
```

The reported Lean audit was obtained by executing the ten-theorem source file. The compiler version used for that execution should be confirmed against the pinned toolchain when reproducing the verification.

Reviewers can independently execute the source and inspect the `#print axioms` output.

## Manuscript Mapping

| Manuscript component | Reproducibility material |
|---|---|
| Section 4.1 — Data Sources and Evaluation Setup | Public CTI inventory, routing policies, and N1 domains |
| Section 4.2 — Sector Classification | Original workbooks, classification scripts, and 214 supported N1 associations |
| Section 4.3 — Comparative Routing Analysis and Formal Verification | Controlled scenarios, C2/F1 results, sensitivity analysis, Boolean verification, and Lean 4 proofs |
| Figure 2 | `figures/enlaces_c2_f1_revisado_sem_titulo.png` |

The reference results correspond to the reported centralized selective and federated policies.

The 15% reduction applies to the eight controlled scenario–recipient cases and the defined logical path-edge metric.

It does not establish measured reductions in latency, network traffic, processing cost, or universal superiority over all possible centralized configurations.

## Scientific Scope

The supplementary materials support three complementary findings:

1. Public CTI records can be assigned to strategic sectors using explicit and auditable title/tag evidence.
2. Under the specified controlled scenarios, federated selective routing preserves the same modeled authorized N3 deliveries while reducing cumulative logical path-edge occurrences.
3. The Lean 4 formalization establishes routing properties, including eligibility preservation and conditional reduction of mandatory N0 intermediation.

The combination of empirical classification, controlled comparison, finite verification, and formal proof supports examination of the proposed architecture within the declared analytical scope.

Operational deployment, independent semantic validation, and measurements of real-world communication overhead remain outside the present evaluation.
