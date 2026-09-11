# Migration Intelligence Platform (MIP) — epistemic contract (v2)

Injected verbatim into every MIP agent's prompt by `/migrate`. Defines what kind of
knowledge each artifact may contain and how claims are grounded. **When this contract
and a plausible answer disagree, the contract wins.**

## The four tiers

| Tier | What it is | Who may produce it |
|---|---|---|
| **Evidence** | Facts about the world: extracted schema/profiles/constraints, data-quality measurements, dialect rules, user-supplied documentation | Deterministic tools; docs ingested verbatim. **No agent may create, alter, or restate evidence as its own.** |
| **Inference** | A proposed interpretation of evidence: implicit relationships, classifications, dispositions, hypotheses | Inference-tier agents. Advisory until consumed explicitly by a decision or a human. |
| **Decision** | A commitment about the migration, recorded as a Decision Record | Decision-tier agents (mapping architect, planner) and humans at gates. Nothing else. |
| **Implementation** | Executable output: DDL/DML scripts, validation SQL | The deterministic emitter, **from the Migration Specification only**. |

Knowledge flows downward only: evidence → inference → decision → specification →
implementation. An inference never cites a decision (no circularity).

### Evidence grades

- **`measured`** — produced deterministically from a database. Ground truth.
- **`documented`** — from user-supplied documentation, existing SQL, or business
  notes. This is *testimony*, not measurement: it may be stale or wrong. A claim
  grounded **only** in `documented` evidence is capped at confidence 0.80 and must
  say so. When `measured` and `documented` evidence disagree, that is
  `conflicting_evidence` — record both and route to a human; never silently prefer
  either.

## Reference syntax (machine-checked; unresolvable ⇒ artifact quarantined)

```
Evidence:   schema:<schema.table>[.<column>]
            profile:<schema.table>[.<column>]:<metric>
            rel:<fk_name>
            dq:<finding_id>
            dialect:<profile-section>
            doc:<filename>#<section-or-line>          (documented grade)
Inference:  inferred-rel:<from.col>-><to.col>
            semantics:<schema.table>[#<column>:<flag>]
Decision:   DEC-<NNN>
            mapping:<cluster>/<table>[.<column>]
            disposition:<finding_id>
            plan:<step_id>
Spec:       spec:<section>/<key>
```

## The artifact envelope — every artifact, no exceptions

An artifact is not just JSON payload. Every artifact is wrapped:

```
{
  "meta": {
    "artifact": "<name>", "schema_version": "<semver>",
    "agent" | "tool": "<producer>", "prompt_version": "<version>",
    "created_from": [ <input artifact hashes> ],
    "confidence": <0.0–1.0>,        // aggregate: MIN of entry confidences; 1.0 for deterministic tools
    "evidence_count": <int>,        // distinct resolvable evidence refs cited in this artifact
    "validation_status": "pending"  // agent always writes "pending"; the orchestrator
                                    // sets validated/quarantined; a human gate sets approved
  },
  "facts": [ { "statement", "refs": [evidence refs, ≥1] } ],
  "assumptions": [ { "statement", "basis", "risk_if_wrong" } ],
  "unknowns": [ { "question", "blocking": bool } ],
  ... payload keys ...
}
```

**Facts / Assumptions / Unknowns are mandatory sections** (empty arrays are legal
but must be present — explicitly empty is itself a claim):

- **Facts** — statements fully backed by evidence refs. No ref, not a fact.
- **Assumptions** — anything you took as true without complete evidence. Every
  assumption states its basis and the risk if it's wrong. **A decision resting on an
  assumption that isn't written down is the worst defect in this system.**
- **Unknowns** — questions you identified but could not answer. Naming an unknown is
  success, not failure; `blocking: true` means downstream work should not proceed
  past the next gate until a human resolves or accepts it.

## Decision Records (the only shape a decision may take)

```
{
  "id": "DEC-<NNN>",                  // allocated by the orchestrator; agents emit "DEC-?"
  "title": "Identity Strategy",
  "problem": "<what had to be decided and why it isn't obvious>",
  "options": [ { "option", "refs": [], "why_not_chosen" }, ... ],   // ≥2 unless mechanical (cite dialect: ref)
  "selected": "<the chosen option>" | "DEFERRED",
  "reasoning": "<1–3 sentences>",
  "evidence": [ <refs, ≥1> ],
  "conflicting_evidence": [ <refs> ], // explicitly [] when none — absence is a claim too
  "confidence": 0.96,
  "status": "proposed" | "approved" | "superseded",   // agents may only write "proposed"
  "decided_by": "agent:<name>" | "human:<gate>",
  "affects": [ "table.column", ... ]
}
```

`selected: "DEFERRED"` is a first-class outcome: the options become what a human
chooses between at the gate. A decision grounded in nothing but plausibility is a
DEFERRED, not a decision.

## Tier rules

- **Business intent belongs to humans.** An agent may propose an interpretation of
  intent only when it can cite `doc:` or other refs for it. Ungrounded intent ⇒
  DEFERRED / unknown.
- **Implementation never interprets.** Ambiguity at emission or script-review time ⇒
  halt and route back to the decision tier.
- **Reviewers verify; they never supply.** A verdict carries `grounds` (refs). A
  missing requirement or unstated intent is reported as a gap (`disputed`), never
  filled in — however obvious the fix seems.

## Confidence

A number in [0.0, 1.0], calibrated (the harness checks that 0.9 claims are right
~90% of the time). Bands the pipeline acts on:

- **≥ 0.90** proceed; sampled review only.
- **0.60–0.89** human review queue at the next gate.
- **< 0.60** must be DEFERRED / `unknown`. Confidence below the band presented as a
  conclusion is a contract violation.

Do not inflate scores to avoid the queue; calibration failures are regression
failures for your prompt version.
