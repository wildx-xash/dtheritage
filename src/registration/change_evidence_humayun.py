"""
Candidate visible-change evidence for Humayun's Tomb.

This phase is deliberately bounded by the completed trust-region experiment.
It produces human-review candidates only inside TRUSTED regions and validated
LOCALLY_RECOVERABLE regions. It does not classify damage.

Run from the repository root:

    python src/registration/change_evidence_humayun.py
"""

from __future__ import annotations

import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


ALLOWED_TIERS = {"TRUSTED", "LOCALLY_RECOVERABLE"}
EXCLUDED_TIERS = {"MARGINAL", "UNTRUSTED", "UNSUPPORTED"}

MIN_CANDIDATE_AREA = 90
MAX_CANDIDATES = 25
MASK_ERODE_PX = 5
DIFF_PERCENTILE = 88
GRAD_PERCENTILE = 75
EDGE_DILATE_PX = 2


def load_gray(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def load_color(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def box_mask(shape: tuple[int, int], box: list[int]) -> np.ndarray:
    mask = np.zeros(shape, np.uint8)
    x0, y0, x1, y1 = box
    mask[y0:y1, x0:x1] = 255
    return mask


def histogram_match_inside_mask(source: np.ndarray, reference: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Map source intensities to reference CDF using only valid comparison pixels."""
    valid = mask > 0
    if valid.sum() < 100:
        return source.copy()

    src_vals = source[valid].ravel()
    ref_vals = reference[valid].ravel()
    src_hist = np.bincount(src_vals, minlength=256).astype(np.float64)
    ref_hist = np.bincount(ref_vals, minlength=256).astype(np.float64)
    src_cdf = np.cumsum(src_hist) / max(src_hist.sum(), 1.0)
    ref_cdf = np.cumsum(ref_hist) / max(ref_hist.sum(), 1.0)

    lut = np.zeros(256, np.uint8)
    j = 0
    for i in range(256):
        while j < 255 and ref_cdf[j] < src_cdf[i]:
            j += 1
        lut[i] = j
    return cv2.LUT(source, lut)


def clahe_gray(image: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)


def gradient_magnitude(image: np.ndarray) -> np.ndarray:
    gx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    return cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def percentile_threshold(values: np.ndarray, percentile: float, fallback: int) -> int:
    if values.size == 0:
        return fallback
    return int(max(fallback, round(float(np.percentile(values, percentile)))))


def remove_green_vegetation(modern_bgr: np.ndarray, valid_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Conservative HSV vegetation suppression for obvious hedges/trees."""
    hsv = cv2.cvtColor(modern_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    green = ((h >= 35) & (h <= 95) & (s >= 45) & (v >= 35)).astype(np.uint8) * 255
    green = cv2.morphologyEx(green, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cleaned = valid_mask.copy()
    cleaned[green > 0] = 0
    return cleaned, green


def make_overlay(base_bgr: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], alpha: float) -> np.ndarray:
    overlay = base_bgr.copy()
    overlay[mask > 0] = color
    return cv2.addWeighted(overlay, alpha, base_bgr, 1.0 - alpha, 0.0)


def region_for_bbox(regions: list[dict], bbox: list[int]) -> dict | None:
    x, y, w, h = bbox
    cx, cy = x + w / 2.0, y + h / 2.0
    for r in regions:
        x0, y0, x1, y1 = r["box_px"]
        if x0 <= cx < x1 and y0 <= cy < y1:
            return r
    return None


def evidence_strength(
    area: int, mean_signal: float, agreement: float, tier: str, foreground_risk: bool
) -> str:
    if foreground_risk:
        return "LOW_EVIDENCE" if area < 300 else "MEDIUM_EVIDENCE"
    if tier == "TRUSTED" and area >= 250 and mean_signal >= 70 and agreement >= 0.45:
        return "HIGH_EVIDENCE"
    if area >= 120 and mean_signal >= 50 and agreement >= 0.30:
        return "MEDIUM_EVIDENCE"
    return "LOW_EVIDENCE"


def coarse_change_type(
    bbox: list[int],
    region_id: str,
    green_overlap: float,
    edge_agreement: float,
    foreground_risk: bool,
) -> str:
    if green_overlap > 0.20:
        return "vegetation_or_occlusion"
    if foreground_risk:
        return "foreground_or_occlusion_uncertainty"
    if edge_agreement >= 0.45:
        return "structural_appearance_difference"
    if region_id in {"arcade", "central_facade_iwan", "upper_structure_parapet"}:
        return "surface_appearance_change"
    return "uncertain_visual_difference"


def run(args: argparse.Namespace) -> int:
    t0 = time.perf_counter()
    root = Path(__file__).resolve().parents[2]
    trust_dir = Path(args.trust_dir) if args.trust_dir else root / "outputs" / "registration" / "trust_region_pair02"
    out_dir = Path(args.output_dir) if args.output_dir else root / "outputs" / "change_evidence" / "humayun"
    out_dir.mkdir(parents=True, exist_ok=True)

    trust_metrics_path = trust_dir / "trust_region_metrics.json"
    trust = json.loads(trust_metrics_path.read_text(encoding="utf-8"))
    supplied_provenance = (
        json.loads(Path(args.provenance_json).read_text(encoding="utf-8"))
        if args.provenance_json
        else {}
    )

    modern_path = Path(trust["input_pair"]["modern_file"])
    archival_path = Path(trust["input_pair"]["archival_file"])
    registered_path = trust_dir / "04_registered_global.jpg"
    modern_reference_path = trust_dir / "01_global_overlay_pair02.jpg"

    modern_original = load_color(modern_path)
    registered = load_color(registered_path)
    modern = cv2.resize(modern_original, (registered.shape[1], registered.shape[0]), interpolation=cv2.INTER_AREA)
    reg_gray = cv2.cvtColor(registered, cv2.COLOR_BGR2GRAY)
    mod_gray = cv2.cvtColor(modern, cv2.COLOR_BGR2GRAY)

    allowed_regions = []
    excluded_regions = []
    valid_mask = np.zeros(reg_gray.shape, np.uint8)
    for region in trust["regions"]:
        tier = region["trust_tier"]
        local = region.get("local_transform", {})
        local_valid = bool(local.get("valid"))
        allowed = tier == "TRUSTED" or (tier == "LOCALLY_RECOVERABLE" and local_valid)
        if allowed:
            allowed_regions.append(region)
            valid_mask = cv2.bitwise_or(valid_mask, box_mask(reg_gray.shape, region["box_px"]))
        elif tier in EXCLUDED_TIERS:
            excluded_regions.append(region)

    warp_valid = (reg_gray > 2).astype(np.uint8) * 255
    valid_mask = cv2.bitwise_and(valid_mask, warp_valid)
    valid_mask, vegetation_mask = remove_green_vegetation(modern, valid_mask)
    valid_mask = cv2.erode(valid_mask, np.ones((MASK_ERODE_PX, MASK_ERODE_PX), np.uint8))

    matched = histogram_match_inside_mask(reg_gray, mod_gray, valid_mask)
    matched_clahe = clahe_gray(matched)
    modern_clahe = clahe_gray(mod_gray)

    intensity_diff = cv2.absdiff(matched_clahe, modern_clahe)
    grad_arch = gradient_magnitude(matched_clahe)
    grad_mod = gradient_magnitude(modern_clahe)
    grad_diff = cv2.absdiff(grad_arch, grad_mod)

    valid_values = valid_mask > 0
    diff_thr = percentile_threshold(intensity_diff[valid_values], DIFF_PERCENTILE, 35)
    grad_thr = percentile_threshold(grad_diff[valid_values], GRAD_PERCENTILE, 25)

    diff_signal = ((intensity_diff >= diff_thr) & valid_values).astype(np.uint8) * 255
    grad_signal = ((grad_diff >= grad_thr) & valid_values).astype(np.uint8) * 255

    edges_arch = cv2.Canny(matched_clahe, 60, 150)
    edges_mod = cv2.Canny(modern_clahe, 60, 150)
    kernel_edge = np.ones((EDGE_DILATE_PX * 2 + 1, EDGE_DILATE_PX * 2 + 1), np.uint8)
    edge_change = cv2.absdiff(cv2.dilate(edges_arch, kernel_edge), cv2.dilate(edges_mod, kernel_edge))
    edge_signal = ((edge_change > 0) & valid_values).astype(np.uint8) * 255

    combined = cv2.bitwise_and(diff_signal, cv2.bitwise_or(grad_signal, edge_signal))
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    combined = cv2.bitwise_and(combined, valid_mask)

    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined, 8)
    candidates = []
    candidate_mask = np.zeros_like(combined)
    for label in range(1, n_labels):
        x, y, w, h, area = [int(v) for v in stats[label]]
        if area < MIN_CANDIDATE_AREA:
            continue
        bbox = [x, y, w, h]
        region = region_for_bbox(allowed_regions, bbox)
        if region is None:
            continue
        comp = labels == label
        mean_diff = float(intensity_diff[comp].mean())
        mean_grad = float(grad_diff[comp].mean())
        edge_agreement = float((edge_signal[comp] > 0).mean())
        gradient_agreement = float((grad_signal[comp] > 0).mean())
        signal_agreement = float(((grad_signal[comp] > 0) | (edge_signal[comp] > 0)).mean())
        green_overlap = float((vegetation_mask[comp] > 0).mean())
        foreground_risk = bool(args.foreground_region and region["region_id"] == args.foreground_region and y + h >= 255)
        strength = evidence_strength(
            area, mean_diff, signal_agreement, region["trust_tier"], foreground_risk
        )
        uncertainty = list(args.base_uncertainty)
        if region["trust_tier"] == "LOCALLY_RECOVERABLE":
            uncertainty.append("local_registration_recoverable_not_primary_global_trust")
        if foreground_risk:
            uncertainty.append("foreground_hedge_or_people_occlusion_zone")
        if green_overlap > 0.05:
            uncertainty.append("possible_vegetation_or_occlusion")
        if edge_agreement < 0.25:
            uncertainty.append("weak_structural_edge_agreement")
        if x <= 5 or y <= 5 or x + w >= combined.shape[1] - 5 or y + h >= combined.shape[0] - 5:
            uncertainty.append("near_valid_mask_or_image_boundary")

        candidate_id = f"{args.candidate_prefix}_{len(candidates) + 1:03d}"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "monument": args.monument,
                "archival_image": archival_path.name,
                "modern_image": modern_path.name,
                "registration_experiment_id": trust["experiment"],
                "registration_region": region["region_id"],
                "registration_region_label": region["label"],
                "registration_trust": region["trust_tier"],
                "bbox_xywh_in_inference_image": bbox,
                "area_px": area,
                "change_type": coarse_change_type(
                    bbox, region["region_id"], green_overlap, edge_agreement, foreground_risk
                ),
                "evidence_strength": strength,
                "review_status": "PENDING_REVIEW",
                "review": {
                    "machine_proposed_category": "candidate_visible_change_evidence",
                    "reviewer_decision": None,
                    "reviewer_category": None,
                    "reviewer_notes": None,
                    "review_timestamp": None,
                },
                "signals": {
                    "mean_normalized_intensity_difference": mean_diff,
                    "mean_gradient_difference": mean_grad,
                    "signal_agreement_fraction": signal_agreement,
                    "gradient_agreement_fraction": gradient_agreement,
                    "edge_change_fraction": edge_agreement,
                    "green_vegetation_overlap_fraction": green_overlap,
                },
                "registration_support": {
                    "region_filtered_correspondences": region["filtered_count"],
                    "region_global_inliers": region["global_inlier_count"],
                    "region_global_rmse_px": (region.get("global_reprojection") or {}).get("rmse_px"),
                    "local_transform_valid": bool((region.get("local_transform") or {}).get("valid")),
                    "local_transform_inliers": (region.get("local_transform") or {}).get("inlier_count"),
                    "local_transform_rmse_px": (
                        (region.get("local_transform") or {}).get("errors_over_local_inliers") or {}
                    ).get("rmse_px"),
                },
                "uncertainty_indicators": uncertainty,
                "provenance": {
                    "archival_file": str(archival_path),
                    "archival_source": trust["input_pair"]["source_from_multi_pair_metadata"].get("archival_source"),
                    "archival_date": supplied_provenance.get("archival", {}).get("year_date"),
                    "archival_author": supplied_provenance.get("archival", {}).get("photographer"),
                    "archival_source_url": supplied_provenance.get("archival", {}).get("source_url"),
                    "archival_license": supplied_provenance.get("archival", {}).get("license"),
                    "modern_file": str(modern_path),
                    "modern_source": trust["input_pair"]["source_from_multi_pair_metadata"].get("modern_source"),
                    "modern_date": supplied_provenance.get("modern", {}).get("year_date"),
                    "modern_author": supplied_provenance.get("modern", {}).get("photographer"),
                    "modern_source_url": supplied_provenance.get("modern", {}).get("source_url"),
                    "modern_license": supplied_provenance.get("modern", {}).get("license"),
                    "trust_region_metrics": str(trust_metrics_path),
                    "registered_archival_image": str(registered_path),
                    "change_analysis_method_version": args.method_version,
                },
            }
        )
        candidate_mask[comp] = 255

    candidates.sort(
        key=lambda c: (
            {"HIGH_EVIDENCE": 3, "MEDIUM_EVIDENCE": 2, "LOW_EVIDENCE": 1}[c["evidence_strength"]],
            c["area_px"],
            c["signals"]["mean_normalized_intensity_difference"],
        ),
        reverse=True,
    )
    candidates = candidates[:MAX_CANDIDATES]

    ranked_mask = np.zeros_like(candidate_mask)
    overlay = make_overlay(modern, valid_mask, (80, 170, 80), 0.25)
    overlay = make_overlay(overlay, combined, (0, 140, 255), 0.45)
    for idx, c in enumerate(candidates, start=1):
        x, y, w, h = c["bbox_xywh_in_inference_image"]
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(
            overlay,
            str(idx),
            (x + 2, max(y + 16, 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        ranked_mask[labels == np.unique(labels[y : y + h, x : x + w])[0]] = 255

    valid_area = int((valid_mask > 0).sum())
    flagged_area = int((combined > 0).sum())
    summary = {
        "experiment": f"candidate_visible_change_evidence_{args.monument_id}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CHANGE_EVIDENCE_PIPELINE_VIABLE" if 0 < len(candidates) <= MAX_CANDIDATES else "CHANGE_EVIDENCE_METHOD_NEEDS_REVISION",
        "inputs": {
            "archival_file": str(archival_path),
            "modern_file": str(modern_path),
            "registered_archival": str(registered_path),
            "trust_region_metrics": str(trust_metrics_path),
        },
        "valid_comparison_area": {
            "included_tiers": sorted(ALLOWED_TIERS),
            "included_regions": [
                {
                    "region_id": r["region_id"],
                    "trust_tier": r["trust_tier"],
                    "box_px": r["box_px"],
                    "local_transform_valid": bool((r.get("local_transform") or {}).get("valid")),
                }
                for r in allowed_regions
            ],
            "excluded_regions": [
                {"region_id": r["region_id"], "trust_tier": r["trust_tier"], "box_px": r["box_px"]}
                for r in excluded_regions
            ],
            "valid_area_px": valid_area,
            "flagged_area_px": flagged_area,
            "flagged_fraction_of_valid_area": float(flagged_area / valid_area) if valid_area else 0.0,
        },
        "method": {
            "photometric_normalisation": "Grayscale histogram matching of registered archival to modern within valid comparison mask, followed by CLAHE clipLimit=2.0 tileGridSize=8x8.",
            "signals": [
                "absolute normalized intensity difference",
                "Sobel gradient magnitude difference",
                "Canny edge-change support",
            ],
            "thresholds": {
                "intensity_diff_percentile_inside_valid_mask": DIFF_PERCENTILE,
                "resolved_intensity_threshold": diff_thr,
                "gradient_diff_percentile_inside_valid_mask": GRAD_PERCENTILE,
                "resolved_gradient_threshold": grad_thr,
                "min_candidate_area_px": MIN_CANDIDATE_AREA,
                "mask_erode_px": MASK_ERODE_PX,
            },
            "false_positive_controls": [
                "valid registration mask",
                "invalid warp exclusion",
                "exclusion of MARGINAL/UNTRUSTED/UNSUPPORTED trust regions",
                "conservative HSV vegetation suppression",
                "agreement between intensity and gradient/edge signals",
                "morphological opening/closing",
                "minimum connected-component area",
            ],
            "evidence_strength_rule": "HIGH requires TRUSTED registration, area >= 250 px, mean signal >= 70 and agreement >= 0.45; MEDIUM requires area >= 120 px, mean signal >= 50 and agreement >= 0.30; otherwise LOW.",
        },
        "candidate_count": len(candidates),
        "candidate_counts_by_strength": {
            level: sum(1 for c in candidates if c["evidence_strength"] == level)
            for level in ["HIGH_EVIDENCE", "MEDIUM_EVIDENCE", "LOW_EVIDENCE"]
        },
        "candidate_counts_by_region": {
            r["region_id"]: sum(1 for c in candidates if c["registration_region"] == r["region_id"])
            for r in allowed_regions
        },
        "manual_inspection_notes": [
            "Candidates overlapping hedges/trees are suppressed where detected, but vegetation and visitor occlusion can still leak into architectural candidates.",
            "Candidate categories are coarse proposals for human review, not damage labels.",
        ],
        "candidates": candidates,
        "runtime_seconds": time.perf_counter() - t0,
    }

    cv2.imwrite(str(out_dir / "01_registered_archival_gray_matched.jpg"), matched)
    cv2.imwrite(str(out_dir / "02_valid_comparison_mask.png"), valid_mask)
    cv2.imwrite(str(out_dir / "03_intensity_difference.png"), intensity_diff)
    cv2.imwrite(str(out_dir / "04_gradient_difference.png"), grad_diff)
    cv2.imwrite(str(out_dir / "05_combined_change_signal.png"), combined)
    cv2.imwrite(str(out_dir / "06_candidate_overlay.jpg"), overlay)
    cv2.imwrite(str(out_dir / "07_vegetation_exclusion_mask.png"), vegetation_mask)
    (out_dir / "candidate_evidence.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        f"# Candidate visible-change evidence - {args.monument}",
        "",
        f"Generated: {summary['timestamp_utc']}",
        "",
        "This is human-review evidence, not autonomous damage detection.",
        "",
        "## Valid comparison area",
        "",
        f"- Valid area: {valid_area} px",
        f"- Flagged area: {flagged_area} px ({summary['valid_comparison_area']['flagged_fraction_of_valid_area']:.3%})",
        f"- Included regions: {', '.join(r['region_id'] for r in allowed_regions)}",
        f"- Excluded regions: {', '.join(r['region_id'] for r in excluded_regions)}",
        "",
        "## Candidates",
        "",
        "| id | region | strength | type | bbox xywh | area | uncertainty |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for c in candidates:
        lines.append(
            f"| `{c['candidate_id']}` | `{c['registration_region']}` | "
            f"`{c['evidence_strength']}` | `{c['change_type']}` | "
            f"{c['bbox_xywh_in_inference_image']} | {c['area_px']} | "
            f"{', '.join(c['uncertainty_indicators']) or 'none'} |"
        )
    lines.extend(["", "## Decision", "", summary["decision"]])
    (out_dir / "candidate_evidence_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"candidates: {len(candidates)}")
    print(f"flagged_fraction: {summary['valid_comparison_area']['flagged_fraction_of_valid_area']:.4f}")
    print(f"decision: {summary['decision']}")
    print(f"output: {out_dir / 'candidate_evidence.json'}")
    return 0


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Bounded candidate visible-change evidence extraction.")
    parser.add_argument("--trust-dir", help="Trust-region output directory containing trust_region_metrics.json.")
    parser.add_argument("--output-dir", help="Additive candidate-evidence output directory.")
    parser.add_argument("--monument", default="Humayun's Tomb")
    parser.add_argument("--monument-id", default="humayun")
    parser.add_argument("--candidate-prefix", default="HUMAYUN_CE")
    parser.add_argument("--method-version", default="change_evidence_humayun_v1")
    parser.add_argument("--foreground-region", default="arcade", help="Optional region ID associated with foreground risk.")
    parser.add_argument("--provenance-json", help="Optional archival/modern provenance object from a supplied manifest.")
    parser.add_argument("--base-uncertainty", action="append", default=[], help="Repeatable uncertainty indicator applied to every candidate in a run.")
    raise SystemExit(run(parser.parse_args()))
