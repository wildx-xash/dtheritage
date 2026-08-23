# DTHeritage - SIH 2026

Archival-baseline conservation intelligence for Indian heritage structures.
The Person 2/3 pipeline registers historical and modern images, bounds where
comparison is geometrically trustworthy, and produces candidate visible-change
evidence for human review. It is not autonomous damage diagnosis.

## Current Status

Person 2/3 scientific work is complete for the three-monument portfolio.

| Monument | Registration result | Change-evidence result |
|---|---|---|
| Humayun's Tomb | `LOCAL_GEOMETRY_STILL_REQUIRED`; bounded registration sufficient | 8 review candidates; pipeline viable |
| Sanchi Stupa / Eastern Torana | valid gateway pair; bounded registration sufficient | 11 review candidates; pipeline viable |
| Qutb Minar / Qutb Complex | no supplied pair passed fixed global validity gates | no candidates generated; documented hard case |

Key measured results: Humayun best pair has 519 filtered matches and 301
inliers; Sanchi gateway has 566 filtered matches and 358 inliers; Qutb's best
matching pair has 103 filtered matches and 53 inliers but fails spatial-spread
validation. Do not interpret match count alone as valid geometry.

## Technical Pipeline

```text
Historical + modern imagery
-> LoFTR matching
-> geometric verification
-> multi-pair robustness
-> bounded trust-region registration
-> valid comparison mask
-> photometric normalization
-> candidate visible-change extraction
-> false-positive controls
-> evidence strength + uncertainty
-> human-review-ready candidate JSON
```

Candidate visible change is not confirmed structural damage. Unsupported
geometry is rejected, uncertainty is retained in the exported evidence, and
human review remains required.

## Verified Results

| Monument | Verified registration evidence | Review-evidence outcome |
|---|---|---|
| Humayun's Tomb | 519 filtered / 301 inliers; bounded trusted geometry | 8 candidates; `CHANGE_EVIDENCE_PIPELINE_VIABLE` |
| Sanchi gateway | 566 filtered / 358 inliers; bounded registration sufficient | 11 candidates; `CHANGE_EVIDENCE_PIPELINE_VIABLE` |
| Qutb Minar | 103 filtered / 53 inliers on best matching pair, but spatial-spread gate fails | zero candidates; unsupported geometry suppressed |

The tracked verification JSON under `artifacts/verification/` is the source for
these values.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first LoFTR run downloads Kornia's Outdoor checkpoint into the ignored
`.torch-cache/` directory. CPU inference is supported.

## Reproduce Person 2/3 Results

Run from the repository root:

```bash
python src/registration/run_pipeline.py --monument humayun
python src/registration/run_pipeline.py --monument sanchi
python src/registration/run_pipeline.py --monument qutb
python src/registration/run_pipeline.py --monument audit
```

Or run the complete sequence:

```bash
python src/registration/run_pipeline.py --monument all
```

The runner preserves actual failure outcomes: invalid Qutb registrations return
metrics and overlays, then write a `NO_CHANGE_EVIDENCE_GENERATED` export rather
than fabricating candidates.

- `humayun` regenerates the LoFTR baseline, multi-pair comparison, bounded
  registration, candidate evidence, and Humayun audit.
- `sanchi` runs its three selected pairs, gateway trust analysis, and candidate
  evidence export.
- `qutb` runs its three fixed pairs and writes the geometry-rejected hard-case
  export.
- `audit` validates and writes the cross-monument integration summary.

### Sanchi Sequence

The Sanchi command performs the complete, tracked workflow:

```text
data/sanchi/pairs/
-> LoFTR registration for three selected pairs
-> bounded trust-region registration for the valid gateway pair
-> valid comparison mask and photometric normalization
-> candidate visible-change extraction with provenance and uncertainty
```

Its inputs, trust regions, and provenance live under `data/sanchi/`.

## Outputs and Verification

Bulk reproducible outputs are written below `outputs/` and remain ignored.
Reviewers and UI teammates should use the compact tracked bundle documented in
[artifacts/verification/README.md](artifacts/verification/README.md).

Primary integration exports:

- `artifacts/verification/humayun/candidate_evidence.json`
- `artifacts/verification/sanchi/candidate_evidence.json`
- `artifacts/verification/qutb/candidate_evidence.json`
- `artifacts/verification/three_monument/cross_monument_audit.json`

Candidate records contain monument/image references, registration trust, region
geometry, evidence strength, uncertainty indicators, signal/support metrics,
provenance, and review status. Qutb's export explicitly represents its rejected
geometry with zero candidates.

## Data and Provenance

- `Data.zip` is the original teammate-delivered archive and is retained.
- `data/source_data/Data/` is its lossless extraction; its manifest is UTF-8
  and references the actual source filenames.
- `data/<monument>/pairs/` is the canonical runtime dataset used by code.

Raw source filenames are retained where they represent the delivered archive.
Runtime names are lowercase, deterministic pair folders. The raw Humayun
embedded-space filename was normalized to `humayun_m04_2015.jpg`; the manifest
now correctly references `humayun_h02_1858.jpg`.

## Supabase Backend and Dashboard

The verified portfolio data is available to the static dashboard through
Supabase. The CV pipeline remains the source of truth: Supabase stores the
tracked verification exports for UI consumption and review, and does not run
LoFTR or change detection.

### Database model

| Table | Purpose |
|---|---|
| `monuments` | Three-monument portfolio and registration status |
| `images` | Image provenance, source URLs, licensing, and storage paths |
| `registrations` | Verified LoFTR and geometric-validation results |
| `evidence_candidates` | Candidate visible-change evidence (8 Humayun, 11 Sanchi, 0 Qutb) |
| `evidence_reviews` | Future human accept/reject/reclassify decisions |

Row Level Security is enabled. The dashboard is allowed to read scientific
outputs; no service-role credential is used by the browser.

### Initial import

Create a local `.env.local` file in the repository root:

```text
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<publishable-or-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<secret-key-for-local-import-only>
```

`.env.local` is ignored by Git. Never commit it or expose the service-role key.
After the Supabase tables and read policies are created, import the tracked
records with:

```bash
python scripts/seed_supabase.py
```

The script reads `data/source_data/Data/manifest.csv` and
`artifacts/verification/`, then imports image metadata, three registrations,
and 19 candidate records. Expected candidate totals are Humayun 8, Sanchi 11,
and Qutb 0.

### Dashboard configuration

Set the public Project URL and anon/publishable key in
`frontend/supabase-config.js`. These values are used only for read requests
under RLS. Start the dashboard with a static server (for example VS Code Live
Server), then open `frontend/index.html`.

## Scope and Limitations

Person 2/3 CV work, the Supabase data layer, and the static dashboard are
implemented. Backend ownership remains Person 4's responsibility; the current
integration is deliberately limited to verified outputs and human-review data.

No precision/recall/F1 claims are made because labelled ground truth is absent.
Candidate evidence may reflect archival degradation, lighting, vegetation,
occlusion, restoration, or residual viewpoint difference and requires human
review.

The three monuments are prototype case studies, not universal monument
generalization. Perspective and parallax can invalidate registration; Qutb is
the documented example. The next milestone is consumption of verified Person
2/3 outputs by Person 4/backend and Person 5/frontend, followed by lead
integration and PPT/demo packaging.

See [CLAUDE.md](CLAUDE.md) for engineering/scientific rules and
[TEAMMATES.MD](TEAMMATES.MD) for team handoff context.
