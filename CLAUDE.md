# DTHeritage Engineering Constitution

## Project and Scope

DTHeritage is an SIH 2026 prototype for archival-baseline conservation
intelligence. Person 2 (Registration CV) and Person 3 (Change Intelligence)
are complete for Humayun's Tomb, Sanchi Stupa/Eastern Torana, and Qutb Minar.

This repository produces human-reviewable visual-change evidence. It does not
diagnose structural damage, measure physical deterioration, or replace a
conservator.

## Scientific Boundaries

- Keep LoFTR Outdoor, confidence threshold, inference sizing, RANSAC, and
  validity gates fixed within comparable experiments.
- Matching success is not registration success. A homography must pass support,
  spatial-spread, transform-sanity, overlap, and visual checks before use.
- Restrict change extraction to `TRUSTED` or validated
  `LOCALLY_RECOVERABLE` regions. Reject marginal, untrusted, or unsupported
  geometry.
- Evidence strength is explainable support, not a probability of damage.
- Preserve negative results, invalid transforms, and Qutb's hard-case outcome.
- Never overwrite original source images. Record reproducible preprocessing,
  including Sanchi's orientation normalization.

## Ownership Boundaries

Person 2/3 own registration, geometric diagnostics, masks, candidate evidence,
uncertainty, and evaluation. Person 4 owns backend/data architecture; do not
replace it. Do not add frontend, authentication, dashboard, database, or other
product features during CV work.

## Reproducibility and Artifacts

- Run workflows through `python src/registration/run_pipeline.py --monument ...`.
- Bulk outputs remain ignored under `outputs/`; committed review evidence lives
  in `artifacts/verification/`.
- `Data.zip` is the original teammate-delivered archive. `data/source_data/Data/`
  is its UTF-8-catalogued, lossless extraction. Runtime code reads the tracked,
  normalized `data/<monument>/pairs/` folders.
- Do not commit `.venv/`, model caches, or bulk generated output folders.

## Current Evidence Status

- Humayun: local geometry required; bounded registration and candidate evidence
  are viable.
- Sanchi: gateway registration, bounded trust regions, and candidate evidence
  are viable.
- Qutb: tested hard case; no pair passed fixed global registration validity, so
  no candidate evidence is generated.
