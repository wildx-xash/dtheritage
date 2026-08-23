# TEAMMATES.MD

# SIH 2026 — Heritage & Culture Project Handoff / Team Execution Context

> **Purpose of this file**
>
> This is the single handoff/context file for continuing the SIH 2026 Heritage project in a fresh ChatGPT/Claude session without losing prior decisions, experiments, scope boundaries, team workflow, or deliverables.
>
> **Important:** The project is already past ideation and early feasibility. Do **not** restart from broad brainstorming or generic prior-art research unless a new technical result forces it.

> **Current execution status (authoritative, 2026-08-23).** Person 2/3 work is
> complete: Humayun reached `LOCAL_GEOMETRY_STILL_REQUIRED`, then
> `BOUNDED_REGISTRATION_SUFFICIENT_FOR_CHANGE_EVIDENCE`, then
> `CHANGE_EVIDENCE_PIPELINE_VIABLE`; Sanchi's gateway workflow is complete;
> Qutb is a documented hard case with no permitted change evidence. Historical
> "paused", "not started", and "next experiment" sections below are retained
> as experiment history, not current instructions. Remaining work is team
> integration: Person 4's Supabase data layer and Person 5's static dashboard
> are now connected to the verified portfolio records. The next work is review
> persistence, asset storage/provenance completion, presentation packaging, and
> final end-to-end testing. Do not redo completed Humayun experiments.

> **Supabase integration status.** The `monuments`, `images`,
> `registrations`, `evidence_candidates`, and `evidence_reviews` tables exist
> with RLS enabled. `scripts/seed_supabase.py` imports the tracked artifact
> bundle using a local, Git-ignored `.env.local`. The browser receives only the
> Project URL and anon/publishable key in `frontend/supabase-config.js`; never
> expose the service-role key. The dashboard must preserve 8 Humayun candidates,
> 11 Sanchi candidates, and Qutb's rejected registration with zero candidates.

> **Current dependency.** Verified Person 2/3 outputs flow to Person 4/backend
> consumption and Person 5/frontend consumption, then to lead integration and
> PPT/demo/project packaging. Backend/frontend integration is not yet complete.

---

# 1. Hackathon Context

We are in the **execution phase for SIH 2026 internal hackathon**.

## Team
- Team size: **6**
- Time available: **1 week**
- Goal: deliver a convincing working **first prototype** for the internal round.

## Required deliverables
We need all of the following by the end of the week:

1. Working prototype
2. GitHub repository
3. PPT / pitch deck
4. Demo video
5. Project description / SIH write-up
6. Supporting architecture / methodology / evaluation material
7. Honest limitations + failure-case evidence

This is a serious SIH project. Scope must be controlled aggressively.

---

# 2. Final Problem Statement Selected

## Theme
**Heritage & Culture**

## Working Title
**Archival-Baseline Conservation Intelligence for Indian Heritage Structures**

## Core Problem

Develop an archival-baseline conservation intelligence system for Indian protected monuments that:

- registers heterogeneous and uncalibrated historical and contemporary imagery into a temporal stack;
- uses 19th–20th century archival photographs, institutional images, and modern crowd photographs;
- detects visible condition changes over time;
- classifies changes by type;
- attaches provenance, source date, method, and confidence/uncertainty to every detected change;
- produces uncertainty-bounded change indicators;
- generates a ranked intervention / inspection priority list across a portfolio of monuments;
- supports conservation budgeting and condition reporting.

## Target Stakeholders

- ASI Conservation Assistants
- Superintending Archaeologists
- State Archaeology Departments
- National Monuments Authority
- INTACH chapters
- Conservation officers managing many monuments with limited staff/budget

---

# 3. What Makes the Project Defensible

This is **NOT**:

- “AI detects cracks in monuments”
- generic crack detection
- before/after image slider
- generic image registration
- generic damage detection
- crowd-photo monitoring by itself
- AR/VR monument tourism
- a single-site IoT monitoring system
- a digital twin project

## Defensible differentiator

The project is centered on:

1. **Archival baseline**
   - old uncalibrated images
   - unknown focal length
   - no EXIF
   - different cameras
   - different viewpoints
   - different lighting
   - modern crowd photographs

2. **Provenance-tracked temporal evidence**
   - every change claim links back to its source/evidence

3. **Uncertainty-aware analysis**
   - no fake millimetre precision
   - no false structural diagnosis from arbitrary photos

4. **Human-in-the-loop review**
   - evidence, not autonomous conservation decisions

5. **Portfolio-level prioritisation**
   - help decide where scarce human inspection/conservation resources should go first

6. **Heritage significance remains configurable by humans**
   - AI must not decide cultural value as if it were objective

## Core pitch sentence

> We turn decades of already-existing archival and contemporary imagery into an auditable conservation history and help officers decide where limited inspection and conservation resources should go first.

---

# 4. Scientific Claims We Must NOT Make

Never claim:

- millimetre-level measurement from arbitrary historical photographs;
- exact physical deterioration measurements unless properly calibrated;
- structural diagnosis from visual difference alone;
- that every pixel difference equals damage;
- that the AI replaces conservators;
- that a numerically returned homography means valid registration;
- that low RANSAC inlier reprojection error alone proves alignment;
- that cultural significance is automatically inferred by AI.

Preferred language:

- visible change evidence
- relative change indicators
- scale-normalised evidence
- confidence / uncertainty
- candidate change region
- human review
- inspection prioritisation
- bounded registration validity

---

# 5. Planned 3-Monument Scope

The project is **NOT only Humayun's Tomb**.

The intended SIH prototype is a **3-monument portfolio**.

Current experimental shortlist:

1. **Humayun's Tomb**
   - Monument #1
   - current technical testbed
   - strong archival + modern imagery
   - documented conservation history
   - best current feasibility evidence

2. **Sanchi Stupa / Toranas**
   - excellent archival imagery
   - gateway/torana geometry may be easier for planar registration
   - documented restoration history
   - strong validation story

3. **Qutb Minar / Qutb Complex**
   - large historical record
   - difficult geometry/viewpoint case
   - good “hard example”

The final demo should eventually show all 3 monuments, not only Humayun.

---

# 6. Data / Image Strategy

## General rule

Do **not** bulk-download hundreds of images.

We need a small curated set of useful pairs.

For each image preserve:

- filename
- monument
- year/date
- author/photographer
- archive/source
- source URL
- license
- viewpoint
- notes

Provenance later becomes part of the product UI/evidence ledger.

## Data sources already identified

Useful sources include:

- Wikimedia Commons
- British Library-related archival records
- Rijksmuseum
- Metropolitan Museum of Art
- UNESCO World Heritage pages
- ASI / conservation documentation where accessible

## Downloader incident

Automated Wikimedia bulk downloads triggered HTTP **429 Too Many Requests**.

Decision:
- stop spending time fighting download automation;
- manual/curated downloading is acceptable;
- for technical testing, modest-resolution images are enough;
- full-resolution final assets can be downloaded only after pair selection.

This is NOT a current technical blocker.

---

# 7. Repository / Local Environment

Current repo:

```text
sih-heritage/
├── data/
│   └── humayun/
│       ├── archival.jpg
│       └── modern.jpg
│
├── experiments/
│   └── registration/
│
├── outputs/
│   └── registration/
│
├── src/
│   └── registration/
│       ├── sift_baseline.py
│       ├── sift_improved.py
│       └── loftr_baseline.py
│
├── .gitignore
├── CLAUDE.md
├── README.md
└── requirements.txt
```

## Python / dependencies

Current direct dependencies:

```text
--extra-index-url https://download.pytorch.org/whl/cpu
numpy==2.5.2
opencv-python==5.0.0.93
torch==2.13.0+cpu
kornia==0.8.3
certifi==2026.7.22
```

LoFTR uses:

- Kornia 0.8.3
- PyTorch 2.13.0+cpu
- `LoFTR(pretrained='outdoor')`
- MegaDepth outdoor weights

Weights are cached locally.

CPU inference is currently ~5 seconds per pair, which is acceptable for the prototype.

## `.gitignore`

Confirmed working for:

```gitignore
.venv/
__pycache__/
*.pyc
outputs/
```

There was a discussion about optionally version-controlling `metrics.json` while keeping images ignored, because metrics are the scientific experiment record.

## requirements cleanup

- `requirements.txt` is now valid UTF-8 and contains direct dependencies.
- the obsolete UTF-16LE `requirements-temp.txt` full freeze was removed; use the direct runtime dependencies in `requirements.txt`.

---

# 8. Claude Code / ECC Workflow

The user works in VS Code with **Claude Code + ECC**.

ECC is configured user-wide with learning-first behavior.

## Important user preference

**Cue the user explicitly whenever Claude Code should be used.**

Do not silently assume Claude should do every task.

## Repo-level `CLAUDE.md`

`CLAUDE.md` is populated and should be treated as the project-specific engineering constitution.

Its main rules:

- current phase = technical feasibility / registration;
- preserve previous experiments;
- no product UI/backend/database during current feasibility;
- no fake confidence scores;
- negative experiments are valid;
- do not overwrite original input images;
- preprocessing must be reproducible;
- geometric validity must be checked explicitly;
- separate matching success from geometry success;
- do not rerun or alter completed Person 2/3 experiments unless reproducibility verification requires it;
- aggressively reject unrelated scope.

If Claude ever says `CLAUDE.md` is empty, verify the actual saved file in the repo instead of trusting stale Claude context.

---

# 9. Technical Feasibility Progress So Far

We have already completed **three registration experiments** on a real Humayun archival-modern pair.

---

# 9.1 Experiment 1 — Vanilla SIFT

## Pipeline

```text
historical image
→ grayscale
→ SIFT
→ descriptor matching
→ Lowe ratio test
→ RANSAC
→ homography
→ warp / overlay
```

## Result
**FAILURE**

## Important measured results

- archival original: 4000 × 3209
- modern original: 1920 × 1080
- archival working: 1600 × 1284
- modern working: 1600 × 900
- archival SIFT keypoints: **17,294**
- modern SIFT keypoints: **5,344**
- good matches after ratio test: **83**
- RANSAC inliers: **9**
- inlier ratio: **0.108**
- inlier hull area: **1.1%**
- all-good-match RMSE: ~**431 px**
- warped archival frame collapsed geometrically
- homography invalid / degenerate

## Interpretation

SIFT detection worked.

The failure occurred at **cross-era descriptor matching**.

The surviving matches were largely wrong and spatially clustered.

A key lesson:

> Very low reprojection error over RANSAC-selected inliers can still correspond to a completely broken registration.

---

# 9.2 Experiment 2 — Improved Classical SIFT

## Improvements tested

1. CLAHE photometric normalisation
2. RootSIFT
3. reproducible ROI restriction
4. mutual / bidirectional matching
5. robust geometric verification

## Result
**FAILURE**

## Important metrics

- archival/modern keypoints after ROI: ~8,528 / 5,746
- forward filtered matches: **34**
- reverse filtered matches: **110**
- mutual matches: **9**
- geometric inliers: **4**
- inlier ratio: **0.444**, but meaningless at such tiny N
- spatial coverage: **3.0%**
- homography: invalid
- all 9 mutual match RMSE: ~**415 px**
- transform still degenerate

## Interpretation

The improved pipeline removed the easy excuses:

- contrast mismatch
- descriptor bin dominance
- irrelevant foreground
- asymmetric matches

It still failed.

Conclusion:

> Further classical SIFT tuning is not justified for this image pair.

---

# 9.3 Experiment 3 — LoFTR Outdoor

## Implementation

- Kornia 0.8.3
- PyTorch 2.13.0+cpu
- `LoFTR(pretrained='outdoor')`
- MegaDepth weights
- inference max dimension: 840 px
- aspect ratio preserved

## Result
# **SUCCESS — LOFTR_REGISTRATION_VIABLE**

This is the first major technical win.

## Actual metrics

- total predicted correspondences: **658**
- confidence range: **0.200–0.996**
- fixed confidence threshold: **0.50**
- filtered correspondences: **345**
- RANSAC inliers: **182**
- inlier ratio: **0.528**
- inlier hull coverage: **5.18% of archival frame**
- MAGSAC cross-check: **223 inliers**
- homography condition number: ~**1.90e4**
- warped quad: convex
- warped area ratio: ~**2.69×**
- implied rotation: ~**0.65°**
- inlier reprojection RMSE: ~**1.667 px**
- max inlier reprojection error: ~**2.991 px**
- all-filtered RMSE: ~**25.2 px**
- NCC: ~**0.292**
- runtime: ~**5.21 s total**
- LoFTR inference: ~**4.80 s**

## Critical comparison

| Metric | Vanilla SIFT | Improved SIFT | LoFTR |
|---|---:|---:|---:|
| usable/filtered matches | 83 | 9 mutual | 345 |
| geometric inliers | 9 | 4 | **182** |
| inlier ratio | 0.108 | 0.444 of only 9 | **0.528** |
| valid homography | No | No | **Yes** |
| runtime | ~1.15 s | ~1.15 s | ~5.21 s |

## Visual interpretation

LoFTR correctly matched:

- central iwan
- framing bands
- star medallions
- flanking bays
- parapet line
- chhatri bases
- plinth arcade
- facade boundaries

It mostly avoided:

- modern tourists
- lawn/path
- changed garden foreground

This confirms that the architectural correspondence information was present in the images; SIFT simply could not represent/match it reliably.

---

# 10. Historical Limitation Discovered After Initial LoFTR

Matching is now strong.

The remaining problem is **global geometry**.

## What aligns well

- main facade
- central iwan
- arcade / facade bands
- left/right structure extent

## What does not align well

- dome
- ground / garden plane
- vertically distant regions from the main inlier support

## Why

The current single homography is supported mainly by a horizontally wide but vertically thin band.

Reported inlier support:

- horizontal spread: strong
- vertical spread: only about **18%** of archival height

The dome and ground live at different depths relative to the facade, so residual parallax/viewpoint differences remain.

Important conclusion:

> A single global homography models the facade reasonably well, but not necessarily the full 3D monument/ground scene.

This is NOT yet a failure of the overall project.

---

# 11. Historical Pair-Selection Decision (Completed)

Originally the next step was going to be:

- trust-region estimation;
- local/piecewise registration.

That decision was paused pending a small multi-pair check, which has now been
completed.

## Reason

We currently have only **one archival-modern Humayun pair** tested with LoFTR.

Therefore we do NOT yet know whether:

A. the limited vertical support is inherent geometry/parallax,

or

B. we simply selected a mediocre modern viewpoint.

## Historical next step and completed outcome

# **MULTI-PAIR LOFTR ROBUSTNESS / PAIR-SELECTION TEST**

Before implementing trust-region/local registration:

1. collect/use multiple sensible archival-modern Humayun combinations;
2. run the **same LoFTR pipeline unchanged**;
3. keep thresholds fixed across pairs;
4. compare geometry objectively.

Suggested small matrix:

```text
Archival A1
├── Modern M1
├── Modern M2
└── Modern M3

Archival A2
├── Modern M1
└── Modern M2
```

Approximately 4–5 pairs are enough.

Do NOT build a huge dataset.

Actual outcome: `LOCAL_GEOMETRY_STILL_REQUIRED`. The best Humayun pair still
required bounded/local trust-region registration before change evidence.

---

# 12. Historical Metrics Plan for Multi-Pair Comparison

For every pair compare:

- total LoFTR correspondences
- filtered correspondences
- RANSAC inliers
- inlier ratio
- homography validity
- horizontal support
- vertical support
- spatial hull coverage
- reprojection statistics
- transform sanity
- independent overlap/NCC
- visual alignment of:
  - facade
  - dome
  - arcade
  - ground

## Decision must be based on geometry, not raw match count.

The experiment should finish with exactly one of:

### `PAIR_SELECTION_IMPROVES_GEOMETRY`

Use if another historical-modern viewpoint materially improves full-structure support/alignment.

### `LOCAL_GEOMETRY_STILL_REQUIRED`

Use if all reasonable pairs still produce:
- good facade registration;
- limited dome/ground alignment;
- insufficient vertical support.

---

# 13. Historical Trust-Region Plan (Completed)

Claude previously started designing a trust-region experiment based on:

- LoFTR inlier/reject residuals
- spatial residual mapping
- grid support
- cross-validation
- TRUSTED / MARGINAL / UNTRUSTED / UNSUPPORTED tiers

This was completed after the multi-pair result. The final outcome was
`BOUNDED_REGISTRATION_SUFFICIENT_FOR_CHANGE_EVIDENCE`; trust tiers now gate
candidate extraction.

Also note:

A high-confidence LoFTR match rejected by RANSAC is **not automatically a genuine parallax correspondence**. It may still be a wrong match.

Therefore any future trust-region method must not assume every high-confidence RANSAC reject is valid physical correspondence.

---

# 14. Historical Change-Detection Plan (Completed)

This gate has been satisfied only inside trusted/recoverable bounded regions.
Candidate visible-change extraction is complete for Humayun and Sanchi, while
Qutb remains intentionally suppressed because its supplied geometry is invalid.

Why:

A poor full-frame warp would cause:

- dome edges
- ground
- vegetation
- shadows
- viewpoint differences

to appear as giant false “changes”.

## Implemented pipeline

```text
registered pair
→ photometric normalisation
→ structural/pixel difference
→ candidate change regions
→ noise filtering
→ confidence / uncertainty
→ human review
→ evidence ledger
```

Output should be called:

**candidate change evidence**

not:

**damage diagnosis**

---

# 15. Manual Registration Fallback — Planned

If automatic registration confidence/support is insufficient, the product should support human-guided landmarks.

Example:

```text
Automatic registration confidence/support insufficient
→ user confirms corresponding landmarks
→ guided alignment
```

Potential landmarks:

- dome apex
- central iwan corners
- parapet corners
- facade/window intersections
- gateway corners

This is not considered “cheating”.

Human-in-the-loop fallback is consistent with the scientific framing.

---

# 16. Planned MVP Product — AFTER FEASIBILITY

The eventual internal-round demo should be approximately:

```text
Portfolio dashboard
→ choose monument
→ archival image + source/date
→ modern image
→ registration
→ validated comparison region
→ candidate change evidence
→ confidence / provenance
→ human Accept / Reject / Reclassify
→ evidence ledger
→ updated conservation/inspection priority
```

## Expected final screens

1. Portfolio / priority dashboard
2. Monument timeline/detail
3. Historical-modern comparison
4. Evidence review card
5. Provenance / uncertainty display
6. One-page conservation dossier

Only build the UI after the technical registration/change pipeline is proven enough.

---

# 17. Intended Priority Engine — Later

Potential prototype idea:

```text
Priority =
Change Severity
× Evidence Confidence
× Persistence
× Human-defined Heritage Significance
```

Exact formula is not frozen.

Important:

- heritage significance must be user-configurable;
- AI should not autonomously determine cultural value;
- priority must be transparent/explainable.

---

# 18. Team of 6 — Working Structure

Exact teammate names are not recorded here yet, but the intended responsibility split is:

| Role | Primary responsibility |
|---|---|
| Person 1 — Lead / Integration | architecture, Git, integration, scope control, final prototype | integration in progress |
| Person 2 — Registration CV | LoFTR, geometry, registration experiments, bounded/local registration | complete |
| Person 3 — Change Intelligence | candidate evidence, evidence strength, uncertainty, false-positive analysis, evaluation | complete |
| Person 4 — Data / Backend | provenance, metadata, evidence storage/APIs | separate backend integration dependency |
| Person 5 — Frontend | dashboard, timeline, comparison, evidence-review UI | integration in progress |
| Person 6 — Research / Validation / Pitch | research, evaluation narrative, PPT/demo material | in progress |

## Current teammate involvement

At the present integration stage:

### Completed Person 2/3 contribution

- Humayun: SIFT failure -> improved SIFT failure -> LoFTR -> multi-pair
  analysis -> `LOCAL_GEOMETRY_STILL_REQUIRED` -> bounded trust regions ->
  `BOUNDED_REGISTRATION_SUFFICIENT_FOR_CHANGE_EVIDENCE` -> candidate evidence
  -> `CHANGE_EVIDENCE_PIPELINE_VIABLE`.
- Sanchi: reproducible eastern-gateway workflow completed with 566 filtered
  correspondences, 358 inliers, bounded registration sufficient, and 11
  human-review candidates.
- Qutb: supplied viewpoints fail fixed registration validity gates; unsupported
  change evidence is intentionally suppressed rather than manufactured.

### Active integration work

- Lead: integrate verified outputs into the final prototype.
- Person 4: consume provenance/metadata/evidence exports in the existing
  backend workstream.
- Person 5: consume candidate, trust, and hard-case outputs in the UI.
- Person 6: package evaluation narrative, PPT, demo, and limitations.

---

# 19. 7-Day Execution Intent

The original 7-day structure remains:

## Day 1
- data
- registration feasibility
- one real archival-modern pair
- architecture only after core feasibility

## Day 2
- registration reliability
- automatic + fallback approach
- pair robustness

## Day 3
- candidate change evidence
- human review

## Day 4
- end-to-end integration
- priority layer

## Day 5
- validation
- false positives
- polish

## Day 6
- PPT
- README
- architecture
- methodology
- project description
- rehearsal

## Day 7
- feature freeze
- bug fixes
- clean install
- GitHub cleanup
- demo video
- final pitch package

Because the technical feasibility work has taken several iterations, the schedule should be adapted pragmatically, but the main rule remains:

> By the final 2–3 days, major feature development should be frozen.

---

# 20. Hard Scope Fence

## Build for internal round

- 3 monuments
- curated archival/modern pairs
- cross-era registration
- registration diagnostics
- bounded/trusted comparison
- provenance
- candidate change evidence
- human review
- evidence ledger
- simple ranking/priority
- polished web demo
- evaluation
- PPT/video/project description

## Do NOT build unless absolutely necessary

- 3D reconstruction
- digital twin
- AR/VR
- drones
- IoT
- mobile app
- giant crawler
- custom deep model
- fine-tuning
- RAG
- chatbot
- blockchain
- complex authentication
- complex cloud infra
- autonomous conservation diagnosis
- “all monuments of India”

---

# 21. Best Current Technical Story for PPT

This is already strong:

```text
1860 archival Humayun image
        vs
modern Humayun image

Vanilla SIFT
→ 9 bad inliers
→ invalid homography

Improved SIFT
→ 4 inliers
→ invalid homography

LoFTR Outdoor
→ 658 predicted correspondences
→ 345 filtered
→ 182 RANSAC inliers
→ 0.528 inlier ratio
→ valid homography
→ facade aligns convincingly
```

This gives us a real experimental narrative:

> Classical matching failed across a ~160-year photographic domain gap. A learned detector-free matcher recovered genuine architectural correspondences. The next challenge is not matching anymore; it is choosing/validating geometry across different viewpoints and depth planes.

This is far stronger than a generic “AI architecture” slide.

---

# 22. Current Exact Next Action

1. Person 4 consumes the verified provenance/registration/evidence exports.
2. Person 5 consumes the same outputs, including Qutb's geometry-rejected state.
3. Lead integrates the end-to-end prototype without changing Person 2/3 science.
4. Person 6 packages evaluation, limitations, PPT, and demo material.

---

# 23. Historical Claude Code Cue — Pair-Selection Task (Completed)

**Claude SHOULD be used** once the additional Humayun images are in `data/`.

Suggested prompt:

```text
Read CLAUDE.md and the successful LoFTR baseline first.

Before introducing trust-region or local registration, test whether the limited
geometric support is partly caused by our choice of historical-modern image pair.

Discover the available Humayun archival and modern images under data/, then run
the existing LoFTR pipeline reproducibly across a small set of sensible
archival-modern combinations without changing model thresholds per pair.

Compare correspondence count, geometric inliers, inlier ratio, horizontal and
vertical support, homography validity, reprojection statistics, transform sanity
and independent overlap/NCC.

Rank the pairs by geometric registration quality rather than raw match count.

Finish with exactly one conclusion:

PAIR_SELECTION_IMPROVES_GEOMETRY

or

LOCAL_GEOMETRY_STILL_REQUIRED

Do not implement trust-region analysis, local warping or change detection yet.
```

---

# 24. User Workflow / Collaboration Preference

For future ChatGPT sessions:

- aggressively control scope;
- explicitly tell the user **when Claude Code should be used**;
- do not ask the user to repeat context already present in this file;
- prefer technical gates over speculative architecture;
- preserve negative results;
- do not let Claude silently broaden the task;
- keep explanations practical and execution-focused;
- remember this is a **team-of-6, 3-monument SIH project**, not a single-image research notebook;
- remember the final package includes **prototype + GitHub + PPT + demo video + project description**.

---

# 25. New Chat Start Instruction

When this file is supplied to a new ChatGPT session, continue from:

> **Integration: consume verified three-monument Person 2/3 outputs without
> rerunning or changing completed CV/change-intelligence experiments.**

Do NOT restart:

- problem-statement selection;
- generic SIH theme exploration;
- broad prior-art analysis;
- SIFT feasibility;
- LoFTR baseline.

Those are already complete.

The immediate strategic dependency is Person 4/backend and Person 5/frontend
consumption of the tracked verification artifacts and reproducible exports.

---

# 26. Current Status Summary

```text
Humayun Person 2/3 pipeline
    ✅ completed and reproducible

Sanchi gateway Person 2/3 pipeline
    ✅ completed and reproducible

Qutb supplied-viewpoint hard case
    ✅ documented; geometry rejected and no candidates generated

Person 4/backend consumption
    ⏭ integration dependency

Person 5/frontend consumption
    ⏭ integration in progress

Lead prototype integration and PPT/demo packaging
    ⏭ current milestone
```

---

# END OF HANDOFF

**Current milestone: integrate verified Person 2/3 outputs into the end-to-end
prototype and presentation package.**
