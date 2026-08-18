"""
Improved classical registration baseline: CLAHE + RootSIFT + ROI + mutual matching.

Second and FINAL classical feasibility experiment for the SIH heritage project.
The vanilla SIFT baseline (src/registration/sift_baseline.py) failed
conclusively: descriptor matching across the historical/modern domain gap
yielded 83 good matches out of 17,294 queries, of which RANSAC found a
9-point near-collinear clique that produced a degenerate homography.

This experiment applies exactly four targeted interventions and re-measures:

  1. CLAHE photometric normalisation before feature extraction.
  2. RootSIFT descriptors (Hellinger distance via L1-normalise + sqrt).
  3. ROI restriction to remove the archival paper border and garden foreground.
  4. Mutual (bidirectional) match consistency on top of the ratio test.

Run from the repository root:

    python src/registration/sift_improved.py

This module deliberately does NOT import from sift_baseline. Experiment code
should be self-contained: if the baseline were later edited, importing from it
would silently change what this experiment means. The duplication is the point.

The original input files are opened read-only and never written to.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

# --------------------------------------------------------------------------
# Region of interest.
#
# Stated rule, applied to both images: keep the built structure -- everything
# from the top of the photographic content down to the base of the plinth
# arcade -- and discard the ground plane below it.
#
# Boundaries were read off a fractional coordinate grid and visually verified
# BEFORE any matching code was run. They are tied to visible structural
# features, not to match outcomes:
#
#   archival: 5% inset on all sides removes the photographic paper border
#             (measured at 3-4%); the arcade parapet runs full-width at
#             y~0.545 and its arch niches end by y~0.62, so y=0.65 cuts just
#             below the arcade base, before the garden dominates.
#   modern:   no lateral inset (there is no paper border); the same arcade's
#             base sits at y~0.72, so y=0.75 cuts just below it, before the
#             lawn, path and visitors.
#
# The two crops are deliberately NOT identical -- forcing them to match would
# be an artificial constraint the scene does not justify.
# --------------------------------------------------------------------------

ROI_ARCHIVAL = (0.05, 0.05, 0.95, 0.65)  # (x0, y0, x1, y1) as fractions
ROI_MODERN = (0.00, 0.00, 1.00, 0.75)

CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID = (8, 8)

# --------------------------------------------------------------------------
# Validity gates.
#
# The first five carry over from the baseline UNCHANGED so the comparison is
# controlled. The last two are new and strictly stronger; both would have
# caught the baseline failure (measured: cond(H)=1.79e9, corner w-values
# changing sign), whereas the baseline's absolute |det(H)| > 1e-6 test passed
# it by a hair because det(H) scales as the cube of the coordinate units.
# --------------------------------------------------------------------------

MIN_DESCRIPTORS = 100
MIN_GOOD_MATCHES = 15
MIN_INLIERS = 12
MIN_INLIER_RATIO = 0.25
MIN_INLIER_HULL_AREA_FRACTION = 0.05
MIN_WARPED_AREA_RATIO = 0.05
MAX_WARPED_AREA_RATIO = 20.0

MAX_CONDITION_NUMBER = 1e8
"""Scale-invariant degeneracy test. cond(cH) == cond(H) for any scalar c,
which is exactly the property the baseline's determinant test lacked."""

# --------------------------------------------------------------------------
# I/O helpers
# --------------------------------------------------------------------------


def resolve_input(directory: Path, stem: str) -> Path:
    """Find the input image for `stem`, tolerating a doubled `.jpg.jpg`
    extension (a Windows hidden-extension artifact seen on delivery)."""
    exact = directory / f"{stem}.jpg"
    if exact.is_file():
        return exact
    candidates = sorted(p for p in directory.glob(f"{stem}*") if p.is_file())
    if not candidates:
        raise FileNotFoundError(f"No input image matching '{stem}*' in {directory}")
    if len(candidates) > 1:
        raise FileNotFoundError(
            f"Ambiguous input for '{stem}' in {directory}: "
            f"{[p.name for p in candidates]}"
        )
    return candidates[0]


def load_image(path: Path) -> np.ndarray:
    """cv2.imread returns None on failure rather than raising, which is a
    classic source of silent downstream errors. Fail loudly instead."""
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not decode image: {path}")
    return image


def roi_pixels(image: np.ndarray, roi: tuple) -> dict:
    """Convert fractional ROI bounds to integer pixel bounds on the original."""
    h, w = image.shape[:2]
    fx0, fy0, fx1, fy1 = roi
    x0, y0 = int(round(fx0 * w)), int(round(fy0 * h))
    x1, y1 = int(round(fx1 * w)), int(round(fy1 * h))
    return {
        "fractions": {"x0": fx0, "y0": fy0, "x1": fx1, "y1": fy1},
        "pixels": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
        "width": x1 - x0,
        "height": y1 - y0,
        "area_fraction_of_original": ((x1 - x0) * (y1 - y0)) / (w * h),
    }


def draw_roi_visualization(image: np.ndarray, box: dict, max_dim: int) -> np.ndarray:
    """Full frame with everything outside the ROI dimmed and the ROI outlined."""
    h, w = image.shape[:2]
    scale = max_dim / max(h, w)
    small = cv2.resize(
        image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
    )
    p = box["pixels"]
    x0, y0 = int(p["x0"] * scale), int(p["y0"] * scale)
    x1, y1 = int(p["x1"] * scale), int(p["y1"] * scale)
    out = (small * 0.35).astype(np.uint8)
    out[y0:y1, x0:x1] = small[y0:y1, x0:x1]
    cv2.rectangle(out, (x0, y0), (x1, y1), (0, 255, 0), 2)
    return out


def resize_to_working(image: np.ndarray, max_dim: int) -> tuple[np.ndarray, dict]:
    """Downscale so the longest side is at most `max_dim`.

    INTER_AREA averages over the source footprint rather than point-sampling,
    which avoids the aliasing that would otherwise inject spurious keypoints.
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return image.copy(), {"resized": False, "scale_x": 1.0, "scale_y": 1.0}
    factor = max_dim / longest
    new_w, new_h = int(round(w * factor)), int(round(h * factor))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, {
        "resized": True,
        "scale_x": new_w / w,
        "scale_y": new_h / h,
        "interpolation": "INTER_AREA",
    }


def annotate_untrusted(image: np.ndarray, message: str) -> np.ndarray:
    """Burn a warning banner into an unvalidated warp/overlay so it can never
    be mistaken for a good result outside the context of metrics.json."""
    out = image.copy()
    h, w = out.shape[:2]
    band = max(36, h // 14)
    cv2.rectangle(out, (0, 0), (w, band), (0, 0, 180), thickness=-1)
    scale = w / 900.0
    cv2.putText(
        out,
        message,
        (int(12 * scale), int(band * 0.68)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6 * scale,
        (255, 255, 255),
        max(1, int(round(2 * scale))),
        cv2.LINE_AA,
    )
    return out


# --------------------------------------------------------------------------
# Intervention 1: CLAHE
# --------------------------------------------------------------------------


def normalize_clahe(gray: np.ndarray, clip: float, tile: tuple) -> np.ndarray:
    """Contrast Limited Adaptive Histogram Equalisation.

    Plain histogram equalisation is global: one transfer curve for the whole
    frame, which here would be dominated by the large flat sky. CLAHE instead
    equalises within a grid of tiles and bilinearly interpolates between them,
    so the low-contrast masonry detail we actually need is amplified locally.
    The clip limit caps each tile's histogram before redistribution, which is
    what stops it from amplifying film grain and scan noise into fake edges.
    """
    return cv2.createCLAHE(clipLimit=clip, tileGridSize=tile).apply(gray)


# --------------------------------------------------------------------------
# Intervention 2: RootSIFT
# --------------------------------------------------------------------------


def to_root_sift(desc: np.ndarray | None, eps: float = 1e-7) -> tuple:
    """Convert SIFT descriptors to RootSIFT.

    L1-normalise each descriptor, then take the element-wise square root. The
    Euclidean distance between two such vectors equals the Hellinger
    (Bhattacharyya) distance between the original histograms. Because sqrt is
    concave it compresses large bins relative to small ones, so a descriptor
    stops being dominated by its few strongest gradient-orientation bins --
    which are exactly the bins most distorted by a contrast difference between
    the two photographs.

    Three lines of NumPy, no new dependency.

    Zero-norm descriptors (a wholly flat patch) would divide by zero, so their
    norm is floored at `eps`; the resulting descriptor stays all-zero rather
    than becoming NaN. The count is returned so it can be recorded.
    """
    if desc is None or len(desc) == 0:
        return desc, 0
    desc = desc.astype(np.float32)
    norms = np.linalg.norm(desc, ord=1, axis=1, keepdims=True)
    n_zero = int((norms < eps).sum())
    norms = np.maximum(norms, eps)
    return np.sqrt(desc / norms).astype(np.float32), n_zero


# --------------------------------------------------------------------------
# Intervention 4: mutual (bidirectional) matching
# --------------------------------------------------------------------------


def ratio_filtered(matcher, desc_q: np.ndarray, desc_t: np.ndarray, ratio: float):
    """One direction of k-NN matching with Lowe's ratio test.

    Returns (list of DMatch, dict mapping queryIdx -> trainIdx).
    """
    knn = matcher.knnMatch(desc_q, desc_t, k=2)
    kept, mapping = [], {}
    for pair in knn:
        if len(pair) < 2:
            continue
        best, second = pair
        if best.distance < ratio * second.distance:
            kept.append(best)
            mapping[best.queryIdx] = best.trainIdx
    return kept, mapping


def mutual_matches(desc_a: np.ndarray, desc_b: np.ndarray, ratio: float):
    """Bidirectional consistency filter.

    Implementation, precisely:

      1. Match archival -> modern with k=2 and apply the ratio test. This gives
         a partial map  f: i -> j  (archival index i prefers modern index j).
      2. Independently match modern -> archival with k=2 and apply the SAME
         ratio test, giving  g: j -> i'.
      3. Keep the forward match (i, j) if and only if  g(j) == i.

    So a correspondence survives only when i is j's ratio-test-passing best
    match *and* j is i's. This is stricter than OpenCV's
    BFMatcher(crossCheck=True), which cannot be combined with knnMatch(k=2)
    and therefore cannot be combined with a ratio test at all; here both
    filters are applied in both directions and then intersected.

    Why this matters for this data specifically: a spurious archival->modern
    match onto, say, a modern tourist can pass the forward ratio test because
    that archival patch is locally distinctive. It will almost never pass in
    reverse, because the tourist's own nearest archival neighbour is some
    unrelated patch. Asymmetric noise is exactly what this removes.
    """
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    fwd, fwd_map = ratio_filtered(matcher, desc_a, desc_b, ratio)
    rev, rev_map = ratio_filtered(matcher, desc_b, desc_a, ratio)
    mutual = [m for m in fwd if rev_map.get(m.trainIdx, -1) == m.queryIdx]
    return mutual, fwd, rev


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------


def estimate_homography(kp_a, kp_b, matches, method: str, threshold: float, iters: int):
    src = np.float32([kp_a[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([kp_b[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    cv_method = cv2.USAC_MAGSAC if method == "magsac" else cv2.RANSAC
    H, mask = cv2.findHomography(
        src,
        dst,
        cv_method,
        ransacReprojThreshold=threshold,
        maxIters=iters,
        confidence=0.999,
    )
    return H, mask, src, dst


def reprojection_errors(H, src, dst) -> np.ndarray:
    """||project(H, x_archival) - x_modern||_2, in modern working pixels.

    Over inliers this is bounded above by the RANSAC threshold BY
    CONSTRUCTION. The baseline demonstrated the danger: it reported 1.11 px
    RMSE on a completely degenerate homography. It is recorded here as a
    sanity value only and is never used as a validity gate.
    """
    projected = cv2.perspectiveTransform(src, H)
    return np.linalg.norm(projected.reshape(-1, 2) - dst.reshape(-1, 2), axis=1)


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


def describe_homography(H: np.ndarray, src_shape, dst_shape) -> dict:
    """Geometric diagnostics, including two checks stronger than the baseline's.

    `condition_number` is scale-invariant, unlike |det(H)|.

    `corner_w_values` are the third homogeneous coordinates of the four mapped
    corners. If they do not all share a sign, the vanishing line of the
    homography passes through the image: part of the source is being mapped
    through infinity, which is what produces the radial-smear artifact seen in
    the baseline. A valid registration cannot have this.
    """
    h_s, w_s = src_shape[:2]
    h_d, w_d = dst_shape[:2]

    corners = np.float32([[0, 0], [w_s, 0], [w_s, h_s], [0, h_s]]).reshape(-1, 1, 2)
    quad = cv2.perspectiveTransform(corners, H).reshape(-1, 2)

    xs = np.array([0, w_s, w_s, 0], dtype=np.float64)
    ys = np.array([0, 0, h_s, h_s], dtype=np.float64)
    w_vals = H[2, 0] * xs + H[2, 1] * ys + H[2, 2]
    same_sign = bool(np.all(w_vals > 0) or np.all(w_vals < 0))

    area = abs(cv2.contourArea(quad.reshape(-1, 1, 2).astype(np.float32)))
    convex = bool(cv2.isContourConvex(np.int32(np.round(quad))))
    singular_values = np.linalg.svd(H[:2, :2], compute_uv=False)

    return {
        "matrix": H.tolist(),
        "determinant": float(np.linalg.det(H)),
        "condition_number": float(np.linalg.cond(H)),
        "corner_w_values": w_vals.tolist(),
        "corner_w_all_same_sign": same_sign,
        "warped_corners_in_modern_roi_coords": quad.tolist(),
        "warped_quad_area_px": float(area),
        "warped_quad_area_ratio_vs_modern_roi": float(area / (w_d * h_d)),
        "warped_quad_is_convex": convex,
        "approx_scale_from_affine_part": [
            float(singular_values[0]),
            float(singular_values[1]),
        ],
        "approx_rotation_deg_from_affine_part": float(
            np.degrees(np.arctan2(H[1, 0], H[0, 0]))
        ),
    }


def overlap_ncc(warped_bgr, modern_bgr, valid_mask):
    """Pearson correlation of greyscale intensity over the valid overlap.

    The only reported signal not derived from the same correspondences RANSAC
    used, so the only one able to disagree with them. Still weak evidence: a
    sepia print and a colour photo of the same wall are not linearly related
    in intensity.
    """
    if valid_mask.sum() < 1000:
        return None
    a = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2GRAY)[valid_mask].astype(np.float64)
    b = cv2.cvtColor(modern_bgr, cv2.COLOR_BGR2GRAY)[valid_mask].astype(np.float64)
    if a.std() < 1e-6 or b.std() < 1e-6:
        return None
    return {
        "overlap_pixels": int(valid_mask.sum()),
        "overlap_fraction_of_modern_roi": float(valid_mask.mean()),
        "pearson_ncc": float(np.corrcoef(a, b)[0, 1]),
    }


# --------------------------------------------------------------------------
# Experiment driver
# --------------------------------------------------------------------------


def run(args) -> int:
    t_start = time.perf_counter()
    cv2.setRNGSeed(args.seed)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics: dict = {
        "experiment": "sift_improved_registration",
        "monument": "humayuns_tomb",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "failure_reason": None,
        "interventions": [
            "CLAHE photometric normalisation",
            "RootSIFT descriptors (L1-normalise + element-wise sqrt)",
            "ROI restriction removing paper border and ground plane",
            "Mutual (bidirectional) match consistency",
        ],
        "parameters": {
            "max_working_dimension_px": args.max_dim,
            "sift_nfeatures": args.nfeatures,
            "clahe_clip_limit": CLAHE_CLIP_LIMIT,
            "clahe_tile_grid_size": list(CLAHE_TILE_GRID),
            "lowe_ratio_threshold": args.ratio,
            "mutual_matching": True,
            "ransac_method_primary": args.ransac,
            "ransac_reproj_threshold_px": args.ransac_threshold,
            "ransac_max_iters": args.max_iters,
            "ransac_confidence": 0.999,
            "rng_seed": args.seed,
        },
        "validity_gates": {
            "min_descriptors_per_image": MIN_DESCRIPTORS,
            "min_good_matches": MIN_GOOD_MATCHES,
            "min_inliers": MIN_INLIERS,
            "min_inlier_ratio": MIN_INLIER_RATIO,
            "min_inlier_hull_area_fraction": MIN_INLIER_HULL_AREA_FRACTION,
            "warped_quad_area_ratio_bounds": [
                MIN_WARPED_AREA_RATIO,
                MAX_WARPED_AREA_RATIO,
            ],
            "max_condition_number": MAX_CONDITION_NUMBER,
            "require_corner_w_same_sign": True,
        },
        "checks": [],
        "environment": {
            "python": sys.version.split()[0],
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "notes": [
            "ROI boundaries were fixed from a fractional coordinate grid and "
            "visually verified before any matching was run; they were not "
            "revised after seeing match results.",
            "Ratio threshold, RANSAC method and all carried-over gate "
            "thresholds are identical to the baseline so the comparison is "
            "controlled.",
            "Inlier reprojection error is bounded above by the RANSAC "
            "threshold by construction and is never used as a validity gate.",
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
            "channels": int(archival.shape[2]),
        },
        "modern": {
            "resolved_path": str(modern_path),
            "width": int(modern.shape[1]),
            "height": int(modern.shape[0]),
            "channels": int(modern.shape[2]),
        },
    }
    print(f"archival: {archival.shape[1]}x{archival.shape[0]}")
    print(f"modern:   {modern.shape[1]}x{modern.shape[0]}")

    # -- Intervention 3: ROI ------------------------------------------------
    box_a = roi_pixels(archival, ROI_ARCHIVAL)
    box_b = roi_pixels(modern, ROI_MODERN)
    metrics["roi"] = {
        "rule": "Keep the built structure -- from the top of the photographic "
        "content down to the base of the plinth arcade -- and discard the "
        "ground plane below it. Boundaries fixed before matching.",
        "archival": {
            **box_a,
            "justification": "5% inset removes the 3-4% photographic paper "
            "border; y=0.65 cuts just below the arcade base, excluding the "
            "garden foreground.",
        },
        "modern": {
            **box_b,
            "justification": "No lateral inset (no paper border); y=0.75 cuts "
            "just below the same arcade base, excluding lawn, path and "
            "visitors.",
        },
        "crops_are_deliberately_not_identical": True,
    }

    cv2.imwrite(
        str(out_dir / "03_archival_roi.jpg"),
        draw_roi_visualization(archival, box_a, args.max_dim),
    )
    cv2.imwrite(
        str(out_dir / "04_modern_roi.jpg"),
        draw_roi_visualization(modern, box_b, args.max_dim),
    )

    pa, pb = box_a["pixels"], box_b["pixels"]
    crop_a = archival[pa["y0"] : pa["y1"], pa["x0"] : pa["x1"]]
    crop_b = modern[pb["y0"] : pb["y1"], pb["x0"] : pb["x1"]]

    work_a, scale_a = resize_to_working(crop_a, args.max_dim)
    work_b, scale_b = resize_to_working(crop_b, args.max_dim)
    metrics["working_images"] = {
        "archival": {
            "width": int(work_a.shape[1]),
            "height": int(work_a.shape[0]),
            **scale_a,
        },
        "modern": {
            "width": int(work_b.shape[1]),
            "height": int(work_b.shape[0]),
            **scale_b,
        },
        "note": "Working images are the ROI CROPS resized, so working "
        "coordinates are relative to the crop origin, not the original.",
    }
    print(
        f"roi:      archival {work_a.shape[1]}x{work_a.shape[0]}, "
        f"modern {work_b.shape[1]}x{work_b.shape[0]}"
    )

    # -- Intervention 1: CLAHE ----------------------------------------------
    t0 = time.perf_counter()
    gray_a = normalize_clahe(
        cv2.cvtColor(work_a, cv2.COLOR_BGR2GRAY), CLAHE_CLIP_LIMIT, CLAHE_TILE_GRID
    )
    gray_b = normalize_clahe(
        cv2.cvtColor(work_b, cv2.COLOR_BGR2GRAY), CLAHE_CLIP_LIMIT, CLAHE_TILE_GRID
    )
    timings["clahe"] = time.perf_counter() - t0
    cv2.imwrite(str(out_dir / "01_archival_normalized.jpg"), gray_a)
    cv2.imwrite(str(out_dir / "02_modern_normalized.jpg"), gray_b)

    # -- SIFT ---------------------------------------------------------------
    sift = cv2.SIFT_create(nfeatures=args.nfeatures)

    t0 = time.perf_counter()
    kp_a, desc_a_raw = sift.detectAndCompute(gray_a, None)
    kp_b, desc_b_raw = sift.detectAndCompute(gray_b, None)
    kp_a, kp_b = list(kp_a), list(kp_b)
    timings["sift"] = time.perf_counter() - t0

    # Reference measurement: SIFT on the FULL frame (CLAHE'd, same working
    # scale) so the effect of the ROI restriction is quantifiable rather than
    # asserted. Costs one extra detection pass and nothing else uses it.
    t0 = time.perf_counter()
    roi_effect = {}
    for label, image, box in (
        ("archival", archival, box_a),
        ("modern", modern, box_b),
    ):
        full_work, full_scale = resize_to_working(image, args.max_dim)
        full_gray = normalize_clahe(
            cv2.cvtColor(full_work, cv2.COLOR_BGR2GRAY),
            CLAHE_CLIP_LIMIT,
            CLAHE_TILE_GRID,
        )
        full_kp = sift.detect(full_gray, None)
        p = box["pixels"]
        sx, sy = full_scale["scale_x"], full_scale["scale_y"]
        x0, y0 = p["x0"] * sx, p["y0"] * sy
        x1, y1 = p["x1"] * sx, p["y1"] * sy
        inside = sum(1 for k in full_kp if x0 <= k.pt[0] < x1 and y0 <= k.pt[1] < y1)
        roi_effect[label] = {
            "keypoints_full_frame": len(full_kp),
            "keypoints_full_frame_inside_roi": inside,
            "keypoints_full_frame_discarded_by_roi": len(full_kp) - inside,
            "fraction_of_full_frame_keypoints_discarded": (
                1.0 - inside / len(full_kp) if len(full_kp) else 0.0
            ),
        }
    timings["roi_reference_detection"] = time.perf_counter() - t0

    n_desc_a = 0 if desc_a_raw is None else int(desc_a_raw.shape[0])
    n_desc_b = 0 if desc_b_raw is None else int(desc_b_raw.shape[0])

    # -- Intervention 2: RootSIFT -------------------------------------------
    t0 = time.perf_counter()
    desc_a, zero_a = to_root_sift(desc_a_raw)
    desc_b, zero_b = to_root_sift(desc_b_raw)
    timings["rootsift"] = time.perf_counter() - t0

    metrics["features"] = {
        "keypoints_before_roi_restriction": roi_effect,
        "archival_keypoints_after_roi": len(kp_a),
        "modern_keypoints_after_roi": len(kp_b),
        "archival_descriptors": n_desc_a,
        "modern_descriptors": n_desc_b,
        "descriptor_dim": 0 if desc_a_raw is None else int(desc_a_raw.shape[1]),
        "descriptor_variant": "RootSIFT (L1-normalise then element-wise sqrt; "
        "Euclidean distance on these equals Hellinger distance on the "
        "original SIFT histograms)",
        "zero_norm_descriptors_archival": zero_a,
        "zero_norm_descriptors_modern": zero_b,
    }
    print(f"keypoints: archival {len(kp_a)}, modern {len(kp_b)}")

    if not gate(
        "sufficient_descriptors",
        n_desc_a >= MIN_DESCRIPTORS and n_desc_b >= MIN_DESCRIPTORS,
        {"archival": n_desc_a, "modern": n_desc_b},
        MIN_DESCRIPTORS,
        "Below this, feature extraction itself failed.",
    ):
        return finish(
            "failed",
            f"Insufficient descriptors (archival={n_desc_a}, modern={n_desc_b}).",
        )

    # -- Intervention 4: mutual matching ------------------------------------
    t0 = time.perf_counter()
    mutual, fwd, rev = mutual_matches(desc_a, desc_b, args.ratio)
    timings["match"] = time.perf_counter() - t0

    metrics["matching"] = {
        "matcher": "BFMatcher(NORM_L2) on RootSIFT, knn k=2, exact, run in "
        "both directions",
        "ratio_threshold": args.ratio,
        "forward_filtered_match_count": len(fwd),
        "reverse_filtered_match_count": len(rev),
        "mutual_match_count": len(mutual),
        "mutual_survival_rate_of_forward": (len(mutual) / len(fwd)) if fwd else 0.0,
        "mutual_filter_definition": "Keep forward match (i -> j) iff the "
        "reverse ratio-filtered match for j maps back to i. Stricter than "
        "BFMatcher(crossCheck=True), which cannot be combined with a ratio "
        "test because it is incompatible with knnMatch(k=2).",
        "mutual_match_distance_stats": (
            {
                "min": float(min(m.distance for m in mutual)),
                "median": float(np.median([m.distance for m in mutual])),
                "max": float(max(m.distance for m in mutual)),
            }
            if mutual
            else None
        ),
    }
    print(f"matches:  forward {len(fwd)}, reverse {len(rev)}, mutual {len(mutual)}")

    if fwd:
        drawn = sorted(fwd, key=lambda m: m.distance)[: args.max_drawn_matches]
        cv2.imwrite(
            str(out_dir / "09_forward_matches.jpg"),
            cv2.drawMatches(
                work_a,
                kp_a,
                work_b,
                kp_b,
                drawn,
                None,
                flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            ),
        )
    if mutual:
        drawn = sorted(mutual, key=lambda m: m.distance)[: args.max_drawn_matches]
        metrics["matching"]["drawn_in_05_good_matches"] = len(drawn)
        cv2.imwrite(
            str(out_dir / "05_good_matches.jpg"),
            cv2.drawMatches(
                work_a,
                kp_a,
                work_b,
                kp_b,
                drawn,
                None,
                flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            ),
        )

    match_gate_passed = gate(
        "sufficient_good_matches",
        len(mutual) >= MIN_GOOD_MATCHES,
        len(mutual),
        MIN_GOOD_MATCHES,
        "A homography needs 4 points; near that count RANSAC has no consensus "
        "to measure and always 'succeeds'.",
    )
    # Failing this gate does NOT stop the run: the geometric diagnostics are
    # still worth producing for inspection, and the resulting warp/overlay is
    # banner-stamped and reported as failed. Below 4 matches a homography
    # cannot be formed at all, so there is genuinely nothing left to compute.
    if len(mutual) < 4:
        return finish(
            "failed",
            f"Only {len(mutual)} mutually consistent matches; a homography "
            "requires at least 4. No geometric diagnostics are possible.",
        )

    # -- Geometry -----------------------------------------------------------
    t0 = time.perf_counter()
    H, mask, src, dst = estimate_homography(
        kp_a, kp_b, mutual, args.ransac, args.ransac_threshold, args.max_iters
    )
    timings["ransac"] = time.perf_counter() - t0

    # Cross-check with the alternative robust estimator. Recorded only; the
    # primary estimator matches the baseline for comparability.
    H_x, mask_x, _, _ = estimate_homography(
        kp_a,
        kp_b,
        mutual,
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
        "Scale-invariant degeneracy test. Replaces the baseline's absolute "
        "|det(H)| test, which was scale-dependent and passed the degenerate "
        "baseline homography (cond was 1.79e9)."
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
        return finish(
            "failed",
            "RANSAC returned no finite homography; no geometric diagnostics "
            "are possible.",
        )

    # An ill-conditioned H is still warped and saved (banner-stamped) so the
    # failure is inspectable, exactly as the baseline's radial smear was.
    cond = float(np.linalg.cond(H))
    conditioning_passed = gate(
        "homography_well_conditioned",
        cond < MAX_CONDITION_NUMBER,
        {"estimated": True, "condition_number": cond},
        f"finite and cond(H) < {MAX_CONDITION_NUMBER:.0e}",
        conditioning_rationale,
    )

    inlier_mask = mask.ravel().astype(bool)
    n_inliers = int(inlier_mask.sum())
    inlier_ratio = n_inliers / len(mutual)

    inlier_matches = [m for m, keep in zip(mutual, inlier_mask) if keep]
    if inlier_matches:
        cv2.imwrite(
            str(out_dir / "06_inlier_matches.jpg"),
            cv2.drawMatches(
                work_a,
                kp_a,
                work_b,
                kp_b,
                inlier_matches,
                None,
                matchColor=(0, 255, 0),
                flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            ),
        )

    hull_fraction = 0.0
    if n_inliers >= 3:
        pts = src.reshape(-1, 2)[inlier_mask].astype(np.float32)
        hull = cv2.convexHull(pts.reshape(-1, 1, 2))
        hull_fraction = float(
            abs(cv2.contourArea(hull)) / (work_a.shape[0] * work_a.shape[1])
        )

    errors_all = reprojection_errors(H, src, dst)
    metrics["ransac"] = {
        "method": args.ransac,
        "reproj_threshold_px": args.ransac_threshold,
        "inlier_count": n_inliers,
        "inlier_ratio": float(inlier_ratio),
        "inlier_hull_area_fraction_of_archival_roi": hull_fraction,
    }
    metrics["homography"] = describe_homography(H, work_a.shape, work_b.shape)
    metrics["geometric_error"] = {
        "definition": "Forward reprojection error ||project(H, x_archival) - "
        "x_modern||_2, in modern ROI working pixels.",
        "caveat": "Bounded above by the RANSAC threshold over inliers by "
        "construction. Not used as a validity gate.",
        "over_ransac_inliers": error_summary(errors_all[inlier_mask]),
        "over_all_mutual_matches": error_summary(errors_all),
    }
    print(f"ransac:   inliers {n_inliers}/{len(mutual)} (ratio {inlier_ratio:.3f})")

    # -- Warp + overlay -----------------------------------------------------
    t0 = time.perf_counter()
    h_m, w_m = work_b.shape[:2]
    registered = cv2.warpPerspective(work_a, H, (w_m, h_m))
    coverage = cv2.warpPerspective(
        np.full(work_a.shape[:2], 255, np.uint8), H, (w_m, h_m)
    )
    valid = coverage > 0
    overlay = cv2.addWeighted(registered, 0.5, work_b, 0.5, 0.0)
    timings["warp"] = time.perf_counter() - t0

    metrics["photometric_check"] = {
        "definition": "Pearson correlation of greyscale intensity over the "
        "valid warp overlap. Independent of the RANSAC correspondences but "
        "weak evidence given the era and colour gap.",
        **(overlap_ncc(registered, work_b, valid) or {}),
    }

    # -- Remaining gates ----------------------------------------------------
    hom = metrics["homography"]
    passed = match_gate_passed and conditioning_passed
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
        "consistent and globally unconstrained. This is what the baseline hit "
        "(1.1% hull).",
    )
    passed &= gate(
        "warped_frame_sane",
        hom["warped_quad_is_convex"]
        and MIN_WARPED_AREA_RATIO
        <= hom["warped_quad_area_ratio_vs_modern_roi"]
        <= MAX_WARPED_AREA_RATIO,
        {
            "convex": hom["warped_quad_is_convex"],
            "area_ratio": hom["warped_quad_area_ratio_vs_modern_roi"],
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
        "If the sign flips, the homography's vanishing line passes through "
        "the image and part of the source is mapped through infinity. This is "
        "the direct cause of the baseline's radial-smear overlay.",
    )

    if not passed:
        failed_names = [c["name"] for c in checks if not c["passed"]]
        banner = "REGISTRATION NOT VALIDATED - " + ", ".join(failed_names)
        registered = annotate_untrusted(registered, banner)
        overlay = annotate_untrusted(overlay, banner)

    cv2.imwrite(str(out_dir / "07_registered_archival.jpg"), registered)
    cv2.imwrite(str(out_dir / "08_overlay.jpg"), overlay)

    if not passed:
        failed_names = ", ".join(c["name"] for c in checks if not c["passed"])
        # "failed" when the correspondence set itself was never adequate;
        # "partial" when enough matches existed but the geometry did not hold.
        status = "partial" if match_gate_passed else "failed"
        return finish(
            status,
            f"Registration is not valid. Failed checks: {failed_names}. "
            "Diagnostics were still written for inspection; the warp and "
            "overlay carry a warning banner and must not be treated as a "
            "valid alignment.",
        )

    return finish("success", None)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Improved classical registration: CLAHE + RootSIFT + ROI "
        "+ mutual matching."
    )
    parser.add_argument("--data-dir", default=str(repo_root / "data" / "humayun"))
    parser.add_argument(
        "--output-dir",
        default=str(repo_root / "outputs" / "registration" / "sift_improved"),
    )
    parser.add_argument("--max-dim", type=int, default=1600)
    parser.add_argument("--nfeatures", type=int, default=0, help="0 = unlimited")
    parser.add_argument("--ratio", type=float, default=0.75)
    parser.add_argument("--ransac", choices=["ransac", "magsac"], default="ransac")
    parser.add_argument("--ransac-threshold", type=float, default=3.0)
    parser.add_argument("--max-iters", type=int, default=10000)
    parser.add_argument("--max-drawn-matches", type=int, default=150)
    parser.add_argument("--seed", type=int, default=0)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
