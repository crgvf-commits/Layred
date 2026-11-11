# Lean 4 formal proof

File: `Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean` (10 named theorem statements). The source is the project's **complete** ten-theorem audit file, not an excerpt.

Toolchain pin from the project: `leanprover/lean4:v4.30.0`.

```sh
# After installing elan / Lean 4, in this directory:
lean Comparacao_C2_F1_N0_Auditoria_10_Teoremas.lean
```

Expected: no compilation errors and no `sorryAx` in the output of any of the ten `#print axioms` commands. A Lean executable was not available for a fresh compilation in the repository-building environment; its acceptance must therefore be checked by the user/reviewer on a machine with the pinned toolchain.

The Lean model formally compares *international ingress via N0* to a selectable *direct international-to-N1 ingress* with identical downstream conditions, and proves the exact count decomposition for a **finite list of routing demands**:

`centralN0Load p qs = federatedN0Load p qs + bypassedN0Load p qs`.

Hence F1 does not increase required N0 mediations and strictly reduces them if the bypass count is positive. This is a theorem **conditional on the policy definitions**, not a measured traffic result. Its statement does not depend on the synthetic paths of Experiment 02 and does not imply a formal proof of the 15% link difference.

Optional automated checker from the repository root: `python scripts/verify_lean.py`. It fails explicitly if Lean is missing and never reports an unperformed compilation as verified.
