# DTHeritage — SIH 2026

**Archival-Baseline Conservation Intelligence for Indian Heritage Structures**

DTHeritage is an SIH 2026 internal-round prototype that turns archival and contemporary monument photographs into **auditable conservation evidence**.

The system is being designed to:

- register historical and modern imagery;
- identify where visual comparison is geometrically trustworthy;
- surface candidate visible changes with provenance and uncertainty;
- keep a human conservator in the loop;
- help prioritize inspection across a small portfolio of monuments.

> This is **not** autonomous structural diagnosis and does not claim millimetre-level measurement from arbitrary historical photographs.

---

## Current Status

We are currently in the **registration feasibility phase**.

| Experiment | Result | Outcome |
|---|---|---|
| Vanilla SIFT | ❌ Failed | Cross-era descriptor matching unreliable |
| Improved SIFT | ❌ Failed | CLAHE + RootSIFT + ROI + mutual matching still invalid |
| LoFTR Outdoor | ✅ Success | Strong cross-era architectural correspondence |

### Best current LoFTR result — Humayun's Tomb

- 658 predicted correspondences
- 345 retained at confidence ≥ 0.50
- 182 RANSAC inliers
- 0.528 inlier ratio
- valid homography on the main facade
- dome/ground still show viewpoint/depth/parallax limitations

### Current technical gate

Before implementing local registration or change detection, we must determine whether **better image-pair selection** improves the geometry.

**Next experiment: Multi-Pair Humayun LoFTR Robustness Test**

Final verdict must be:

```text
PAIR_SELECTION_IMPROVES_GEOMETRY
```

or:

```text
LOCAL_GEOMETRY_STILL_REQUIRED
```

---

## Internal-Round Scope

The final prototype is deliberately limited to **3 monuments**:

1. **Humayun's Tomb** — current technical testbed
2. **Sanchi Stupa / Toranas** — restoration-history / gateway case
3. **Qutb Minar / Qutb Complex** — difficult geometry case

Expected demo flow:

```text
Portfolio
→ Monument
→ Archival image + provenance
→ Modern image
→ Registration
→ Valid comparison region
→ Candidate visible-change evidence
→ Confidence / uncertainty
→ Human review
→ Evidence ledger
→ Inspection priority
```

---

## What We Are NOT Building

For the internal round, do not add:

- AR/VR
- digital twins
- IoT
- drones
- chatbot/RAG
- blockchain
- mobile app
- giant image crawler
- custom model training/fine-tuning
- complex authentication
- autonomous structural diagnosis

If a feature does not strengthen the path from **archival evidence → defensible inspection priority**, it is post-internal-round.

---

## Repository Structure

```text
sih-heritage/
├── data/
│   └── humayun/
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
├── TEAMMATES.MD
├── README.md
└── requirements.txt
```

`TEAMMATES.MD` is the **canonical execution/handoff document**. Read it before making architectural or scope decisions.

---

## Setup

Clone:

```bash
git clone https://github.com/wildx-xash/dtheritage.git
cd dtheritage
```

Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Current direct dependencies include:

- NumPy
- OpenCV
- PyTorch CPU
- Kornia
- certifi

---

# Team Workstreams

Replace the member numbers with actual names after assignment.

## Member 1 — Lead / Integration / Scope

**Owner: project lead**

Current work:

- maintain `main`;
- review/merge branches;
- protect scope;
- keep README + `TEAMMATES.MD` current;
- coordinate Claude Code/ECC usage;
- make final decisions after experiment gates;
- later integrate CV + data + UI;
- coordinate final demo package.

Do **not** try to personally implement all six workstreams.

---

## Member 2 — Registration / LoFTR / Geometry

Current work:

### Multi-Pair Humayun LoFTR Robustness Test

Use the same LoFTR model and thresholds across all pairs.

Compare:

- filtered correspondences
- geometric inliers
- inlier ratio
- horizontal support
- vertical support
- spatial coverage
- homography validity
- reprojection statistics
- overlap/NCC
- facade/dome/arcade/ground alignment

Return exactly:

```text
PAIR_SELECTION_IMPROVES_GEOMETRY
```

or:

```text
LOCAL_GEOMETRY_STILL_REQUIRED
```

Do not implement change detection yet.

---

## Member 3 — Evaluation / Change-Intelligence Preparation

Current work:

- aggregate experiment `metrics.json`;
- produce clean pair-comparison tables;
- normalize registration metrics consistently;
- flag invalid transforms;
- document registration success/failure criteria;
- prepare the future change-detection evaluation methodology.

Do **not** run change detection until registration strategy is frozen.

Later owns:

- candidate change extraction;
- false-positive analysis;
- uncertainty methodology;
- controlled/synthetic evaluation.

---

## Member 4 — Dataset / Provenance

Current work:

For Humayun's Tomb, collect a small test set:

- current archival image;
- ideally one additional archival viewpoint;
- 2–3 additional modern viewpoints.

Prioritize geometrically comparable views.

For every image record:

```text
filename
monument
year/date
photographer
archive/source
source URL
license
viewpoint
notes
```

Then begin the same curated process for:

- Sanchi
- Qutb

Do not bulk-download hundreds of images.

Create/update:

```text
data/manifest.csv
```

or:

```text
data/manifest.json
```

---

## Member 5 — Frontend / UX

Current work:

Build **wireframes/static mock screens only** using mock data:

1. portfolio dashboard
2. monument timeline/detail
3. archival-modern comparison
4. registration validity/support
5. evidence review
6. provenance/uncertainty panel

Do not connect to CV/backend yet.

Do not build auth, admin panels, profiles or unrelated product features.

---

## Member 6 — PPT / Research / Project Description

**Start this now.**

Current work:

Create the PPT skeleton:

1. Problem
2. Stakeholder
3. Why archival imagery is underused
4. Existing work / prior art
5. Gap
6. Proposed system
7. Architecture
8. SIFT failure → LoFTR success
9. Quantitative results
10. 3-monument prototype
11. Human-in-the-loop workflow
12. Validation strategy
13. Expected impact
14. Limitations
15. Roadmap

Also begin:

- SIH project description;
- reference tracking;
- experiment narrative;
- conservation-history evidence.

Useful technical story already available:

```text
Vanilla SIFT
→ 9 bad inliers
→ invalid homography

Improved SIFT
→ 4 inliers
→ invalid homography

LoFTR
→ 658 predicted
→ 345 filtered
→ 182 RANSAC inliers
→ valid facade homography
```

---

# Dependency Map

```text
Member 4: additional Humayun images
        ↓
Member 2: multi-pair LoFTR test
        ↓
Registration strategy frozen
        ↓
Member 3: change-detection feasibility
        ↓
Evidence schema frozen
        ↓
Member 5: connect real outputs into UI
        ↓
Member 1: end-to-end integration

Member 6 works in parallel:
PPT + write-up + validation narrative
```

---

## Git Workflow

Do not work directly on `main`.

Suggested branches:

```text
cv/pair-robustness
eval/registration
data/provenance
ui/prototype
docs/pitch
```

Start work:

```bash
git checkout main
git pull
git checkout -b <branch-name>
```

Push:

```bash
git add .
git commit -m "type: short description"
git push -u origin <branch-name>
```

The integration lead reviews before merging.

### Never commit

- `.venv/`
- `__pycache__/`
- `.pyc`
- model caches
- unnecessary generated images

Every teammate creates their own virtual environment.

---

## Claude Code / ECC

Read `CLAUDE.md` before using Claude Code.

Claude may assist implementation, but **Claude does not decide project scope**.

For non-trivial work:

1. inspect existing code first;
2. define the exact technical question;
3. state acceptance criteria;
4. implement only the bounded task;
5. run the actual experiment/tests;
6. report measured results;
7. review the diff before committing.

### Current Claude task

Claude should be used for the **multi-pair LoFTR robustness experiment** after the additional Humayun images are available.

---

## Deliverable Ownership

| Deliverable | Primary owner | Contributors |
|---|---|---|
| Working prototype | Member 1 | 2, 3, 4, 5 |
| GitHub | Member 1 | Everyone |
| Registration | Member 2 | Member 3 |
| Dataset/provenance | Member 4 | Member 6 |
| Change intelligence | Member 3 | Member 2 |
| Frontend | Member 5 | Member 1 |
| PPT | Member 6 | Members 1, 2, 3 |
| Project description | Member 6 | Member 1 |
| Evaluation | Member 3 | Members 2, 4 |
| Demo video | Member 1 + Member 5 | Everyone later |

---

## Internal-Round Definition of Done

- [ ] 3 monuments represented
- [ ] provenance recorded for demo images
- [ ] cross-era registration demonstrated
- [ ] unreliable geometry bounded/rejected
- [ ] candidate visible-change evidence demonstrated on valid regions
- [ ] human Accept/Reject/Reclassify works
- [ ] evidence ledger works
- [ ] portfolio inspection priority works
- [ ] at least one failure/false-positive case shown
- [ ] quantitative evaluation available
- [ ] clean clone/setup works
- [ ] README current
- [ ] PPT complete
- [ ] project description complete
- [ ] demo video complete
- [ ] no unsupported structural-diagnosis claims

---

## Current Next Milestone

> **Complete the multi-pair Humayun LoFTR robustness test and freeze the registration strategy.**

Until this gate is resolved:

- no change detection;
- no local warp unless required;
- no backend integration;
- no scope expansion.
