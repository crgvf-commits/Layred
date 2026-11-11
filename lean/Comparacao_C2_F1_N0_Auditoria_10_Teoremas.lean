import Lean

/-!
WorldCIST'27 — Comparative formal model (Lean 4 / core library).

SCIENTIFIC SCOPE
C2 is a selective centralized policy whose international ingress depends on N0.
F1 accepts the same C2 path OR a directly authorized international-to-N1 path.
Both use identical N2 and N3 qualification, authorization, and applicability rules.
N1 domains are represented by Fin 8, matching the eight domains in the paper.

The theorem proves properties CONDITIONAL ON this declared topology/policy.
It is NOT a measurement of MISP traffic, end-to-end latency, semantic correctness,
network resilience, or unconditional superiority of federation.

This is a candidate Lean 4 file: compilation must be verified with the Lean compiler.
-/

namespace WorldCIST27

-- Scoped classical decidability is required for propositions in routing policies.
open Classical

abbrev RecordId := Nat
abbrev SourceId := Nat
abbrev OrganizationId := Nat
abbrev Sector := Fin 8

/-- Policy and infrastructure conditions are kept explicit and abstract.
    They must be grounded in observed configuration/logs before empirical claims. -/
structure RoutingPolicy where
  sectorRelevant : RecordId → Sector → Prop
  internationalAuthorized : SourceId → Sector → Prop
  internationalLinkAvailable : SourceId → Sector → Prop
  n0Available : Prop
  n0IntakeAuthorized : SourceId → Prop
  n0ForwardAuthorized : RecordId → Sector → Prop
  n1Available : Sector → Prop
  n2Available : Sector → Prop
  technicallyQualified : RecordId → Sector → Prop
  n3Available : OrganizationId → Prop
  recipientAuthorized : RecordId → OrganizationId → Prop
  operationallyApplicable : RecordId → OrganizationId → Prop

/-- Selective centralized international ingress: obligatory passage via N0.
    The baseline is NOT a claim that every real centralized network requires N0. -/
def C2Ingress (p : RoutingPolicy) (src : SourceId)
    (r : RecordId) (d : Sector) : Prop :=
  p.n0Available ∧
  p.n0IntakeAuthorized src ∧
  p.n0ForwardAuthorized r d ∧
  p.sectorRelevant r d ∧
  p.n1Available d

/-- Authorized sector-specific direct international-to-N1 communication. -/
def DirectIngress (p : RoutingPolicy) (src : SourceId)
    (r : RecordId) (d : Sector) : Prop :=
  p.internationalAuthorized src d ∧
  p.internationalLinkAvailable src d ∧
  p.sectorRelevant r d ∧
  p.n1Available d

/-- Federation accepts an N0-mediated path OR an eligible direct N1 path. -/
def F1Ingress (p : RoutingPolicy) (src : SourceId)
    (r : RecordId) (d : Sector) : Prop :=
  C2Ingress p src r d ∨ DirectIngress p src r d

/-- Common downstream conditions at N2 and for delivery to N3. -/
def DownstreamReady (p : RoutingPolicy) (r : RecordId)
    (d : Sector) (org : OrganizationId) : Prop :=
  p.n2Available d ∧
  p.technicallyQualified r d ∧
  p.n3Available org ∧
  p.recipientAuthorized r org ∧
  p.operationallyApplicable r org

/-- Eligible final delivery under centralized selective reference. -/
def C2Delivery (p : RoutingPolicy) (src : SourceId)
    (r : RecordId) (d : Sector) (org : OrganizationId) : Prop :=
  C2Ingress p src r d ∧ DownstreamReady p r d org

/-- Eligible final delivery under proposed federated policy. -/
def F1Delivery (p : RoutingPolicy) (src : SourceId)
    (r : RecordId) (d : Sector) (org : OrganizationId) : Prop :=
  F1Ingress p src r d ∧ DownstreamReady p r d org

/-- Main comparative theorem:
  (1) C2 admissible final deliveries remain admissible under F1;
  (2) F1 operational delivery respects N2 qualification and N3 conditions;
  (3) if N0 is unavailable but direct N1 communication is eligible,
      F1 can receive the record and C2 cannot through its defined route;
  (4) absent an eligible direct path, both admit the same final deliveries.

  Theorem (3) is a topological/policy guarantee, not measured uptime.
  Theorem (4) is important: federation does not magically improve end-recipient
  selectivity when both configurations apply the same downstream criteria.
-/
theorem centralized_vs_federated (p : RoutingPolicy) :
    (∀ src r d org,
      C2Delivery p src r d org → F1Delivery p src r d org) ∧
    (∀ src r d org,
      F1Delivery p src r d org →
        p.technicallyQualified r d ∧
        p.recipientAuthorized r org ∧
        p.operationallyApplicable r org) ∧
    (∀ src r d,
      ¬ p.n0Available →
      DirectIngress p src r d →
      F1Ingress p src r d ∧ ¬ C2Ingress p src r d) ∧
    (∀ src r d org,
      ¬ DirectIngress p src r d →
      (F1Delivery p src r d org ↔ C2Delivery p src r d org)) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro src r d org h
    exact ⟨Or.inl h.1, h.2⟩
  · intro src r d org h
    exact ⟨h.2.2.1, h.2.2.2.2.1, h.2.2.2.2.2⟩
  · intro src r d hN0 hDirect
    constructor
    · exact Or.inr hDirect
    · intro hC2
      exact hN0 hC2.1
  · intro src r d org hNoDirect
    constructor
    · intro hFed
      cases hFed.1 with
      | inl hC2 => exact ⟨hC2, hFed.2⟩
      | inr hDirect => exact False.elim (hNoDirect hDirect)
    · intro hC2
      exact ⟨Or.inl hC2.1, hC2.2⟩

/-- Corollary: a fully qualified N3 delivery can remain eligible despite N0
    unavailability IF direct communication and all downstream conditions hold. -/
theorem federated_operational_path_when_n0_unavailable
    (p : RoutingPolicy) (src : SourceId) (r : RecordId)
    (d : Sector) (org : OrganizationId)
    (hN0 : ¬ p.n0Available)
    (hDirect : DirectIngress p src r d)
    (hDown : DownstreamReady p r d org) :
    F1Delivery p src r d org ∧ ¬ C2Delivery p src r d org := by
  constructor
  · exact ⟨Or.inr hDirect, hDown⟩
  · intro hC2
    exact hN0 hC2.1.1


/-! ### Added in Stage 4 revision: N0 mediation workload

The measure is the NUMBER OF N0-MEDIATED ROUTING DECISIONS in a declared
list of requests. It is NOT CPU, memory, latency, network bytes, or a measured
MISP transmission count. A request can represent a source-record-domain tuple.

F1 prioritizes an available, authorized direct international-to-N1 route; if
none exists, F1 retains the same N0-mediated path available to C2. This
routing-choice policy is explicit; no actual choice is inferred from the corpus.
-/

structure RoutingDemand where
  source : SourceId
  record : RecordId
  domain : Sector
  recipient : OrganizationId
  deriving Repr

inductive SelectedRoute where
  | noRoute
  | viaN0
  | directN1
  deriving DecidableEq, Repr

/-- C2's chosen route, if international ingress via N0 is permitted. -/
noncomputable def routeC2 (p : RoutingPolicy) (q : RoutingDemand) : SelectedRoute := by
  classical
  exact if C2Ingress p q.source q.record q.domain then .viaN0 else .noRoute

/-- F1 prioritizes the authorized sector-specific direct route and otherwise
    falls back to the same N0 route as C2. -/
noncomputable def routeF1 (p : RoutingPolicy) (q : RoutingDemand) : SelectedRoute := by
  classical
  exact if DirectIngress p q.source q.record q.domain then .directN1
    else routeC2 p q

/-- One unit per N0-mediated ingress decision, zero otherwise. -/
def n0Units : SelectedRoute → Nat
  | .viaN0 => 1
  | .noRoute => 0
  | .directN1 => 0

/-- N0-mediated requests avoided by F1 when a C2 route would have existed. -/
noncomputable def bypassUnits (p : RoutingPolicy) (q : RoutingDemand) : Nat :=
  if C2Ingress p q.source q.record q.domain ∧
     DirectIngress p q.source q.record q.domain then 1 else 0

/-- Every request's C2 N0 load partitions into F1 load plus avoided N0 work. -/
theorem single_request_decomposition (p : RoutingPolicy) (q : RoutingDemand) :
    n0Units (routeC2 p q) = n0Units (routeF1 p q) + bypassUnits p q := by
  classical
  by_cases hd : DirectIngress p q.source q.record q.domain
  · by_cases hc : C2Ingress p q.source q.record q.domain
    · simp [routeC2, routeF1, n0Units, bypassUnits, hd, hc]
    · simp [routeC2, routeF1, n0Units, bypassUnits, hd, hc]
  · by_cases hc : C2Ingress p q.source q.record q.domain
    · simp [routeC2, routeF1, n0Units, bypassUnits, hd, hc]
    · simp [routeC2, routeF1, n0Units, bypassUnits, hd, hc]

/-- Recursively sums a per-request counting function over a finite list. -/
def sumDemand (f : RoutingDemand → Nat) : List RoutingDemand → Nat
  | [] => 0
  | q :: qs => f q + sumDemand f qs

noncomputable def centralN0Load (p : RoutingPolicy) (qs : List RoutingDemand) : Nat :=
  sumDemand (fun q => n0Units (routeC2 p q)) qs

noncomputable def federatedN0Load (p : RoutingPolicy) (qs : List RoutingDemand) : Nat :=
  sumDemand (fun q => n0Units (routeF1 p q)) qs

noncomputable def bypassedN0Load (p : RoutingPolicy) (qs : List RoutingDemand) : Nat :=
  sumDemand (bypassUnits p) qs

/-- Main comparative N0 theorem: exact decomposition, not a guessed gain. -/
theorem n0_load_decomposition (p : RoutingPolicy) (qs : List RoutingDemand) :
    centralN0Load p qs = federatedN0Load p qs + bypassedN0Load p qs := by
  induction qs with
  | nil => rfl
  | cons q rest ih =>
      change n0Units (routeC2 p q) + centralN0Load p rest =
        (n0Units (routeF1 p q) + federatedN0Load p rest) +
        (bypassUnits p q + bypassedN0Load p rest)
      have hsingle := single_request_decomposition p q
      omega

/-- The F1 policy cannot increase N0 mediation counts relative to C2. -/
theorem federated_n0_not_greater (p : RoutingPolicy) (qs : List RoutingDemand) :
    federatedN0Load p qs ≤ centralN0Load p qs := by
  have h := n0_load_decomposition p qs
  omega

/-- Strictly fewer N0 mediations whenever a real eligible bypass is present. -/
theorem federated_n0_strictly_less_if_bypass
    (p : RoutingPolicy) (qs : List RoutingDemand)
    (hb : 0 < bypassedN0Load p qs) :
    federatedN0Load p qs < centralN0Load p qs := by
  have h := n0_load_decomposition p qs
  omega

/-- A concrete request for which BOTH the central and the direct N1 routes are
    eligible witnesses a strict reduction, even if other requests remain. -/
theorem strictly_less_with_eligible_direct_request
    (p : RoutingPolicy) (q : RoutingDemand) (other : List RoutingDemand)
    (hc : C2Ingress p q.source q.record q.domain)
    (hd : DirectIngress p q.source q.record q.domain) :
    federatedN0Load p (q :: other) < centralN0Load p (q :: other) := by
  have hb : bypassUnits p q = 1 := by
    simp [bypassUnits, hc, hd]
  have hpositive : 0 < bypassedN0Load p (q :: other) := by
    change 0 < bypassUnits p q + bypassedN0Load p other
    rw [hb]
    omega
  exact federated_n0_strictly_less_if_bypass p (q :: other) hpositive

/-- NEGATIVE CONTROL: without an authorized direct alternative, the federated
    selection is exactly the same as the centralized one for that request. -/
theorem no_direct_same_route
    (p : RoutingPolicy) (q : RoutingDemand)
    (h : ¬ DirectIngress p q.source q.record q.domain) :
    routeF1 p q = routeC2 p q := by
  simp [routeF1, h]

/-- NEGATIVE CONTROL: a single request with no direct route has no N0
    mediation advantage in F1. The model does not assert unconditional gain. -/
theorem no_direct_same_n0_work
    (p : RoutingPolicy) (q : RoutingDemand)
    (h : ¬ DirectIngress p q.source q.record q.domain) :
    n0Units (routeF1 p q) = n0Units (routeC2 p q) := by
  rw [no_direct_same_route p q h]

/-- Direct N1 ingress remains possible while the central entry point is down,
    conditional on an authorized and available direct international connection. -/
theorem route_available_without_n0
    (p : RoutingPolicy) (q : RoutingDemand)
    (hn0 : ¬ p.n0Available)
    (hd : DirectIngress p q.source q.record q.domain) :
    routeF1 p q = .directN1 ∧ routeC2 p q = .noRoute := by
  constructor
  · simp [routeF1, hd]
  · have hno : ¬ C2Ingress p q.source q.record q.domain := by
      intro h
      exact hn0 h.1
    simp [routeC2, hno]

end WorldCIST27

-- Audit kernel axioms for all 10 theorems. No sorryAx is acceptable.
#print axioms WorldCIST27.centralized_vs_federated
#print axioms WorldCIST27.federated_operational_path_when_n0_unavailable
#print axioms WorldCIST27.single_request_decomposition
#print axioms WorldCIST27.n0_load_decomposition
#print axioms WorldCIST27.federated_n0_not_greater
#print axioms WorldCIST27.federated_n0_strictly_less_if_bypass
#print axioms WorldCIST27.strictly_less_with_eligible_direct_request
#print axioms WorldCIST27.no_direct_same_route
#print axioms WorldCIST27.no_direct_same_n0_work
#print axioms WorldCIST27.route_available_without_n0
