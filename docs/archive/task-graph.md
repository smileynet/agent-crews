# Self-Hosted Plan — Task Graphs

## Master Plan DAG

Execution order: 2 → 3 → (1 ∥ 4) → 5 → FINAL

```mermaid
graph LR
    P2[Phase 2: Meta Crew] --> P3[Phase 3: Fleet Wiring]
    P3 --> P1[Phase 1: Data Separation]
    P3 --> P4[Phase 4: Doc Restructure]
    P1 --> P5[Phase 5: Hygiene Validation]
    P4 --> P5
    P5 --> FINAL[FINAL: Generate Examples]

    %% PARALLEL: Phase 1 and Phase 4 can run simultaneously after Phase 3
```

| Phase | Depends On | Notes |
|-------|-----------|-------|
| Phase 2 (Meta Crew) | — | Entry point, no deps |
| Phase 3 (Fleet Wiring) | Phase 2 | Needs meta.yaml |
| Phase 1 (Data Separation) | Phase 3 | ∥ with Phase 4 |
| Phase 4 (Doc Restructure) | Phase 3 | ∥ with Phase 1 |
| Phase 5 (Hygiene Validation) | Phase 1, Phase 4 | Join point |
| FINAL (Generate Examples) | Phase 5 | Terminal |

---

## Phase 2 — Meta Crew

```mermaid
graph TD
    2_1[2.1 Extract agent prompts from .kiro/agents/*.json]
    2_2[2.2 Extract prompt content from .kiro/prompts/*.md]
    2_3[2.3 Design project-hygiene agent prompt]
    2_4[2.4 Write meta.yaml workflow/scope/tools]
    2_5[2.5 Write meta.yaml orchestrator archetype]
    2_6[2.6 Write meta.yaml worker archetype]
    2_7[2.7 Write meta.yaml prompts section]
    2_8[2.8 Validate meta.yaml structure]

    2_1 --> 2_5
    2_1 --> 2_6
    2_3 --> 2_6
    2_2 --> 2_7
    2_4 --> 2_8
    2_5 --> 2_8
    2_6 --> 2_8
    2_7 --> 2_8

    %% PARALLEL: 2.1, 2.2, 2.3, 2.4 can all start immediately
    %% PARALLEL: 2.5, 2.6, 2.7 can run in parallel once their deps resolve
```

---

## Phase 3 — Fleet Wiring

```mermaid
graph TD
    3_1[3.1 Add self_hosted flag to generate.py]
    3_2[3.2 Add fleet.example.yaml reading]
    3_3[3.3 Create fleet.example.yaml]
    3_4[3.4 Add meta crew exception to generator]
    3_5[3.5 Run just build agent-crews]
    3_6[3.6 Diff generated vs hand-crafted .kiro/]
    3_7[3.7 Run idempotency test]
    3_8[3.8 Verify other projects still generate]

    3_1 --> 3_5
    3_2 --> 3_5
    3_3 --> 3_5
    3_4 --> 3_5
    3_1 --> 3_8
    3_2 --> 3_8
    3_4 --> 3_8
    3_5 --> 3_6
    3_5 --> 3_7

    %% PARALLEL: 3.1, 3.2, 3.3, 3.4 can all run in parallel (independent changes)
    %% PARALLEL: 3.6, 3.7, 3.8 can all run in parallel after their deps
```

---

## Phase 1 — Data Separation

```mermaid
graph TD
    1_1[1.1 Update .gitignore]
    1_2[1.2 git rm --cached fleet.yaml]
    1_3[1.3 git rm --cached -r projects/]
    1_4[1.4 Verify fleet.example.yaml has no personal data]
    1_5[1.5 Update README.md references]
    1_6[1.6 Verify just build still works]
    1_7[1.7 Grep committed files for personal names]

    1_1 --> 1_2
    1_1 --> 1_3
    1_2 --> 1_6
    1_3 --> 1_6
    1_2 --> 1_7
    1_3 --> 1_7

    %% PARALLEL: 1.2, 1.3 can run in parallel (both depend only on 1.1)
    %% PARALLEL: 1.4, 1.5 are independent — can run alongside everything
    %% PARALLEL: 1.6, 1.7 can run in parallel after 1.2+1.3
```

---

## Phase 4 — Doc Restructure

```mermaid
graph TD
    4_1[4.1 Rewrite README.md]
    4_2[4.2 Scrub AGENTS.md]
    4_3[4.3 Update AGENTS.md agent roster]
    4_4[4.4 Update AGENTS.md prompt list]
    4_5[4.5 Create CONTRIBUTING.md]
    4_6[4.6 Verify all internal links resolve]

    4_1 --> 4_6
    4_2 --> 4_6
    4_3 --> 4_6
    4_4 --> 4_6
    4_5 --> 4_6

    %% PARALLEL: 4.1, 4.2, 4.5 can all run in parallel (independent)
    %% PARALLEL: 4.3, 4.4 can run in parallel (both need Phase 3 output, available at phase start)
    %% All of 4.1–4.5 can run in parallel; 4.6 is the join gate
```

---

## Phase 5 — Hygiene Validation

```mermaid
graph TD
    5_1[5.1 Data separation checks 1-6]
    5_2[5.2 Meta crew checks 7-9]
    5_3[5.3 Generation checks 10-12]
    5_4[5.4 Documentation checks 13-19]
    5_5[5.5 Fix BLOCKING/DRIFT findings]
    5_6[5.6 Create CI validation script]

    5_1 --> 5_5
    5_2 --> 5_5
    5_3 --> 5_5
    5_4 --> 5_5
    5_5 --> 5_6

    %% PARALLEL: 5.1, 5.2, 5.3, 5.4 ALL run in parallel (independent check groups)
```

---

## FINAL — Generate Examples

```mermaid
graph TD
    F_1[F.1 Generate example projects from fleet.example.yaml]
    F_2[F.2 Copy generated output to examples/]
    F_3[F.3 Create examples/README.md]
    F_4[F.4 Validate example agents are valid JSON]
    F_5[F.5 Run Phase 5 checks 20-23 against examples/]

    F_1 --> F_2
    F_2 --> F_4
    F_2 --> F_5

    %% PARALLEL: F.3 is independent — can run alongside F.1/F.2
    %% PARALLEL: F.4, F.5 can run in parallel after F.2
```
