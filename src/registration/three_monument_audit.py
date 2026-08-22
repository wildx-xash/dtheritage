"""Create additive Person 2/3 portfolio outputs from measured monument runs."""

from __future__ import annotations

import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from change_evidence_humayun import (
    EDGE_DILATE_PX,
    MASK_ERODE_PX,
    MIN_CANDIDATE_AREA,
    clahe_gray,
    gradient_magnitude,
    histogram_match_inside_mask,
    load_color,
    percentile_threshold,
    remove_green_vegetation,
)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_fields(payload: dict, fields: set[str], label: str) -> None:
    missing = sorted(field for field in fields if field not in payload)
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(missing)}")


def require_decision(payload: dict, expected: str, label: str) -> None:
    actual = payload.get("decision") or payload.get("final_decision") or payload.get("technical_conclusion")
    if actual != expected:
        raise ValueError(f"{label} decision is {actual!r}, expected {expected!r}")


def row(pair_id: str, path: Path) -> dict:
    data = read(path)
    require_fields(data, {"status", "correspondences", "timings_seconds"}, str(path))
    corr, ransac = data["correspondences"], data.get("ransac", {})
    hom, geo = data.get("homography", {}), data.get("geometric_error", {})
    return {
        "pair_id": pair_id,
        "status": data["status"],
        "failure_reason": data.get("failure_reason"),
        "predicted_correspondences": corr["total_predicted"],
        "filtered_correspondences": corr["filtered_count"],
        "ransac_inliers": ransac.get("inlier_count"),
        "inlier_ratio": ransac.get("inlier_ratio"),
        "hull_coverage": ransac.get("inlier_hull_area_fraction_of_archival_inference"),
        "condition_number": hom.get("condition_number"),
        "warped_quad_is_convex": hom.get("warped_quad_is_convex"),
        "corner_w_all_same_sign": hom.get("corner_w_all_same_sign"),
        "overlap_fraction": (data.get("photometric_check") or {}).get("overlap_fraction_of_modern"),
        "inlier_rmse_px": ((geo.get("over_ransac_inliers") or {}).get("rmse_px")),
        "all_filtered_rmse_px": ((geo.get("over_all_filtered") or {}).get("rmse_px")),
        "runtime_seconds": data["timings_seconds"]["total"],
        "metrics_path": str(path),
    }


def sensitivity(trust_dir: Path) -> list[dict]:
    trust = read(trust_dir / "trust_region_metrics.json")
    registered = load_color(trust_dir / "04_registered_global.jpg")
    modern = load_color(Path(trust["input_pair"]["modern_file"]))
    modern = cv2.resize(modern, (registered.shape[1], registered.shape[0]), interpolation=cv2.INTER_AREA)
    reg_gray = cv2.cvtColor(registered, cv2.COLOR_BGR2GRAY)
    mod_gray = cv2.cvtColor(modern, cv2.COLOR_BGR2GRAY)
    mask = np.zeros(reg_gray.shape, np.uint8)
    for region in trust["regions"]:
        local = region.get("local_transform", {})
        if region["trust_tier"] == "TRUSTED" or (region["trust_tier"] == "LOCALLY_RECOVERABLE" and local.get("valid")):
            x0, y0, x1, y1 = region["box_px"]
            mask[y0:y1, x0:x1] = 255
    mask = cv2.bitwise_and(mask, (reg_gray > 2).astype(np.uint8) * 255)
    mask, _ = remove_green_vegetation(modern, mask)
    mask = cv2.erode(mask, np.ones((MASK_ERODE_PX, MASK_ERODE_PX), np.uint8))
    matched = clahe_gray(histogram_match_inside_mask(reg_gray, mod_gray, mask))
    modern_clahe = clahe_gray(mod_gray)
    intensity = cv2.absdiff(matched, modern_clahe)
    gradient = cv2.absdiff(gradient_magnitude(matched), gradient_magnitude(modern_clahe))
    valid = mask > 0
    edges_a = cv2.Canny(matched, 60, 150)
    edges_b = cv2.Canny(modern_clahe, 60, 150)
    kernel = np.ones((EDGE_DILATE_PX * 2 + 1, EDGE_DILATE_PX * 2 + 1), np.uint8)
    edge = cv2.absdiff(cv2.dilate(edges_a, kernel), cv2.dilate(edges_b, kernel)) > 0
    result = []
    for diff_p, grad_p in ((84, 70), (88, 75), (92, 80)):
        diff_t = percentile_threshold(intensity[valid], diff_p, 35)
        grad_t = percentile_threshold(gradient[valid], grad_p, 25)
        combined = ((intensity >= diff_t) & ((gradient >= grad_t) | edge) & valid).astype(np.uint8) * 255
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        count, _, stats, _ = cv2.connectedComponentsWithStats(combined, 8)
        areas = [int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= MIN_CANDIDATE_AREA]
        result.append({
            "diff_percentile": diff_p,
            "grad_percentile": grad_p,
            "resolved_diff_threshold": diff_t,
            "resolved_grad_threshold": grad_t,
            "candidate_count": len(areas),
            "candidate_area_px": areas,
            "flagged_area_px": int((combined > 0).sum()),
            "flagged_fraction_of_valid_area": float((combined > 0).sum() / valid.sum()),
        })
    return result


def qutb_hard_case(root: Path, qutb_pairs: list[dict]) -> dict:
    if any(pair["status"] == "success" for pair in qutb_pairs):
        raise ValueError("Qutb hard-case export is invalid because a pair passed registration.")
    if not all(pair["failure_reason"] for pair in qutb_pairs):
        raise ValueError("Qutb hard-case export requires a recorded failure reason for every pair.")
    return {
        "experiment": "candidate_visible_change_evidence_qutb",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "NO_CHANGE_EVIDENCE_GENERATED",
        "monument": "Qutb Minar / Qutb Complex",
        "registration_gate": "No tested Qutb pair passed global homography validity; bounded local registration and change extraction were not attempted.",
        "tested_registration_metrics": [pair["metrics_path"] for pair in qutb_pairs],
        "candidate_count": 0,
        "candidate_counts_by_strength": {"HIGH_EVIDENCE": 0, "MEDIUM_EVIDENCE": 0, "LOW_EVIDENCE": 0},
        "candidates": [],
        "uncertainty_and_failure_factors": [
            "insufficient spatial distribution of global inliers for the full-height pair",
            "invalid folded / vanishing-line-crossing transforms for detail and steep-view pairs",
            "tower curvature, depth variation, and viewpoint difference require future human-guided local landmark input",
        ],
    }


def main(qutb_only: bool = False) -> int:
    root = Path(__file__).resolve().parents[2]
    qutb_pairs = [
        row(p, root / "outputs/registration/qutb/loftr_pairs" / p / "metrics.json")
        for p in ("tower_full_1858_2008", "tower_detail_1860_2015", "tower_full_1858_2017_negative")
    ]
    qutb_no_evidence = qutb_hard_case(root, qutb_pairs)
    qutb_output = root / "outputs/change_evidence/qutb"
    qutb_output.mkdir(parents=True, exist_ok=True)
    (qutb_output / "candidate_evidence.json").write_text(json.dumps(qutb_no_evidence, indent=2) + "\n", encoding="utf-8")
    if qutb_only:
        print("QUTB_HARD_CASE_DOCUMENTED")
        return 0

    sanchi_pairs = [
        row(p, root / "outputs/registration/sanchi/loftr_pairs" / p / "metrics.json")
        for p in ("gateway_front_1863_2015", "stupa_front_1880_2015", "stupa_front_1880_2013")
    ]
    if sanchi_pairs[0]["status"] != "success":
        raise ValueError("Sanchi gateway pair must pass registration before portfolio completion.")
    sanchi_trust_path = root / "outputs/registration/sanchi/trust_region_gateway_1863_2015/trust_region_metrics.json"
    sanchi_trust = read(sanchi_trust_path)
    require_decision(sanchi_trust, "BOUNDED_REGISTRATION_SUFFICIENT_FOR_CHANGE_EVIDENCE", "Sanchi trust-region output")
    sanchi_change_path = root / "outputs/change_evidence/sanchi/candidate_evidence.json"
    sanchi_change = read(sanchi_change_path)
    require_decision(sanchi_change, "CHANGE_EVIDENCE_PIPELINE_VIABLE", "Sanchi change-evidence output")
    if sanchi_change.get("candidate_count", 0) < 1 or not sanchi_change.get("candidates"):
        raise ValueError("Sanchi change-evidence output contains no candidates.")
    humayun_audit = read(root / "outputs/evaluation/person2_3_final/person2_3_final_audit.json")
    require_decision(humayun_audit, "PERSON_2_AND_3_WORK_COMPLETE", "Humayun audit")
    payload = {
        "experiment": "three_monument_person2_person3_audit",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Person 2 Registration CV and Person 3 Change Intelligence only",
        "humayun_reference": humayun_audit,
        "sanchi": {
            "registration_pairs": sanchi_pairs,
            "best_pair": "gateway_front_1863_2015",
            "trust_region_metrics": str(sanchi_trust_path),
            "bounded_registration_decision": sanchi_trust["final_decision"],
            "trust_regions": sanchi_trust["regions"],
            "candidate_evidence": sanchi_change,
            "threshold_sensitivity": sensitivity(sanchi_trust_path.parent),
        },
        "qutb": {
            "registration_pairs": qutb_pairs,
            "best_matching_pair": "tower_full_1858_2008",
            "geometric_registration_decision": "NO_VALID_GLOBAL_REGISTRATION",
            "candidate_evidence": qutb_no_evidence,
        },
        "integration_outputs": {
            "sanchi_candidate_evidence": "outputs/change_evidence/sanchi/candidate_evidence.json",
            "qutb_candidate_evidence": "outputs/change_evidence/qutb/candidate_evidence.json",
            "common_candidate_fields": ["candidate_id", "monument", "registration_trust", "bbox_xywh_in_inference_image", "evidence_strength", "uncertainty_indicators", "signals", "registration_support", "provenance", "review_status"],
        },
        "final_decision": "THREE_MONUMENT_PERSON_2_AND_3_WORK_COMPLETE",
    }
    out = root / "outputs/evaluation/three_monument"
    out.mkdir(parents=True, exist_ok=True)
    (out / "person2_3_cross_monument_audit.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# Three-monument Person 2/3 audit", "", "## Sanchi", ""]
    lines += [f"- `{r['pair_id']}`: {r['status']}, {r['filtered_correspondences']} filtered, {r['ransac_inliers']} inliers." for r in sanchi_pairs]
    lines += [f"- Bounded registration: `{sanchi_trust['final_decision']}`.", f"- Candidate evidence: {sanchi_change['candidate_count']} candidates; {sanchi_change['candidate_counts_by_strength']}.", "", "## Qutb", ""]
    lines += [f"- `{r['pair_id']}`: {r['status']}, {r['filtered_correspondences']} filtered, {r['ransac_inliers']} inliers." for r in qutb_pairs]
    lines += ["- Change evidence was not generated because no global registration passed validation.", "", "## Decision", "", payload["final_decision"]]
    (out / "person2_3_cross_monument_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(payload["final_decision"])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate and export three-monument Person 2/3 evidence.")
    parser.add_argument("--qutb-only", action="store_true", help="Write and validate only the Qutb hard-case evidence export.")
    try:
        raise SystemExit(main(parser.parse_args().qutb_only))
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"AUDIT FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
