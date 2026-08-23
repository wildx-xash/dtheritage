# Person 2/3 Integration Contract

This document defines only the Registration CV and Change Intelligence handoff.
It does not define or replace Person 4's backend/data architecture.

## Authoritative Review Exports

Use the compact tracked artifacts when bulk `outputs/` are unavailable:

| Monument | Candidate export | Registration context | Status |
|---|---|---|---|
| Humayun | `artifacts/verification/humayun/candidate_evidence.json` | `artifacts/verification/humayun/trust_region_metrics.json` | candidate evidence viable |
| Sanchi | `artifacts/verification/sanchi/candidate_evidence.json` | `artifacts/verification/sanchi/trust_region_metrics.json` | candidate evidence viable |
| Qutb | `artifacts/verification/qutb/candidate_evidence.json` | `artifacts/verification/qutb/registration_metrics_full_height.json` | hard case; zero candidates by geometry gate |

`artifacts/verification/three_monument/cross_monument_audit.json` is the
portfolio-level summary. The matching generated paths live below `outputs/`
and can be recreated with `src/registration/run_pipeline.py`.

## Candidate Record Fields

Successful candidate exports use a common shape containing:

- `candidate_id`, `monument`, `archival_image`, `modern_image`
- `registration_region`, `registration_trust`,
  `bbox_xywh_in_inference_image`
- `change_type`, `evidence_strength`, `uncertainty_indicators`
- `signals`, `registration_support`, `provenance`, `review_status`

Evidence strength is not a probability of physical damage. All candidate records
remain pending human review.

## Visual Assets

- Humayun: `artifacts/verification/humayun/candidate_overlay.jpg`
- Sanchi: `artifacts/verification/sanchi/candidate_overlay.jpg`
- Qutb: `artifacts/verification/qutb/invalid_geometry_overlay.jpg`

Qutb's zero-candidate export must be represented as a geometry-rejected hard
case, not as no visible change or a successful registration.
