# Person 2/3 CV Handoff Contract

This document describes only the Registration CV and Change Intelligence output
contract. It does not define or replace Person 4's backend/data architecture.

## Primary Output

Person 4/frontend integration should consume:

- `outputs/change_evidence/humayun/candidate_evidence.json`

Each candidate contains:

- `candidate_id`
- `monument`
- `archival_image`, `modern_image`
- `registration_region`
- `registration_trust`
- `bbox_xywh_in_inference_image`
- `change_type`
- `evidence_strength`
- `uncertainty_indicators`
- `signals`
- `registration_support`
- `provenance`
- `review_status`

## Registration Context

Use these files to explain geometry and valid comparison area:

- `outputs/registration/loftr_pairs/comparison.json`
- `outputs/registration/loftr_pairs/final_ranking.json`
- `outputs/registration/trust_region_pair02/trust_region_metrics.json`
- `outputs/registration/trust_region_pair02/02_trust_regions.jpg`

Only `TRUSTED` and validated `LOCALLY_RECOVERABLE` regions should be treated as
valid comparison regions. `MARGINAL`, `UNTRUSTED`, and `UNSUPPORTED` regions are
not valid change-evidence areas.

## Change Evidence Visuals

- `outputs/change_evidence/humayun/02_valid_comparison_mask.png`
- `outputs/change_evidence/humayun/05_combined_change_signal.png`
- `outputs/change_evidence/humayun/06_candidate_overlay.jpg`

The output is candidate visible-change evidence for human review. It is not a
damage diagnosis, structural assessment, or physical measurement.
