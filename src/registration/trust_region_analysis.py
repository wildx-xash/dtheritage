"""
Bounded local-geometry / trust-region analysis for the best Humayun LoFTR pair.

This experiment starts from the validated multi-pair result:

    data/humayun/pairs/pair02_archA_wide_front

It does not tune or replace LoFTR. It reruns the same fixed baseline settings
only because the existing metrics preserve summary statistics and homography
matrices, but not the raw correspondence coordinates needed for spatial trust
analysis.

Outputs are written additively to:

    outputs/registration/trust_region_pair02

Run from the repository root:

    python src/registration/trust_region_analysis.py
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:  # pragma: no cover
    pass

import cv2
import kornia
import numpy as np
import torch
from kornia.feature import LoFTR

from loftr_baseline import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    MAX_CONDITION_NUMBER,
    MAX_WARPED_AREA_RATIO,
    MIN_WARPED_AREA_RATIO,
    as_bgr,
    describe_homography,
    error_summary,
    estimate_homography,
    load_image,
    overlap_ncc,
    prepare_for_loftr,
    reprojection_errors,
)


REGIONS = [
    {
        "region_id": "central_facade_iwan",
        "label": "central facade / iwan",
        "box_rel": [0.32, 0.25, 0.68, 0.58],
        "landmark_fallback": ["central iwan corners", "gateway corners"],
    },
    {
        "region_id": "arcade",
        "label": "arcade / lower facade",
        "box_rel": [0.06, 0.35, 0.94, 0.58],
        "landmark_fallback": ["facade intersections", "gateway corners"],
    },
    {
        "region_id": "dome",
        "label": "dome",
        "box_rel": [0.42, 0.02, 0.58, 0.20],
        "landmark_fallback": ["dome apex", "dome springing points"],
    },
    {
        "region_id": "upper_structure_parapet",
        "label": "upper structure / parapet",
        "box_rel": [0.24, 0.18, 0.76, 0.36],
        "landmark_fallback": ["parapet corners", "facade intersections"],
    },
    {
        "region_id": "ground_garden_reflection",
        "label": "ground / garden / reflection",
        "box_rel": [0.00, 0.70, 1.00, 1.00],
        "landmark_fallback": ["path edges", "garden/terrace corners"],
    },
]

GRID_COLS = 8
GRID_ROWS = 6
MIN_REGION_FILTERED = 12
MIN_REGION_INLIERS = 8
MIN_TRUSTED_INLIERS = 30
MIN_MARGINAL_INLIERS = 12
MAX_TRUSTED_RMSE = 2.2
MAX_TRUSTED_MEDIAN = 1.8
MAX_MARGINAL_RMSE = 3.0
MAX_MARGINAL_MEDIAN = 2.5
MIN_LOCAL_HOMOGRAPHY_INLIERS = 12
MIN_STRONG_LOCAL_HOMOGRAPHY_INLIERS = 30


def rel_box_to_px(box_rel: list[float], width: int, height: int) -> list[int]:
    x0, y0, x1, y1 = box_rel
    return [
        int(round(x0 * width)),
        int(round(y0 * height)),
        int(round(x1 * width)),
        int(round(y1 * height)),
    ]


def points_in_box(points: np.ndarray, box: list[int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    return (
        (points[:, 0] >= x0)
        & (points[:, 0] < x1)
        & (points[:, 1] >= y0)
        & (points[:, 1] < y1)
    )


def convex_hull_fraction(points: np.ndarray, box: list[int]) -> float:
    if len(points) < 3:
        return 0.0
    x0, y0, x1, y1 = box
    area = max(1, (x1 - x0) * (y1 - y0))
    hull = cv2.convexHull(points.reshape(-1, 1, 2).astype(np.float32))
    return float(abs(cv2.contourArea(hull)) / area)


def classify_region(inliers: int, filtered: int, rmse: float | None, median: float | None) -> str:
    if filtered < MIN_REGION_FILTERED:
        return "UNSUPPORTED"
    if inliers < MIN_MARGINAL_INLIERS:
        return "UNTRUSTED"
    if (
        inliers >= MIN_TRUSTED_INLIERS
        and rmse is not None
        and median is not None
        and rmse <= MAX_TRUSTED_RMSE
        and median <= MAX_TRUSTED_MEDIAN
    ):
        return "TRUSTED"
    if (
        inliers >= MIN_MARGINAL_INLIERS
        and rmse is not None
        and median is not None
        and rmse <= MAX_MARGINAL_RMSE
        and median <= MAX_MARGINAL_MEDIAN
    ):
        return "MARGINAL"
    return "UNTRUSTED"


def tier_color(tier: str) -> tuple[int, int, int]:
    return {
        "TRUSTED": (45, 170, 45),
        "LOCALLY_RECOVERABLE": (90, 190, 90),
        "MARGINAL": (0, 190, 230),
        "UNTRUSTED": (0, 80, 220),
        "UNSUPPORTED": (80, 80, 80),
    }[tier]


def draw_region_visual(modern: np.ndarray, regions: list[dict]) -> np.ndarray:
    out = as_bgr(modern).copy()
    overlay = out.copy()
    for r in regions:
        x0, y0, x1, y1 = r["box_px"]
        color = tier_color(r["trust_tier"])
        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)
        cv2.rectangle(out, (x0, y0), (x1, y1), color, 2)
        text = f"{r['region_id']}: {r['trust_tier']}"
        cv2.putText(
            out,
            text,
            (x0 + 6, max(y0 + 20, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
    return cv2.addWeighted(overlay, 0.28, out, 0.72, 0)


def draw_grid_heatmap(modern: np.ndarray, cells: list[dict]) -> np.ndarray:
    out = as_bgr(modern).copy()
    overlay = out.copy()
    for c in cells:
        x0, y0, x1, y1 = c["box_px"]
        color = tier_color(c["trust_tier"])
        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)
        cv2.rectangle(out, (x0, y0), (x1, y1), color, 1)
        cv2.putText(
            out,
            str(c["inlier_count"]),
            (x0 + 5, y0 + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return cv2.addWeighted(overlay, 0.35, out, 0.65, 0)


def local_ncc_for_box(
    registered: np.ndarray, modern: np.ndarray, valid: np.ndarray, box: list[int]
) -> float | None:
    x0, y0, x1, y1 = box
    roi_valid = valid[y0:y1, x0:x1]
    if roi_valid.sum() < 500:
        return None
    return overlap_ncc(
        registered[y0:y1, x0:x1],
        modern[y0:y1, x0:x1],
        roi_valid,
    )


def analyze_region(
    spec: dict,
    width: int,
    height: int,
    f_a: np.ndarray,
    f_b: np.ndarray,
    conf: np.ndarray,
    inlier_mask: np.ndarray,
    global_errors: np.ndarray,
    archival_shape: tuple[int, int],
    registered_global: np.ndarray,
    modern: np.ndarray,
    valid_global: np.ndarray,
    ransac_threshold: float,
    max_iters: int,
) -> dict:
    box = rel_box_to_px(spec["box_rel"], width, height)
    in_region = points_in_box(f_b, box)
    region_inliers = in_region & inlier_mask
    filtered_count = int(in_region.sum())
    inlier_count = int(region_inliers.sum())
    local_errors = global_errors[region_inliers]
    global_summary = error_summary(local_errors)

    local_result: dict = {
        "attempted": False,
        "reason": "insufficient filtered support",
    }
    if filtered_count >= MIN_REGION_FILTERED:
        H_l, mask_l = estimate_homography(
            f_a[in_region],
            f_b[in_region],
            "ransac",
            ransac_threshold,
            max_iters,
        )
        if H_l is not None and mask_l is not None and np.all(np.isfinite(H_l)):
            local_mask = mask_l.ravel().astype(bool)
            local_inliers = int(local_mask.sum())
            local_errors_all = reprojection_errors(H_l, f_a[in_region], f_b[in_region])
            local_hom = describe_homography(
                H_l, archival_shape, modern.shape[:2], 1.0, 1.0
            )
            sane = (
                local_inliers >= MIN_LOCAL_HOMOGRAPHY_INLIERS
                and np.linalg.cond(H_l) < MAX_CONDITION_NUMBER
                and local_hom["warped_quad_is_convex"]
                and MIN_WARPED_AREA_RATIO
                <= local_hom["warped_quad_area_ratio_vs_modern"]
                <= MAX_WARPED_AREA_RATIO
                and local_hom["corner_w_all_same_sign"]
            )
            local_result = {
                "attempted": True,
                "estimated": True,
                "valid": bool(sane),
                "inlier_count": local_inliers,
                "inlier_ratio": float(local_inliers / filtered_count),
                "errors_over_local_inliers": error_summary(local_errors_all[local_mask]),
                "condition_number": float(np.linalg.cond(H_l)),
                "warped_quad_is_convex": local_hom["warped_quad_is_convex"],
                "warped_quad_area_ratio_vs_modern": local_hom[
                    "warped_quad_area_ratio_vs_modern"
                ],
                "corner_w_all_same_sign": local_hom["corner_w_all_same_sign"],
                "global_rmse_on_global_inliers": (
                    global_summary or {}
                ).get("rmse_px"),
                "reason": "valid bounded transform" if sane else "local transform failed sanity/support gates",
            }
        else:
            local_result = {
                "attempted": True,
                "estimated": False,
                "valid": False,
                "reason": "RANSAC did not estimate a finite local homography",
            }

    rmse = (global_summary or {}).get("rmse_px")
    median = (global_summary or {}).get("median_px")
    tier = classify_region(inlier_count, filtered_count, rmse, median)
    if tier == "TRUSTED" and local_result.get("attempted") and not local_result.get("valid"):
        tier = "MARGINAL"
    elif (
        tier in {"MARGINAL", "UNTRUSTED"}
        and local_result.get("valid")
        and local_result.get("inlier_count", 0) >= MIN_STRONG_LOCAL_HOMOGRAPHY_INLIERS
    ):
        tier = "LOCALLY_RECOVERABLE"

    reason_parts = []
    if filtered_count < MIN_REGION_FILTERED:
        reason_parts.append("too few filtered correspondences")
    if inlier_count < MIN_MARGINAL_INLIERS:
        reason_parts.append("too few validated global inliers")
    if rmse is not None:
        reason_parts.append(f"global RMSE {rmse:.2f}px")
    if median is not None:
        reason_parts.append(f"median {median:.2f}px")
    if local_result.get("valid"):
        reason_parts.append("bounded local homography passed sanity gates")
    elif local_result.get("attempted"):
        reason_parts.append(local_result.get("reason", "local transform not valid"))

    return {
        "region_id": spec["region_id"],
        "label": spec["label"],
        "box_px": box,
        "box_rel": spec["box_rel"],
        "filtered_count": filtered_count,
        "global_inlier_count": inlier_count,
        "global_inlier_ratio_in_region": (
            float(inlier_count / filtered_count) if filtered_count else None
        ),
        "mean_inlier_confidence": (
            float(conf[region_inliers].mean()) if inlier_count else None
        ),
        "inlier_hull_fraction_of_region": convex_hull_fraction(f_b[region_inliers], box),
        "global_reprojection": global_summary,
        "global_ncc": local_ncc_for_box(registered_global, modern, valid_global, box),
        "local_transform": local_result,
        "trust_tier": tier,
        "explanation": "; ".join(reason_parts) if reason_parts else "no measurable support",
        "human_guided_fallback_landmarks": spec["landmark_fallback"],
    }


def run(args: argparse.Namespace) -> int:
    t0 = time.perf_counter()
    cv2.setRNGSeed(args.seed)
    torch.manual_seed(args.seed)

    root = Path(args.repo_root)
    data_dir = Path(args.data_dir) if args.data_dir else root / "data" / "humayun" / "pairs" / "pair02_archA_wide_front"
    out_dir = Path(args.output_dir) if args.output_dir else root / "outputs" / "registration" / "trust_region_pair02"
    out_dir.mkdir(parents=True, exist_ok=True)

    pair_metrics_path = Path(args.pair_metrics) if args.pair_metrics else (
        root / "outputs" / "registration" / "loftr_pairs" / "pair02_archA_wide_front" / "metrics.json"
    )
    prior_metrics = json.loads(pair_metrics_path.read_text(encoding="utf-8"))

    region_config = None
    if args.regions_json:
        region_config = json.loads(Path(args.regions_json).read_text(encoding="utf-8"))
    region_specs = region_config.get("regions", REGIONS) if region_config else REGIONS
    pair_id = region_config.get("pair_id", args.pair_id) if region_config else args.pair_id
    source_metadata = (region_config.get("source_metadata", {}) if region_config else {})

    archival_path = data_dir / "archival.jpg"
    modern_path = data_dir / "modern.jpg"
    archival = load_image(archival_path)
    modern_original = load_image(modern_path)
    tensor_a, colour_a, _gray_a, geo_a = prepare_for_loftr(archival, args.max_dim)
    tensor_b, colour_b, _gray_b, geo_b = prepare_for_loftr(modern_original, args.max_dim)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif args.device == "cpu":
        device = torch.device("cpu")
    else:
        device = torch.device("cuda")

    matcher = LoFTR(pretrained="outdoor").to(device).eval()
    with torch.inference_mode():
        prediction = matcher(
            {"image0": tensor_a.to(device), "image1": tensor_b.to(device)}
        )

    pts_a = prediction["keypoints0"].cpu().numpy()
    pts_b = prediction["keypoints1"].cpu().numpy()
    conf = prediction["confidence"].cpu().numpy()
    in_bounds = (
        (pts_a[:, 0] < geo_a["resized_width"])
        & (pts_a[:, 1] < geo_a["resized_height"])
        & (pts_b[:, 0] < geo_b["resized_width"])
        & (pts_b[:, 1] < geo_b["resized_height"])
    )
    pts_a, pts_b, conf = pts_a[in_bounds], pts_b[in_bounds], conf[in_bounds]
    keep = conf >= args.conf_threshold
    f_a, f_b, f_conf = pts_a[keep], pts_b[keep], conf[keep]

    H, mask = estimate_homography(
        f_a, f_b, args.ransac, args.ransac_threshold, args.max_iters
    )
    if H is None or mask is None or not np.all(np.isfinite(H)):
        raise RuntimeError("Could not reproduce pair02 global homography.")

    inlier_mask = mask.ravel().astype(bool)
    global_errors = reprojection_errors(H, f_a, f_b)
    h_m, w_m = colour_b.shape[:2]
    registered_global = cv2.warpPerspective(colour_a, H, (w_m, h_m))
    coverage = cv2.warpPerspective(
        np.full(colour_a.shape[:2], 255, np.uint8), H, (w_m, h_m)
    )
    valid_global = coverage > 0
    overlay_global = cv2.addWeighted(registered_global, 0.5, colour_b, 0.5, 0.0)

    regions = [
        analyze_region(
            spec,
            w_m,
            h_m,
            f_a,
            f_b,
            f_conf,
            inlier_mask,
            global_errors,
            colour_a.shape[:2],
            registered_global,
            colour_b,
            valid_global,
            args.ransac_threshold,
            args.max_iters,
        )
        for spec in region_specs
    ]

    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            box = [
                int(round(col * w_m / GRID_COLS)),
                int(round(row * h_m / GRID_ROWS)),
                int(round((col + 1) * w_m / GRID_COLS)),
                int(round((row + 1) * h_m / GRID_ROWS)),
            ]
            in_cell = points_in_box(f_b, box)
            cell_inliers = in_cell & inlier_mask
            summary = error_summary(global_errors[cell_inliers])
            tier = classify_region(
                int(cell_inliers.sum()),
                int(in_cell.sum()),
                (summary or {}).get("rmse_px"),
                (summary or {}).get("median_px"),
            )
            cells.append(
                {
                    "row": row,
                    "col": col,
                    "box_px": box,
                    "filtered_count": int(in_cell.sum()),
                    "inlier_count": int(cell_inliers.sum()),
                    "trust_tier": tier,
                    "global_reprojection": summary,
                }
            )

    trusted_regions = [r for r in regions if r["trust_tier"] == "TRUSTED"]
    final_decision = (
        "BOUNDED_REGISTRATION_SUFFICIENT_FOR_CHANGE_EVIDENCE"
        if trusted_regions
        else "MANUAL_GUIDED_REGISTRATION_REQUIRED"
    )

    payload = {
        "experiment": "bounded_local_geometry_trust_region_registration",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_pair": {
            "pair_id": pair_id,
            "archival_file": str(archival_path),
            "modern_file": str(modern_path),
            "source_from_multi_pair_metadata": {
                "archival_source": source_metadata.get("archival_source", "archival.jpg"),
                "modern_source": source_metadata.get("modern_source", "in_Delhi-Front_view.jpg"),
            },
        },
        "implementation": {
            "library": "kornia",
            "library_version": kornia.__version__,
            "torch_version": torch.__version__,
            "device": str(device),
            "python": sys.version.split()[0],
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "parameters": {
            "max_inference_dimension_px": args.max_dim,
            "confidence_threshold": args.conf_threshold,
            "ransac_method": args.ransac,
            "ransac_reproj_threshold_px": args.ransac_threshold,
            "ransac_max_iters": args.max_iters,
            "grid_cols": GRID_COLS,
            "grid_rows": GRID_ROWS,
            "region_thresholds": {
                "min_region_filtered": MIN_REGION_FILTERED,
                "min_region_inliers": MIN_REGION_INLIERS,
                "min_trusted_inliers": MIN_TRUSTED_INLIERS,
                "max_trusted_rmse": MAX_TRUSTED_RMSE,
                "max_trusted_median": MAX_TRUSTED_MEDIAN,
                "max_marginal_rmse": MAX_MARGINAL_RMSE,
                "max_marginal_median": MAX_MARGINAL_MEDIAN,
            },
        },
        "reproduced_global_result": {
            "prior_metrics_path": str(pair_metrics_path),
            "prior_filtered_count": prior_metrics["correspondences"]["filtered_count"],
            "prior_inlier_count": prior_metrics["ransac"]["inlier_count"],
            "prior_inlier_ratio": prior_metrics["ransac"]["inlier_ratio"],
            "filtered_count": int(len(f_conf)),
            "inlier_count": int(inlier_mask.sum()),
            "inlier_ratio": float(inlier_mask.sum() / len(f_conf)),
            "geometric_error_over_inliers": error_summary(global_errors[inlier_mask]),
            "geometric_error_over_all_filtered": error_summary(global_errors),
            "overlap_fraction": float(valid_global.mean()),
            "ncc": overlap_ncc(registered_global, colour_b, valid_global),
        },
        "method_notes": [
            "Trust is assigned from validated RANSAC inlier support, local residuals, and overlap diagnostics.",
            "RANSAC-rejected LoFTR matches are not treated as physical parallax evidence.",
            "Local homographies are attempted only inside named regions with enough filtered correspondences and must pass support and transform sanity gates.",
            "This output identifies bounded comparison regions only; it does not perform change detection.",
        ],
        "regions": regions,
        "grid_cells": cells,
        "final_decision": final_decision,
        "next_allowed_phase": (
            "candidate visible-change evidence only inside TRUSTED bounded regions"
            if final_decision == "BOUNDED_REGISTRATION_SUFFICIENT_FOR_CHANGE_EVIDENCE"
            else "human-guided landmark registration experiment"
        ),
        "runtime_seconds": time.perf_counter() - t0,
    }

    cv2.imwrite(str(out_dir / "01_global_overlay_pair02.jpg"), overlay_global)
    cv2.imwrite(str(out_dir / "02_trust_regions.jpg"), draw_region_visual(colour_b, regions))
    cv2.imwrite(str(out_dir / "03_support_heatmap_grid.jpg"), draw_grid_heatmap(colour_b, cells))
    cv2.imwrite(str(out_dir / "04_registered_global.jpg"), registered_global)
    (out_dir / "trust_region_metrics.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# Bounded local geometry / trust-region registration",
        "",
        f"Generated: {payload['timestamp_utc']}",
        "",
        f"Input: `{pair_id}` (`archival.jpg` vs `modern.jpg`, source modern `{payload['input_pair']['source_from_multi_pair_metadata']['modern_source']}`).",
        "",
        "## Global reproduction",
        "",
        f"- Filtered correspondences: {len(f_conf)}",
        f"- RANSAC inliers: {int(inlier_mask.sum())}",
        f"- Inlier ratio: {float(inlier_mask.sum() / len(f_conf)):.3f}",
        f"- Inlier RMSE: {payload['reproduced_global_result']['geometric_error_over_inliers']['rmse_px']:.3f}px",
        f"- All-filtered RMSE: {payload['reproduced_global_result']['geometric_error_over_all_filtered']['rmse_px']:.3f}px",
        f"- NCC over global overlap: {payload['reproduced_global_result']['ncc']:.3f}",
        "",
        "## Region trust",
        "",
        "| region | tier | filtered | global inliers | global RMSE | global NCC | local transform | explanation |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for r in regions:
        rmse = (r["global_reprojection"] or {}).get("rmse_px")
        local = r["local_transform"]
        local_text = "valid" if local.get("valid") else local.get("reason", "not attempted")
        ncc_text = "n/a" if r["global_ncc"] is None else f"{r['global_ncc']:.3f}"
        lines.append(
            f"| {r['label']} | `{r['trust_tier']}` | {r['filtered_count']} | "
            f"{r['global_inlier_count']} | "
            f"{rmse:.3f} | " if rmse is not None else
            f"| {r['label']} | `{r['trust_tier']}` | {r['filtered_count']} | {r['global_inlier_count']} | n/a | "
        )
        if rmse is not None:
            lines[-1] += f"{ncc_text} | {local_text} | {r['explanation']} |"
        else:
            lines[-1] += f"{ncc_text} | {local_text} | {r['explanation']} |"
    lines.extend(
        [
            "",
            "## Decision",
            "",
            payload["final_decision"],
        ]
    )
    (out_dir / "trust_region_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"metrics: {out_dir / 'trust_region_metrics.json'}")
    print(f"report:  {out_dir / 'trust_region_report.md'}")
    print(f"decision: {final_decision}")
    return 0


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Bounded local geometry / trust-region analysis for pair02."
    )
    parser.add_argument("--repo-root", default=str(repo_root))
    parser.add_argument("--data-dir", help="Pair directory containing archival.jpg and modern.jpg.")
    parser.add_argument("--output-dir", help="Additive output directory for this trust-region run.")
    parser.add_argument("--pair-metrics", help="Metrics JSON from the corresponding validated LoFTR run.")
    parser.add_argument("--pair-id", default="pair02_archA_wide_front")
    parser.add_argument("--regions-json", help="Optional JSON defining pair metadata and bounded region specs.")
    parser.add_argument("--max-dim", type=int, default=840)
    parser.add_argument("--conf-threshold", type=float, default=DEFAULT_CONFIDENCE_THRESHOLD)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--ransac", choices=["ransac", "magsac"], default="ransac")
    parser.add_argument("--ransac-threshold", type=float, default=3.0)
    parser.add_argument("--max-iters", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
