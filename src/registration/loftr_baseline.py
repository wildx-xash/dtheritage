"""
LoFTR learned detector-free matching baseline for archival-to-modern registration.

Third feasibility experiment for the SIH heritage project. The two classical
experiments both failed at CORRESPONDENCE, not at geometry:

  * sift_baseline  : 83 ratio-test survivors of 17,294 queries -> 9 inliers,
                     near-collinear (1.1% hull), degenerate homography.
  * sift_improved  : CLAHE + RootSIFT + ROI + mutual matching -> 9 mutual
                     matches -> 4 inliers (the minimal sample), reprojection
                     error 0.000 px on an invalid result.

Both are detect-then-describe: a repeatable detector must fire at the same
physical point in BOTH images, and hand-designed gradient histograms must then
be similar there. Across a ~160-year gap in medium, weathering and
illumination, both stages fail independently.

LoFTR is detector-free. It never commits to keypoints: it runs interleaved
self- and cross-attention over a coarse 1/8-resolution grid of BOTH images
jointly, so each location is represented conditioned on the other image, and
matches are decided from global context rather than local patch appearance.
Coarse matches are then refined to sub-pixel resolution.

This experiment tests only the correspondence question. Every geometric
validity gate is carried over from the classical experiments at identical
thresholds, plus an overlap floor.

Run from the repository root:

    python src/registration/loftr_baseline.py

The original input files are opened read-only and never written to.
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

# The Kornia weight download uses urllib, which on this Windows install has no
# usable CA bundle and fails with CERTIFICATE_VERIFY_FAILED. Point it at
# certifi's bundle rather than disabling verification. Harmless once the
# weights are cached; required on a fresh machine.
try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:  # pragma: no cover - certifi is a soft dependency
    pass

import cv2
import numpy as np
import torch
import kornia
from kornia.feature import LoFTR

WEIGHTS_SOURCE_URL = "http://cmp.felk.cvut.cz/~mishkdmy/models/loftr_outdoor.ckpt"

# --------------------------------------------------------------------------
# Validity gates.
#
# Carried over from sift_improved at IDENTICAL thresholds so that a LoFTR
# result is held to exactly the same standard as the classical ones. The only
# addition is an overlap floor.
#
# Deliberately absent: any gate on reprojection error. The classical runs
# returned 1.11 px and then 0.000 px on two completely invalid registrations,
# because over inliers that quantity is bounded by the RANSAC threshold by
# construction. It is recorded, never gated.
# --------------------------------------------------------------------------

MIN_FILTERED_MATCHES = 15
MIN_INLIERS = 12
MIN_INLIER_RATIO = 0.25
MIN_INLIER_HULL_AREA_FRACTION = 0.05
MIN_WARPED_AREA_RATIO = 0.05
MAX_WARPED_AREA_RATIO = 20.0
MAX_CONDITION_NUMBER = 1e8
MIN_OVERLAP_FRACTION = 0.10
"""Overlap floor only. Note from the baseline: a degenerate homography covered
98% of the output frame, so a HIGH overlap fraction proves nothing. Only a low
one is informative."""

DEFAULT_CONFIDENCE_THRESHOLD = 0.5
"""Declared before the run. Kornia's LoFTR already applies an internal coarse
threshold (0.2); 0.5 is the conventional additional cutoff. Match counts at a
range of thresholds are recorded for transparency, but the decision threshold
is fixed."""


# --------------------------------------------------------------------------
# I/O and preprocessing
# --------------------------------------------------------------------------


def resolve_input(directory: Path, stem: str) -> Path:
    """Find the input image, tolerating a doubled '.jpg.jpg' extension."""
    exact = directory / f"{stem}.jpg"
    if exact.is_file():
        return exact
    candidates = sorted(p for p in directory.glob(f"{stem}*") if p.is_file())
    if not candidates:
        raise FileNotFoundError(f"No input image matching '{stem}*' in {directory}")
    if len(candidates) > 1:
        raise FileNotFoundError(
            f"Ambiguous input for '{stem}': {[p.name for p in candidates]}"
        )
    return candidates[0]


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not decode image: {path}")
    return image


def prepare_for_loftr(image: np.ndarray, max_dim: int, multiple: int = 8):
    """Resize preserving aspect ratio exactly, then pad to a multiple of 8.

    LoFTR's coarse level is 1/8 resolution, so both dimensions must be
    divisible by 8. Two ways to achieve that: distort the aspect ratio by
    rounding each dimension independently, or resize with a SINGLE scale factor
    and pad the remainder. We pad, because a single scale factor keeps the
    coordinate mapping back to the original exact and introduces no geometric
    distortion. The padding is at most 7 px on the right/bottom and any
    correspondence landing inside it is discarded afterwards.

    Returns (padded grayscale tensor, unpadded colour resized image, unpadded
    grayscale resized image, geometry record).
    """
    h, w = image.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (new_w, new_h), interpolation=interp)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    pad_r = (-new_w) % multiple
    pad_b = (-new_h) % multiple
    padded = cv2.copyMakeBorder(gray, 0, pad_b, 0, pad_r, cv2.BORDER_CONSTANT, value=0)

    tensor = torch.from_numpy(padded).float()[None, None] / 255.0
    geometry = {
        "original_width": w,
        "original_height": h,
        "scale": float(scale),
        "resized_width": new_w,
        "resized_height": new_h,
        "pad_right": pad_r,
        "pad_bottom": pad_b,
        "padded_width": new_w + pad_r,
        "padded_height": new_h + pad_b,
        "interpolation": "INTER_AREA" if scale < 1.0 else "INTER_LINEAR",
        "aspect_ratio_preserved_exactly": True,
    }
    return tensor, resized, gray, geometry


# --------------------------------------------------------------------------
# Visualization
# --------------------------------------------------------------------------


def as_bgr(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image


def draw_correspondences(
    img_a, pts_a, img_b, pts_b, colors=None, max_draw=400, seed=0
) -> tuple[np.ndarray, int]:
    """Side-by-side correspondence plot.

    cv2.drawMatches expects KeyPoint/DMatch objects; LoFTR emits raw coordinate
    arrays, so drawing directly is simpler than manufacturing those. If there
    are more correspondences than `max_draw`, a uniform random subsample is
    drawn (seeded) -- never a 'best' subset, which would misrepresent quality.
    """
    a, b = as_bgr(img_a), as_bgr(img_b)
    ha, wa = a.shape[:2]
    hb, wb = b.shape[:2]
    canvas = np.zeros((max(ha, hb), wa + wb, 3), np.uint8)
    canvas[:ha, :wa] = a
    canvas[:hb, wa:] = b

    n = len(pts_a)
    idx = np.arange(n)
    if max_draw is not None and n > max_draw:
        idx = np.random.default_rng(seed).choice(n, max_draw, replace=False)

    for i in idx:
        xa, ya = int(round(pts_a[i][0])), int(round(pts_a[i][1]))
        xb, yb = int(round(pts_b[i][0])) + wa, int(round(pts_b[i][1]))
        colour = (0, 255, 0) if colors is None else tuple(int(c) for c in colors[i])
        cv2.line(canvas, (xa, ya), (xb, yb), colour, 1, cv2.LINE_AA)
        cv2.circle(canvas, (xa, ya), 2, colour, -1, cv2.LINE_AA)
        cv2.circle(canvas, (xb, yb), 2, colour, -1, cv2.LINE_AA)
    return canvas, len(idx)


def confidence_colors(conf: np.ndarray) -> np.ndarray:
    """Map confidence to a JET colour so the match plot shows quality."""
    spread = float(conf.max() - conf.min())
    scaled = np.clip((conf - conf.min()) / max(spread, 1e-9) * 255, 0, 255)
    return cv2.applyColorMap(scaled.astype(np.uint8)[None, :], cv2.COLORMAP_JET)[0]


def draw_confidence_histogram(conf: np.ndarray, threshold: float) -> np.ndarray:
    """Histogram plot of the LoFTR confidence distribution."""
    W, H, pad = 900, 400, 50
    canvas = np.full((H, W, 3), 255, np.uint8)
    counts, _ = np.histogram(conf, bins=40, range=(0.0, 1.0))
    if counts.max() == 0:
        return canvas
    bw = (W - 2 * pad) / len(counts)
    for i, c in enumerate(counts):
        x0 = int(pad + i * bw)
        x1 = int(pad + (i + 1) * bw) - 1
        y = int((H - pad) - (c / counts.max()) * (H - 2 * pad))
        cv2.rectangle(canvas, (x0, y), (x1, H - pad), (180, 120, 60), -1)
    xt = int(pad + threshold * (W - 2 * pad))
    cv2.line(canvas, (xt, pad // 2), (xt, H - pad), (0, 0, 220), 2)
    cv2.putText(
        canvas,
        f"threshold={threshold}",
        (xt + 6, pad),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 220),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        f"LoFTR confidence (n={len(conf)})",
        (pad, H - pad // 3),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return canvas


def annotate_untrusted(image: np.ndarray, message: str) -> np.ndarray:
    out = as_bgr(image).copy()
    h, w = out.shape[:2]
    band = max(36, h // 14)
    cv2.rectangle(out, (0, 0), (w, band), (0, 0, 180), thickness=-1)
    scale = w / 900.0
    cv2.putText(
        out,
        message,
        (int(12 * scale), int(band * 0.68)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55 * scale,
        (255, 255, 255),
        max(1, int(round(2 * scale))),
        cv2.LINE_AA,
    )
    return out


# --------------------------------------------------------------------------
# Geometry (carried over from the SIFT experiments)
# --------------------------------------------------------------------------


def estimate_homography(src, dst, method: str, threshold: float, iters: int):
    cv_method = cv2.USAC_MAGSAC if method == "magsac" else cv2.RANSAC
    return cv2.findHomography(
        src.reshape(-1, 1, 2),
        dst.reshape(-1, 1, 2),
        cv_method,
        ransacReprojThreshold=threshold,
        maxIters=iters,
        confidence=0.999,
    )


def reprojection_errors(H, src, dst) -> np.ndarray:
    projected = cv2.perspectiveTransform(
        src.reshape(-1, 1, 2).astype(np.float32), H
    ).reshape(-1, 2)
    return np.linalg.norm(projected - dst.reshape(-1, 2), axis=1)


def error_summary(errors: np.ndarray) -> dict | None:
    if errors.size == 0:
        return None
    return {
        "count": int(errors.size),
        "mean_px": float(np.mean(errors)),
        "median_px": float(np.median(errors)),
        "rmse_px": float(np.sqrt(np.mean(errors**2))),
        "max_px": float(np.max(errors)),
    }


def describe_homography(H, src_shape, dst_shape, scale_a, scale_b) -> dict:
    """Geometric diagnostics, including the two checks that caught both
    classical failures: scale-invariant conditioning, and the vanishing-line
    sign test on the mapped corner w-coordinates."""
    h_s, w_s = src_shape[:2]
    h_d, w_d = dst_shape[:2]

    corners = np.float32([[0, 0], [w_s, 0], [w_s, h_s], [0, h_s]]).reshape(-1, 1, 2)
    quad = cv2.perspectiveTransform(corners, H).reshape(-1, 2)

    xs = np.array([0, w_s, w_s, 0], dtype=np.float64)
    ys = np.array([0, 0, h_s, h_s], dtype=np.float64)
    w_vals = H[2, 0] * xs + H[2, 1] * ys + H[2, 2]

    area = abs(cv2.contourArea(quad.reshape(-1, 1, 2).astype(np.float32)))
    singular_values = np.linalg.svd(H[:2, :2], compute_uv=False)

    # Lift H from inference coordinates to ORIGINAL image coordinates:
    #   x_infer = S x_orig, so H_orig = S_modern^-1 @ H_infer @ S_archival.
    s_a = np.diag([scale_a, scale_a, 1.0])
    s_b_inv = np.diag([1.0 / scale_b, 1.0 / scale_b, 1.0])
    H_orig = s_b_inv @ H @ s_a

    return {
        "matrix_inference_coords": H.tolist(),
        "matrix_original_coords": H_orig.tolist(),
        "determinant": float(np.linalg.det(H)),
        "condition_number": float(np.linalg.cond(H)),
        "corner_w_values": w_vals.tolist(),
        "corner_w_all_same_sign": bool(np.all(w_vals > 0) or np.all(w_vals < 0)),
        "warped_corners_in_modern_inference_coords": quad.tolist(),
        "warped_quad_area_px": float(area),
        "warped_quad_area_ratio_vs_modern": float(area / (w_d * h_d)),
        "warped_quad_is_convex": bool(cv2.isContourConvex(np.int32(np.round(quad)))),
        "approx_scale_from_affine_part": [
            float(singular_values[0]),
            float(singular_values[1]),
        ],
        "approx_rotation_deg_from_affine_part": float(
            np.degrees(np.arctan2(H[1, 0], H[0, 0]))
        ),
    }


def overlap_ncc(warped_bgr, modern_bgr, valid_mask):
    if valid_mask.sum() < 1000:
        return None
    a = cv2.cvtColor(as_bgr(warped_bgr), cv2.COLOR_BGR2GRAY)[valid_mask].astype(float)
    b = cv2.cvtColor(as_bgr(modern_bgr), cv2.COLOR_BGR2GRAY)[valid_mask].astype(float)
    if a.std() < 1e-6 or b.std() < 1e-6:
        return None
    return float(np.corrcoef(a, b)[0, 1])


# --------------------------------------------------------------------------
# Experiment driver
# --------------------------------------------------------------------------


def run(args) -> int:
    t_start = time.perf_counter()
    cv2.setRNGSeed(args.seed)
    torch.manual_seed(args.seed)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    metrics: dict = {
        "experiment": "loftr_baseline_registration",
        "monument": "humayuns_tomb",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "failure_reason": None,
        "implementation": {
            "library": "kornia",
            "library_version": kornia.__version__,
            "torch_version": torch.__version__,
            "model": "LoFTR (detector-free local feature matching with "
            "transformers)",
            "pretrained_weights": "outdoor",
            "weights_rationale": "Trained on MegaDepth (outdoor landmark photo "
            "collections with wide viewpoint and illumination variation). The "
            "'indoor' alternative is ScanNet and is inappropriate for outdoor "
            "architecture.",
            "weights_source_url": WEIGHTS_SOURCE_URL,
            "device": str(device),
            "cuda_available": bool(torch.cuda.is_available()),
        },
        "parameters": {
            "max_inference_dimension_px": args.max_dim,
            "pad_multiple": 8,
            "confidence_threshold": args.conf_threshold,
            "ransac_method_primary": args.ransac,
            "ransac_reproj_threshold_px": args.ransac_threshold,
            "ransac_max_iters": args.max_iters,
            "rng_seed": args.seed,
            "preprocessing": "Greyscale conversion and aspect-preserving "
            "resize with zero padding to a multiple of 8. No CLAHE, no ROI "
            "crop, no contrast manipulation -- LoFTR was trained on ordinary "
            "photographs and the point of this experiment is to isolate the "
            "learned-matching variable.",
        },
        "validity_gates": {
            "min_filtered_matches": MIN_FILTERED_MATCHES,
            "min_inliers": MIN_INLIERS,
            "min_inlier_ratio": MIN_INLIER_RATIO,
            "min_inlier_hull_area_fraction": MIN_INLIER_HULL_AREA_FRACTION,
            "warped_quad_area_ratio_bounds": [
                MIN_WARPED_AREA_RATIO,
                MAX_WARPED_AREA_RATIO,
            ],
            "max_condition_number": MAX_CONDITION_NUMBER,
            "require_corner_w_same_sign": True,
            "min_overlap_fraction": MIN_OVERLAP_FRACTION,
            "note": "Identical to the sift_improved thresholds, plus an "
            "overlap floor, so LoFTR is held to exactly the same standard.",
        },
        "checks": [],
        "environment": {
            "python": sys.version.split()[0],
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
        "notes": [
            "This experiment tests the CORRESPONDENCE question. Correspondence "
            "success and homography success are separate questions and are "
            "reported separately.",
            "Reprojection error over inliers is bounded above by the RANSAC "
            "threshold by construction and is never used as a validity gate.",
            "RANSAC threshold is in LoFTR INFERENCE pixels, whose resolution "
            "differs from the SIFT experiments' working images; account for "
            "that when comparing absolute pixel errors.",
            "Geometric registration is a prerequisite for change analysis. It "
            "is not evidence of structural change, damage or deterioration.",
        ],
    }
    checks = metrics["checks"]
    timings: dict = {}
    metrics["timings_seconds"] = timings

    def gate(name, passed, value, threshold, rationale) -> bool:
        checks.append(
            {
                "name": name,
                "passed": bool(passed),
                "value": value,
                "threshold": threshold,
                "rationale": rationale,
            }
        )
        return bool(passed)

    def finish(status: str, reason: str | None) -> int:
        metrics["status"] = status
        metrics["failure_reason"] = reason
        timings["total"] = time.perf_counter() - t_start
        (out_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\nstatus: {status.upper()}")
        if reason:
            print(f"reason: {reason}")
        print(f"metrics: {out_dir / 'metrics.json'}")
        return 0 if status == "success" else 1

    # -- Load ---------------------------------------------------------------
    t0 = time.perf_counter()
    data_dir = Path(args.data_dir)
    archival_path = resolve_input(data_dir, "archival")
    modern_path = resolve_input(data_dir, "modern")
    archival = load_image(archival_path)
    modern = load_image(modern_path)
    timings["load"] = time.perf_counter() - t0

    metrics["inputs"] = {
        "archival": {
            "resolved_path": str(archival_path),
            "width": int(archival.shape[1]),
            "height": int(archival.shape[0]),
        },
        "modern": {
            "resolved_path": str(modern_path),
            "width": int(modern.shape[1]),
            "height": int(modern.shape[0]),
        },
    }
    print(f"archival: {archival.shape[1]}x{archival.shape[0]}")
    print(f"modern:   {modern.shape[1]}x{modern.shape[0]}")

    # -- Preprocess ---------------------------------------------------------
    t0 = time.perf_counter()
    tensor_a, colour_a, gray_a, geo_a = prepare_for_loftr(archival, args.max_dim)
    tensor_b, colour_b, gray_b, geo_b = prepare_for_loftr(modern, args.max_dim)
    timings["preprocess"] = time.perf_counter() - t0

    metrics["inference_images"] = {"archival": geo_a, "modern": geo_b}
    cv2.imwrite(str(out_dir / "01_input_archival.jpg"), gray_a)
    cv2.imwrite(str(out_dir / "02_input_modern.jpg"), gray_b)
    print(
        f"inference: archival {geo_a['resized_width']}x{geo_a['resized_height']} "
        f"(scale {geo_a['scale']:.4f}), modern "
        f"{geo_b['resized_width']}x{geo_b['resized_height']} "
        f"(scale {geo_b['scale']:.4f})"
    )

    # -- LoFTR --------------------------------------------------------------
    t0 = time.perf_counter()
    matcher = LoFTR(pretrained="outdoor").to(device).eval()
    timings["model_load"] = time.perf_counter() - t0
    metrics["implementation"]["weights_cache_path"] = str(
        Path(torch.hub.get_dir()) / "checkpoints" / "loftr_outdoor.ckpt"
    )

    t0 = time.perf_counter()
    with torch.inference_mode():
        prediction = matcher(
            {"image0": tensor_a.to(device), "image1": tensor_b.to(device)}
        )
    timings["inference"] = time.perf_counter() - t0

    pts_a = prediction["keypoints0"].cpu().numpy()
    pts_b = prediction["keypoints1"].cpu().numpy()
    conf = prediction["confidence"].cpu().numpy()

    # Discard anything landing in the zero padding: those pixels are not image
    # content and a match there is meaningless.
    in_bounds = (
        (pts_a[:, 0] < geo_a["resized_width"])
        & (pts_a[:, 1] < geo_a["resized_height"])
        & (pts_b[:, 0] < geo_b["resized_width"])
        & (pts_b[:, 1] < geo_b["resized_height"])
    )
    n_in_pad = int((~in_bounds).sum())
    pts_a, pts_b, conf = pts_a[in_bounds], pts_b[in_bounds], conf[in_bounds]
    n_total = len(conf)
    print(f"loftr:    {n_total} correspondences ({n_in_pad} discarded in padding)")

    if n_total == 0:
        metrics["correspondences"] = {
            "total_predicted": 0,
            "discarded_in_padding": n_in_pad,
        }
        gate(
            "sufficient_filtered_matches",
            False,
            0,
            MIN_FILTERED_MATCHES,
            "LoFTR returned no correspondences at all.",
        )
        return finish("failed", "LoFTR predicted zero correspondences.")

    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    hist_counts, hist_edges = np.histogram(conf, bins=20, range=(0.0, 1.0))
    thresholds_probe = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    t0 = time.perf_counter()
    keep = conf >= args.conf_threshold
    f_a, f_b, f_conf = pts_a[keep], pts_b[keep], conf[keep]
    timings["filter"] = time.perf_counter() - t0

    metrics["correspondences"] = {
        "total_predicted": n_total,
        "discarded_in_padding": n_in_pad,
        "confidence_threshold": args.conf_threshold,
        "filtered_count": int(len(f_conf)),
        "confidence_distribution": {
            "min": float(conf.min()),
            "max": float(conf.max()),
            "mean": float(conf.mean()),
            "std": float(conf.std()),
            "percentiles": {
                f"p{p}": float(np.percentile(conf, p)) for p in percentiles
            },
            "histogram": {
                "bin_edges": hist_edges.tolist(),
                "counts": hist_counts.tolist(),
            },
        },
        "counts_at_thresholds": {
            str(t): int((conf >= t).sum()) for t in thresholds_probe
        },
        "threshold_note": "The decision threshold was fixed at "
        f"{args.conf_threshold} before the run. Counts at other thresholds are "
        "reported for transparency only and were not used to select a result.",
    }
    print(
        f"filter:   {len(f_conf)} of {n_total} matches at confidence "
        f">= {args.conf_threshold}"
    )

    cv2.imwrite(
        str(out_dir / "08_confidence_histogram.jpg"),
        draw_confidence_histogram(conf, args.conf_threshold),
    )
    all_vis, n_drawn_all = draw_correspondences(
        colour_a,
        pts_a,
        colour_b,
        pts_b,
        confidence_colors(conf),
        max_draw=args.max_drawn_matches,
        seed=args.seed,
    )
    cv2.imwrite(str(out_dir / "03_all_matches.jpg"), all_vis)
    metrics["correspondences"]["drawn_in_03_all_matches"] = n_drawn_all

    if len(f_conf):
        filt_vis, n_drawn_f = draw_correspondences(
            colour_a,
            f_a,
            colour_b,
            f_b,
            confidence_colors(f_conf),
            max_draw=args.max_drawn_matches,
            seed=args.seed,
        )
        cv2.imwrite(str(out_dir / "04_filtered_matches.jpg"), filt_vis)
        metrics["correspondences"]["drawn_in_04_filtered_matches"] = n_drawn_f

    match_gate = gate(
        "sufficient_filtered_matches",
        len(f_conf) >= MIN_FILTERED_MATCHES,
        int(len(f_conf)),
        MIN_FILTERED_MATCHES,
        "A homography needs 4 points; near that count RANSAC has no consensus "
        "to measure and always 'succeeds'.",
    )
    if len(f_conf) < 4:
        return finish(
            "failed",
            f"Only {len(f_conf)} correspondences survived confidence "
            "filtering; a homography requires at least 4.",
        )

    # -- Geometry -----------------------------------------------------------
    t0 = time.perf_counter()
    H, mask = estimate_homography(
        f_a, f_b, args.ransac, args.ransac_threshold, args.max_iters
    )
    timings["ransac"] = time.perf_counter() - t0

    H_x, mask_x = estimate_homography(
        f_a,
        f_b,
        "magsac" if args.ransac == "ransac" else "ransac",
        args.ransac_threshold,
        args.max_iters,
    )
    metrics["cross_check_estimator"] = {
        "method": "magsac" if args.ransac == "ransac" else "ransac",
        "inlier_count": int(mask_x.sum()) if mask_x is not None else 0,
        "homography_estimated": H_x is not None,
    }

    conditioning_rationale = (
        "Scale-invariant degeneracy test; cond(cH) == cond(H). The baseline's "
        "absolute |det(H)| test was scale-dependent and passed a homography "
        "with cond = 1.79e9."
    )
    if H is None or not bool(np.all(np.isfinite(H))):
        gate(
            "homography_well_conditioned",
            False,
            {"estimated": H is not None, "condition_number": None},
            f"finite and cond(H) < {MAX_CONDITION_NUMBER:.0e}",
            conditioning_rationale,
        )
        metrics["ransac"] = {"inlier_count": 0, "inlier_ratio": 0.0}
        return finish("failed", "RANSAC returned no finite homography.")

    cond = float(np.linalg.cond(H))
    conditioning_gate = gate(
        "homography_well_conditioned",
        cond < MAX_CONDITION_NUMBER,
        {"estimated": True, "condition_number": cond},
        f"finite and cond(H) < {MAX_CONDITION_NUMBER:.0e}",
        conditioning_rationale,
    )

    inlier_mask = mask.ravel().astype(bool)
    n_inliers = int(inlier_mask.sum())
    inlier_ratio = n_inliers / len(f_conf)

    if n_inliers:
        in_vis, _ = draw_correspondences(
            colour_a,
            f_a[inlier_mask],
            colour_b,
            f_b[inlier_mask],
            None,
            max_draw=args.max_drawn_matches,
            seed=args.seed,
        )
        cv2.imwrite(str(out_dir / "05_inlier_matches.jpg"), in_vis)

    hull_fraction = 0.0
    if n_inliers >= 3:
        hull = cv2.convexHull(f_a[inlier_mask].reshape(-1, 1, 2).astype(np.float32))
        hull_fraction = float(
            abs(cv2.contourArea(hull)) / (gray_a.shape[0] * gray_a.shape[1])
        )

    errors_all = reprojection_errors(H, f_a, f_b)
    metrics["ransac"] = {
        "method": args.ransac,
        "reproj_threshold_px": args.ransac_threshold,
        "inlier_count": n_inliers,
        "inlier_ratio": float(inlier_ratio),
        "inlier_hull_area_fraction_of_archival_inference": hull_fraction,
    }
    metrics["homography"] = describe_homography(
        H, gray_a.shape, gray_b.shape, geo_a["scale"], geo_b["scale"]
    )
    metrics["geometric_error"] = {
        "definition": "Forward reprojection error ||project(H, x_archival) - "
        "x_modern||_2, in modern INFERENCE pixels.",
        "caveat": "Bounded above by the RANSAC threshold over inliers by "
        "construction. Recorded, never gated.",
        "over_ransac_inliers": error_summary(errors_all[inlier_mask]),
        "over_all_filtered": error_summary(errors_all),
    }
    print(f"ransac:   inliers {n_inliers}/{len(f_conf)} (ratio {inlier_ratio:.3f})")

    # -- Warp + overlay -----------------------------------------------------
    t0 = time.perf_counter()
    h_m, w_m = gray_b.shape[:2]
    registered = cv2.warpPerspective(colour_a, H, (w_m, h_m))
    coverage = cv2.warpPerspective(
        np.full(gray_a.shape[:2], 255, np.uint8), H, (w_m, h_m)
    )
    valid = coverage > 0
    overlay = cv2.addWeighted(registered, 0.5, colour_b, 0.5, 0.0)
    timings["warp"] = time.perf_counter() - t0

    overlap_fraction = float(valid.mean())
    metrics["photometric_check"] = {
        "definition": "Pearson correlation of greyscale intensity over the "
        "valid warp overlap. The only reported signal not derived from the "
        "correspondences RANSAC used.",
        "overlap_pixels": int(valid.sum()),
        "overlap_fraction_of_modern": overlap_fraction,
        "pearson_ncc": overlap_ncc(registered, colour_b, valid),
    }

    # -- Gates --------------------------------------------------------------
    hom = metrics["homography"]
    passed = match_gate and conditioning_gate
    passed &= gate(
        "sufficient_inliers",
        n_inliers >= MIN_INLIERS,
        n_inliers,
        MIN_INLIERS,
        "Absolute floor on the size of the consensus set.",
    )
    passed &= gate(
        "sufficient_inlier_ratio",
        inlier_ratio >= MIN_INLIER_RATIO,
        float(inlier_ratio),
        MIN_INLIER_RATIO,
        "If under a quarter of filtered matches agree, the consensus set is "
        "likely a coincidental cluster.",
    )
    passed &= gate(
        "inlier_spatial_spread",
        hull_fraction >= MIN_INLIER_HULL_AREA_FRACTION,
        hull_fraction,
        MIN_INLIER_HULL_AREA_FRACTION,
        "Inliers confined to a small region give a homography that is locally "
        "consistent and globally unconstrained.",
    )
    passed &= gate(
        "warped_frame_sane",
        hom["warped_quad_is_convex"]
        and MIN_WARPED_AREA_RATIO
        <= hom["warped_quad_area_ratio_vs_modern"]
        <= MAX_WARPED_AREA_RATIO,
        {
            "convex": hom["warped_quad_is_convex"],
            "area_ratio": hom["warped_quad_area_ratio_vs_modern"],
        },
        {
            "convex": True,
            "area_ratio_bounds": [MIN_WARPED_AREA_RATIO, MAX_WARPED_AREA_RATIO],
        },
        "A folded or collapsed quadrilateral is the signature of a degenerate "
        "homography that still produces an image.",
    )
    passed &= gate(
        "no_vanishing_line_crossing",
        hom["corner_w_all_same_sign"],
        hom["corner_w_values"],
        "all four corner w-values share a sign",
        "A sign flip means the vanishing line passes through the image and "
        "part of the source is mapped through infinity. This caused the "
        "radial smear in both classical experiments.",
    )
    passed &= gate(
        "sufficient_overlap",
        overlap_fraction >= MIN_OVERLAP_FRACTION,
        overlap_fraction,
        MIN_OVERLAP_FRACTION,
        "Floor only. A degenerate homography covered 98% of the frame in the "
        "baseline, so a high overlap fraction proves nothing.",
    )

    if not passed:
        failed_names = [c["name"] for c in checks if not c["passed"]]
        banner = "REGISTRATION NOT VALIDATED - " + ", ".join(failed_names)
        registered = annotate_untrusted(registered, banner)
        overlay = annotate_untrusted(overlay, banner)

    cv2.imwrite(str(out_dir / "06_registered_archival.jpg"), registered)
    cv2.imwrite(str(out_dir / "07_overlay.jpg"), overlay)

    if not passed:
        failed_names = ", ".join(c["name"] for c in checks if not c["passed"])
        status = "partial" if match_gate else "failed"
        return finish(
            status,
            f"Registration is not valid. Failed checks: {failed_names}. "
            "Diagnostics were written for inspection; the warp and overlay "
            "carry a warning banner and must not be treated as a valid "
            "alignment.",
        )

    return finish("success", None)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="LoFTR detector-free matching baseline for archival-to-"
        "modern registration."
    )
    parser.add_argument("--data-dir", default=str(repo_root / "data" / "humayun"))
    parser.add_argument(
        "--output-dir",
        default=str(repo_root / "outputs" / "registration" / "loftr_baseline"),
    )
    parser.add_argument("--max-dim", type=int, default=840)
    parser.add_argument(
        "--conf-threshold", type=float, default=DEFAULT_CONFIDENCE_THRESHOLD
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--ransac", choices=["ransac", "magsac"], default="ransac")
    parser.add_argument("--ransac-threshold", type=float, default=3.0)
    parser.add_argument("--max-iters", type=int, default=10000)
    parser.add_argument("--max-drawn-matches", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
