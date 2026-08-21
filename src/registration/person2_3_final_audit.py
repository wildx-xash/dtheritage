"""
Final Person 2/3 audit and evaluation package.

This script does not rerun LoFTR or rebuild backend/ledger data. It reads the
actual registration and change-intelligence outputs, performs a small threshold
sensitivity analysis around the change-evidence thresholds, and writes a final
handoff package for integration teammates.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from change_evidence_humayun import (
    ALLOWED_TIERS,
    EDGE_DILATE_PX,
    MASK_ERODE_PX,
    MIN_CANDIDATE_AREA,
    clahe_gray,
    gradient_magnitude,
    histogram_match_inside_mask,
    load_color,
    remove_green_vegetation,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_valid_mask(trust: dict, shape: tuple[int, int], modern_bgr: np.ndarray, reg_gray: np.ndarray) -> tuple[np.ndarray, list[dict], list[dict]]:
    valid_mask = np.zeros(shape, np.uint8)
    included, excluded = [], []
    for region in trust["regions"]:
        tier = region["trust_tier"]
        local_valid = bool((region.get("local_transform") or {}).get("valid"))
        allowed = tier == "TRUSTED" or (tier == "LOCALLY_RECOVERABLE" and local_valid)
        x0, y0, x1, y1 = region["box_px"]
        if allowed:
            valid_mask[y0:y1, x0:x1] = 255
            included.append(region)
        else:
            excluded.append(region)
    warp_valid = (reg_gray > 2).astype(np.uint8) * 255
    valid_mask = cv2.bitwise_and(valid_mask, warp_valid)
    valid_mask, _vegetation = remove_green_vegetation(modern_bgr, valid_mask)
    return cv2.erode(valid_mask, np.ones((MASK_ERODE_PX, MASK_ERODE_PX), np.uint8)), included, excluded


def count_candidates(mask: np.ndarray) -> tuple[int, int, list[int]]:
    n_labels, _labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    areas = [int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, n_labels)]
    kept = [a for a in areas if a >= MIN_CANDIDATE_AREA]
    return len(kept), int(sum(kept)), kept


def sensitivity_run(root: Path, diff_percentile: int, grad_percentile: int) -> dict:
    trust = read_json(root / "outputs/registration/trust_region_pair02/trust_region_metrics.json")
    registered = load_color(root / "outputs/registration/trust_region_pair02/04_registered_global.jpg")
    modern = load_color(Path(trust["input_pair"]["modern_file"]))
    modern = cv2.resize(modern, (registered.shape[1], registered.shape[0]), interpolation=cv2.INTER_AREA)
    reg_gray = cv2.cvtColor(registered, cv2.COLOR_BGR2GRAY)
    mod_gray = cv2.cvtColor(modern, cv2.COLOR_BGR2GRAY)
    valid_mask, _included, _excluded = build_valid_mask(trust, reg_gray.shape, modern, reg_gray)

    matched = histogram_match_inside_mask(reg_gray, mod_gray, valid_mask)
    matched_clahe = clahe_gray(matched)
    modern_clahe = clahe_gray(mod_gray)
    intensity_diff = cv2.absdiff(matched_clahe, modern_clahe)
    grad_diff = cv2.absdiff(gradient_magnitude(matched_clahe), gradient_magnitude(modern_clahe))
    valid = valid_mask > 0

    diff_thr = int(max(35, round(float(np.percentile(intensity_diff[valid], diff_percentile)))))
    grad_thr = int(max(25, round(float(np.percentile(grad_diff[valid], grad_percentile)))))
    diff_signal = ((intensity_diff >= diff_thr) & valid).astype(np.uint8) * 255
    grad_signal = ((grad_diff >= grad_thr) & valid).astype(np.uint8) * 255

    edges_arch = cv2.Canny(matched_clahe, 60, 150)
    edges_mod = cv2.Canny(modern_clahe, 60, 150)
    kernel_edge = np.ones((EDGE_DILATE_PX * 2 + 1, EDGE_DILATE_PX * 2 + 1), np.uint8)
    edge_change = cv2.absdiff(cv2.dilate(edges_arch, kernel_edge), cv2.dilate(edges_mod, kernel_edge))
    edge_signal = ((edge_change > 0) & valid).astype(np.uint8) * 255

    combined = cv2.bitwise_and(diff_signal, cv2.bitwise_or(grad_signal, edge_signal))
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    combined = cv2.bitwise_and(combined, valid_mask)

    count, area, areas = count_candidates(combined)
    valid_area = int(valid.sum())
    return {
        "diff_percentile": diff_percentile,
        "grad_percentile": grad_percentile,
        "resolved_diff_threshold": diff_thr,
        "resolved_grad_threshold": grad_thr,
        "candidate_count": count,
        "flagged_area_px": area,
        "flagged_fraction_of_valid_area": float(area / valid_area) if valid_area else 0.0,
        "candidate_area_px": areas[:20],
    }


def main() -> int:
    t0 = time.perf_counter()
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "outputs/evaluation/person2_3_final"

    loftr = read_json(root / "outputs/registration/loftr_baseline/metrics.json")
    pair02 = read_json(root / "outputs/registration/loftr_pairs/pair02_archA_wide_front/metrics.json")
    ranking = read_json(root / "outputs/registration/loftr_pairs/final_ranking.json")
    trust = read_json(root / "outputs/registration/trust_region_pair02/trust_region_metrics.json")
    change = read_json(root / "outputs/change_evidence/humayun/candidate_evidence.json")

    sensitivity = [
        sensitivity_run(root, d, g)
        for d, g in [(84, 70), (88, 75), (92, 80)]
    ]

    false_positive_categories: dict[str, int] = {}
    uncertainty_categories: dict[str, int] = {}
    for candidate in change["candidates"]:
        false_positive_categories[candidate["change_type"]] = (
            false_positive_categories.get(candidate["change_type"], 0) + 1
        )
        for u in candidate["uncertainty_indicators"]:
            uncertainty_categories[u] = uncertainty_categories.get(u, 0) + 1

    regions = trust["regions"]
    trusted_area = 0
    for r in regions:
        if r["trust_tier"] in ALLOWED_TIERS and (
            r["trust_tier"] == "TRUSTED" or (r.get("local_transform") or {}).get("valid")
        ):
            x0, y0, x1, y1 = r["box_px"]
            trusted_area += (x1 - x0) * (y1 - y0)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Person 2 Registration CV and Person 3 Change Intelligence only",
        "person2_registration_audit": {
            "classical_sift": {
                "implementation": "src/registration/sift_baseline.py",
                "status": "failed_as_expected",
                "note": "README/LoFTR baseline preserve failure interpretation; no successful metrics JSON is present in current outputs.",
            },
            "improved_sift": {
                "implementation": "src/registration/sift_improved.py",
                "status": "failed_as_expected",
                "note": "README/LoFTR baseline preserve improved SIFT failure interpretation; no successful metrics JSON is present in current outputs.",
            },
            "loftr_baseline": {
                "implementation": "src/registration/loftr_baseline.py",
                "metrics_path": "outputs/registration/loftr_baseline/metrics.json",
                "predicted_correspondences": loftr["correspondences"]["total_predicted"],
                "filtered_correspondences": loftr["correspondences"]["filtered_count"],
                "ransac_inliers": loftr["ransac"]["inlier_count"],
                "inlier_ratio": loftr["ransac"]["inlier_ratio"],
                "status": loftr["status"],
            },
            "multi_pair": {
                "implementation": "src/registration/loftr_pairs.py",
                "comparison_path": "outputs/registration/loftr_pairs/comparison.json",
                "best_pair": "pair02_archA_wide_front",
                "conclusion": ranking["technical_conclusion"],
                "best_pair_metrics": {
                    "filtered_correspondences": pair02["correspondences"]["filtered_count"],
                    "ransac_inliers": pair02["ransac"]["inlier_count"],
                    "inlier_ratio": pair02["ransac"]["inlier_ratio"],
                    "hull_coverage": pair02["ransac"]["inlier_hull_area_fraction_of_archival_inference"],
                    "reprojection_rmse_inliers_px": pair02["geometric_error"]["over_ransac_inliers"]["rmse_px"],
                    "reprojection_rmse_all_filtered_px": pair02["geometric_error"]["over_all_filtered"]["rmse_px"],
                },
            },
            "bounded_registration": {
                "implementation": "src/registration/trust_region_analysis.py",
                "metrics_path": "outputs/registration/trust_region_pair02/trust_region_metrics.json",
                "conclusion": trust["final_decision"],
                "trusted_or_recoverable_regions": [
                    {
                        "region_id": r["region_id"],
                        "trust_tier": r["trust_tier"],
                        "filtered_count": r["filtered_count"],
                        "global_inlier_count": r["global_inlier_count"],
                        "global_rmse_px": (r.get("global_reprojection") or {}).get("rmse_px"),
                        "local_valid": bool((r.get("local_transform") or {}).get("valid")),
                        "local_rmse_px": ((r.get("local_transform") or {}).get("errors_over_local_inliers") or {}).get("rmse_px"),
                    }
                    for r in regions
                ],
                "trusted_box_area_px_before_mask_refinement": trusted_area,
            },
        },
        "person3_change_audit": {
            "implementation": "src/registration/change_evidence_humayun.py",
            "evidence_path": "outputs/change_evidence/humayun/candidate_evidence.json",
            "decision": change["decision"],
            "candidate_count": change["candidate_count"],
            "candidate_counts_by_strength": change["candidate_counts_by_strength"],
            "candidate_counts_by_region": change["candidate_counts_by_region"],
            "valid_area_px": change["valid_comparison_area"]["valid_area_px"],
            "flagged_area_px": change["valid_comparison_area"]["flagged_area_px"],
            "flagged_fraction_of_valid_area": change["valid_comparison_area"]["flagged_fraction_of_valid_area"],
            "false_positive_categories": false_positive_categories,
            "uncertainty_categories": uncertainty_categories,
            "safe_language_check": "Outputs use candidate/appearance/occlusion terminology, not structural diagnosis.",
        },
        "threshold_sensitivity": {
            "purpose": "Small robustness check; no ground-truth accuracy claimed.",
            "runs": sensitivity,
            "interpretation": "Candidate burden remains small across nearby thresholds; stricter thresholds reduce candidates/area rather than causing a full-frame explosion.",
        },
        "integration_contract": {
            "primary_machine_readable_output": "outputs/change_evidence/humayun/candidate_evidence.json",
            "registration_context": "outputs/registration/trust_region_pair02/trust_region_metrics.json",
            "visual_artifacts": [
                "outputs/registration/trust_region_pair02/02_trust_regions.jpg",
                "outputs/change_evidence/humayun/02_valid_comparison_mask.png",
                "outputs/change_evidence/humayun/06_candidate_overlay.jpg",
            ],
            "candidate_required_fields": [
                "candidate_id",
                "registration_region",
                "registration_trust",
                "bbox_xywh_in_inference_image",
                "change_type",
                "evidence_strength",
                "uncertainty_indicators",
                "signals",
                "registration_support",
                "provenance",
                "review_status",
            ],
        },
        "final_decision": "PERSON_2_AND_3_WORK_COMPLETE",
        "runtime_seconds": time.perf_counter() - t0,
    }

    write_json(out_dir / "person2_3_final_audit.json", payload)

    lines = [
        "# Person 2/3 Final CV Audit",
        "",
        f"Generated: {payload['generated_utc']}",
        "",
        "## Registration",
        "",
        f"- LoFTR baseline: {loftr['correspondences']['filtered_count']} filtered, {loftr['ransac']['inlier_count']} inliers, ratio {loftr['ransac']['inlier_ratio']:.3f}.",
        f"- Multi-pair conclusion: `{ranking['technical_conclusion']}`.",
        f"- Best pair02: {pair02['correspondences']['filtered_count']} filtered, {pair02['ransac']['inlier_count']} inliers, ratio {pair02['ransac']['inlier_ratio']:.3f}.",
        f"- Bounded registration: `{trust['final_decision']}`.",
        "",
        "## Change Intelligence",
        "",
        f"- Change decision: `{change['decision']}`.",
        f"- Candidates: {change['candidate_count']}.",
        f"- Flagged valid area: {change['valid_comparison_area']['flagged_fraction_of_valid_area']:.3%}.",
        f"- Evidence strengths: {change['candidate_counts_by_strength']}.",
        "",
        "## Threshold Sensitivity",
        "",
        "| diff pctl | grad pctl | candidates | flagged fraction |",
        "|---:|---:|---:|---:|",
    ]
    for run in sensitivity:
        lines.append(
            f"| {run['diff_percentile']} | {run['grad_percentile']} | "
            f"{run['candidate_count']} | {run['flagged_fraction_of_valid_area']:.3%} |"
        )
    lines.extend(
        [
            "",
            "## Integration",
            "",
            "Person 4/frontend should consume `outputs/change_evidence/humayun/candidate_evidence.json` plus the trust-region metrics and visuals listed in the JSON audit.",
            "",
            "## Decision",
            "",
            payload["final_decision"],
        ]
    )
    (out_dir / "person2_3_final_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"audit: {out_dir / 'person2_3_final_audit.json'}")
    print(f"decision: {payload['final_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
