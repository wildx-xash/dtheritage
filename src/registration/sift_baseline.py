"""
SIFT-based archival-to-modern image registration baseline.

Feasibility experiment for the SIH heritage project. This is EXPERIMENT code:
it measures whether a classical SIFT + ratio-test + RANSAC-homography pipeline
can align a ~1860s photograph of Humayun's Tomb with a modern photograph.

Run from the repository root:

    python src/registration/sift_baseline.py

Scope caveats, stated explicitly because they bound what the output means:

  * A single homography is exact only for a planar scene or a pure camera
    rotation. This scene is neither: the facade is roughly planar, but the
    plinth arcade, garden and trees lie at very different depths, and the two
    photographs were taken from different 3D positions. The best achievable
    result is therefore alignment of the facade plane with parallax error
    everywhere else. That is expected, not a bug.
  * Successful geometric registration says nothing about structural condition.
    It is a prerequisite for change analysis, not evidence of change.

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
# Validity gates.
#
# These encode what we are willing to call "a technically valid registration".
# They are deliberately conservative: the failure mode we most want to avoid is
# a plausible-looking overlay produced by a homography that is not actually
# supported by the evidence.
# --------------------------------------------------------------------------

MIN_DESCRIPTORS = 100
"""Fewer than this in either image means feature extraction itself failed."""

MIN_GOOD_MATCHES = 15
"""A homography needs 4 correspondences. At 4, RANSAC has no consensus to
measure and will always 'succeed'. 15 is the practical floor at which the
inlier count carries information."""

MIN_INLIERS = 12
MIN_INLIER_RATIO = 0.25
"""If under a quarter of the ratio-test survivors agree on one homography, the
consensus set is more likely a coincidental cluster than a real alignment."""

MIN_INLIER_HULL_AREA_FRACTION = 0.05
"""Spatial-degeneracy guard. Inliers packed into one window arch yield a
homography that is locally perfect and globally wild, while still passing every
count-based check. We require the convex hull of the inlier keypoints to cover
at least this fraction of the archival working image."""

MIN_WARPED_AREA_RATIO = 0.05
MAX_WARPED_AREA_RATIO = 20.0
"""Sanity bounds on where the archival frame lands in modern coordinates. A
collapsed or exploded quadrilateral is the signature of a degenerate H."""

MIN_ABS_DETERMINANT = 1e-6
"""Guards the singular / rank-deficient homography."""


# --------------------------------------------------------------------------
# I/O helpers
# --------------------------------------------------------------------------


def resolve_input(directory: Path, stem: str) -> Path:
    """Find the input image for `stem` inside `directory`.

    The brief specifies `archival.jpg` / `modern.jpg`, but the files as
    delivered are named `archival.jpg.jpg` / `modern.jpg.jpg` (Windows
    hidden-extension artifact). Rather than rename the originals -- which the
    experiment protocol forbids -- we accept either spelling and record which
    path was actually used in metrics.json.
    """
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
    """Read a BGR image, failing loudly. cv2.imread returns None on failure
    instead of raising, which is a classic source of silent downstream errors."""
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not decode image: {path}")
    return image


def make_working_copy(image: np.ndarray, max_dim: int) -> tuple[np.ndarray, dict]:
    """Downscale a copy so the longest side is at most `max_dim`.

    Returns the copy and a record of exactly what scaling was applied, so the
    homography estimated in working coordinates can be lifted back to full
    resolution later. INTER_AREA is the correct interpolation for downscaling:
    it averages over the source footprint rather than point-sampling, which
    avoids the aliasing that would otherwise inject spurious SIFT keypoints.
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return image.copy(), {
            "resized": False,
            "scale_x": 1.0,
            "scale_y": 1.0,
            "interpolation": None,
        }

    factor = max_dim / longest
    new_w, new_h = int(round(w * factor)), int(round(h * factor))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, {
        "resized": True,
        # Actual achieved scale, not the requested factor -- integer rounding
        # of the target size makes these differ slightly.
        "scale_x": new_w / w,
        "scale_y": new_h / h,
        "interpolation": "INTER_AREA",
    }


def annotate_untrusted(image: np.ndarray, message: str) -> np.ndarray:
    """Burn a warning banner into an image.

    Written onto any warp/overlay produced by a run that failed validation, so
    that an unvalidated result cannot be mistaken for a good one if the file is
    ever viewed outside the context of metrics.json.
    """
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
        0.7 * scale,
        (255, 255, 255),
        max(1, int(round(2 * scale))),
        cv2.LINE_AA,
    )
    return out


# --------------------------------------------------------------------------
# Pipeline stages
# --------------------------------------------------------------------------


def detect_sift(gray: np.ndarray, n_features: int) -> tuple[list, np.ndarray | None]:
    """SIFT keypoints + descriptors.

    SIFT finds blob-like extrema across a scale-space pyramid and describes a
    local patch as a 128-D histogram of gradient orientations, normalised for
    contrast. That makes it invariant to scale, in-plane rotation and affine
    illumination change -- but *not* to the kind of appearance change we have
    here (monochrome print vs colour photo, different sun angle, 160 years of
    weathering), which is precisely what this experiment is testing.
    """
    sift = cv2.SIFT_create(nfeatures=n_features)
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    return list(keypoints), descriptors


def match_descriptors(
    desc_a: np.ndarray, desc_b: np.ndarray, ratio: float
) -> tuple[list, int]:
    """Brute-force L2 k-NN match followed by Lowe's ratio test.

    Exact brute force rather than FLANN: at a few thousand descriptors it costs
    well under a second, and it makes the match set a property of the data
    rather than of an approximate-index configuration.

    The ratio test discards a match when the nearest and second-nearest
    descriptor distances are close, i.e. when the correspondence is ambiguous.
    Repetitive architecture -- and this facade is nothing but repeated arches --
    is exactly where that ambiguity arises, so this filter does most of the
    real work here.

    Returns (good matches, raw knn query count).
    """
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    knn = matcher.knnMatch(desc_a, desc_b, k=2)

    good = []
    for pair in knn:
        if len(pair) < 2:
            continue
        best, second = pair
        if best.distance < ratio * second.distance:
            good.append(best)
    return good, len(knn)


def estimate_homography(
    kp_a: list, kp_b: list, matches: list, method: str, threshold: float, max_iters: int
):
    """Robustly fit the archival -> modern homography.

    RANSAC repeatedly draws the 4-point minimal sample a homography needs,
    fits, and counts how many of the remaining correspondences land within
    `threshold` pixels of their predicted position. The model with the largest
    consensus set wins. This is what lets us tolerate a match set that is
    mostly wrong, which -- across a 160-year appearance gap -- it will be.
    """
    src = np.float32([kp_a[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([kp_b[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    cv_method = cv2.USAC_MAGSAC if method == "magsac" else cv2.RANSAC
    H, mask = cv2.findHomography(
        src,
        dst,
        cv_method,
        ransacReprojThreshold=threshold,
        maxIters=max_iters,
        confidence=0.999,
    )
    return H, mask, src, dst


def reprojection_errors(H: np.ndarray, src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Per-correspondence forward reprojection error, in modern working pixels.

    Defined as ||project(H, x_archival) - x_modern||_2. Note the asymmetry: this
    is the forward error only, and on inliers it is bounded above by the RANSAC
    threshold *by construction*. It is a sanity check, not an independent
    measure of registration quality.
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


def describe_homography(H: np.ndarray, archival_shape, modern_shape) -> dict:
    """Interpretable diagnostics derived from H.

    Where the archival frame lands, whether that quadrilateral is still convex
    (a non-convex or self-intersecting result means the homography folded the
    plane), and the approximate similarity transform implied by the affine part.
    """
    h_a, w_a = archival_shape[:2]
    h_m, w_m = modern_shape[:2]

    corners = np.float32([[0, 0], [w_a, 0], [w_a, h_a], [0, h_a]]).reshape(-1, 1, 2)
    warped_corners = cv2.perspectiveTransform(corners, H)
    quad = warped_corners.reshape(-1, 2)

    area = abs(cv2.contourArea(warped_corners))
    convex = bool(cv2.isContourConvex(np.int32(np.round(quad))))

    # Approximate scale/rotation from the 2x2 affine block. Only meaningful
    # when the projective terms are small, so it is labelled approximate.
    affine = H[:2, :2]
    singular_values = np.linalg.svd(affine, compute_uv=False)
    rotation_deg = float(np.degrees(np.arctan2(H[1, 0], H[0, 0])))

    return {
        "matrix": H.tolist(),
        "determinant": float(np.linalg.det(H)),
        "warped_archival_corners_in_modern_coords": quad.tolist(),
        "warped_quad_area_px": float(area),
        "warped_quad_area_ratio_vs_modern": float(area / (w_m * h_m)),
        "warped_quad_is_convex": convex,
        "approx_scale_from_affine_part": [
            float(singular_values[0]),
            float(singular_values[1]),
        ],
        "approx_rotation_deg_from_affine_part": rotation_deg,
    }


def overlap_ncc(warped_bgr: np.ndarray, modern_bgr: np.ndarray, valid_mask: np.ndarray):
    """Pearson correlation of greyscale intensity over the valid overlap.

    This is the only quality signal in the report that is *not* derived from
    the same correspondences RANSAC used, so it is the only one that can
    disagree with them. It is nonetheless weak evidence here: a sepia albumen
    print and a modern colour photograph of the same wall do not have linearly
    related intensities, so a low value does not by itself imply misalignment.
    """
    if valid_mask.sum() < 1000:
        return None
    a = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2GRAY)[valid_mask].astype(np.float64)
    b = cv2.cvtColor(modern_bgr, cv2.COLOR_BGR2GRAY)[valid_mask].astype(np.float64)
    if a.std() < 1e-6 or b.std() < 1e-6:
        return None
    return {
        "overlap_pixels": int(valid_mask.sum()),
        "overlap_fraction_of_modern": float(valid_mask.mean()),
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
        "experiment": "sift_baseline_registration",
        "monument": "humayuns_tomb",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "failure_reason": None,
        "parameters": {
            "max_working_dimension_px": args.max_dim,
            "sift_nfeatures": args.nfeatures,
            "lowe_ratio_threshold": args.ratio,
            "ransac_method": args.ransac,
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
        },
        "checks": [],
        "environment": {
            "python": sys.version.split()[0],
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "notes": [
            "A single homography is exact only for a planar scene or a pure "
            "camera rotation; this scene is neither, so residual parallax at "
            "non-facade depths is expected rather than anomalous.",
            "Reprojection error over inliers is bounded above by the RANSAC "
            "threshold by construction and is a sanity check, not an "
            "independent quality measure.",
            "Geometric registration is a prerequisite for change analysis. It "
            "is not evidence of structural change, damage or deterioration.",
        ],
    }

    checks = metrics["checks"]
    timings: dict = {}
    metrics["timings_seconds"] = timings

    def gate(name: str, passed: bool, value, threshold, rationale: str) -> bool:
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

    # -- 1. Load -----------------------------------------------------------
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
            "requested_name": "archival.jpg",
            "width": int(archival.shape[1]),
            "height": int(archival.shape[0]),
            "channels": int(archival.shape[2]),
        },
        "modern": {
            "resolved_path": str(modern_path),
            "requested_name": "modern.jpg",
            "width": int(modern.shape[1]),
            "height": int(modern.shape[0]),
            "channels": int(modern.shape[2]),
        },
    }
    print(f"archival: {archival_path.name}  {archival.shape[1]}x{archival.shape[0]}")
    print(f"modern:   {modern_path.name}  {modern.shape[1]}x{modern.shape[0]}")

    # -- 2/3/4. Working copies (originals are never written) ---------------
    work_a, scale_a = make_working_copy(archival, args.max_dim)
    work_b, scale_b = make_working_copy(modern, args.max_dim)
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
    }
    print(
        f"working:  archival {work_a.shape[1]}x{work_a.shape[0]}, "
        f"modern {work_b.shape[1]}x{work_b.shape[0]}"
    )

    # -- 5. Greyscale for feature extraction -------------------------------
    gray_a = cv2.cvtColor(work_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(work_b, cv2.COLOR_BGR2GRAY)

    # -- 6. SIFT -----------------------------------------------------------
    t0 = time.perf_counter()
    kp_a, desc_a = detect_sift(gray_a, args.nfeatures)
    kp_b, desc_b = detect_sift(gray_b, args.nfeatures)
    timings["sift"] = time.perf_counter() - t0

    n_desc_a = 0 if desc_a is None else int(desc_a.shape[0])
    n_desc_b = 0 if desc_b is None else int(desc_b.shape[0])
    metrics["features"] = {
        "archival_keypoints": len(kp_a),
        "modern_keypoints": len(kp_b),
        "archival_descriptors": n_desc_a,
        "modern_descriptors": n_desc_b,
        "descriptor_dim": 0 if desc_a is None else int(desc_a.shape[1]),
    }
    print(f"keypoints: archival {len(kp_a)}, modern {len(kp_b)}")

    cv2.imwrite(
        str(out_dir / "01_keypoints_archival.jpg"),
        cv2.drawKeypoints(
            work_a, kp_a, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        ),
    )
    cv2.imwrite(
        str(out_dir / "02_keypoints_modern.jpg"),
        cv2.drawKeypoints(
            work_b, kp_b, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        ),
    )

    if not gate(
        "sufficient_descriptors",
        n_desc_a >= MIN_DESCRIPTORS and n_desc_b >= MIN_DESCRIPTORS,
        {"archival": n_desc_a, "modern": n_desc_b},
        MIN_DESCRIPTORS,
        "Below this, SIFT extraction itself failed and matching is meaningless.",
    ):
        return finish(
            "failed",
            f"Insufficient SIFT descriptors (archival={n_desc_a}, "
            f"modern={n_desc_b}, required>={MIN_DESCRIPTORS}).",
        )

    # -- 7/8. Match + ratio test -------------------------------------------
    t0 = time.perf_counter()
    good, n_raw = match_descriptors(desc_a, desc_b, args.ratio)
    timings["match"] = time.perf_counter() - t0

    metrics["matching"] = {
        "matcher": "BFMatcher(NORM_L2), knn k=2, exact",
        "raw_knn_query_count": n_raw,
        "raw_descriptor_match_count": n_raw * 2,
        "filter": f"Lowe ratio test, threshold={args.ratio}",
        "good_match_count": len(good),
        "good_match_fraction_of_queries": (len(good) / n_raw) if n_raw else 0.0,
        "good_match_distance_stats": (
            {
                "min": float(min(m.distance for m in good)),
                "median": float(np.median([m.distance for m in good])),
                "max": float(max(m.distance for m in good)),
            }
            if good
            else None
        ),
    }
    print(f"matches:  raw knn queries {n_raw}, good after ratio test {len(good)}")

    if good:
        drawn = sorted(good, key=lambda m: m.distance)[: args.max_drawn_matches]
        metrics["matching"]["drawn_in_03_good_matches"] = len(drawn)
        cv2.imwrite(
            str(out_dir / "03_good_matches.jpg"),
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

    if not gate(
        "sufficient_good_matches",
        len(good) >= MIN_GOOD_MATCHES,
        len(good),
        MIN_GOOD_MATCHES,
        "A homography needs 4 points; near that count RANSAC has no consensus "
        "to measure and always 'succeeds'.",
    ):
        return finish(
            "failed",
            f"Too few matches survived the ratio test "
            f"({len(good)} < {MIN_GOOD_MATCHES}).",
        )

    # -- 9/10. RANSAC homography -------------------------------------------
    t0 = time.perf_counter()
    H, mask, src, dst = estimate_homography(
        kp_a, kp_b, good, args.ransac, args.ransac_threshold, args.max_iters
    )
    timings["ransac"] = time.perf_counter() - t0

    h_ok = H is not None and bool(np.all(np.isfinite(H)))
    det = float(np.linalg.det(H)) if h_ok else None
    h_ok = h_ok and abs(det) > MIN_ABS_DETERMINANT
    if not gate(
        "homography_estimated",
        h_ok,
        {"estimated": H is not None, "determinant": det},
        f"finite and |det| > {MIN_ABS_DETERMINANT}",
        "Guards the singular or non-finite solution.",
    ):
        metrics["ransac"] = {"inlier_count": 0, "inlier_ratio": 0.0}
        return finish(
            "failed",
            "RANSAC could not estimate a valid homography from the filtered "
            "correspondences.",
        )

    inlier_mask = mask.ravel().astype(bool)
    n_inliers = int(inlier_mask.sum())
    inlier_ratio = n_inliers / len(good)

    inlier_matches = [m for m, keep in zip(good, inlier_mask) if keep]
    if inlier_matches:
        cv2.imwrite(
            str(out_dir / "04_inlier_matches.jpg"),
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

    # Spatial spread of the inlier support in the archival image.
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
        "inlier_hull_area_fraction_of_archival_working": hull_fraction,
    }
    metrics["homography"] = describe_homography(H, work_a.shape, work_b.shape)
    metrics["geometric_error"] = {
        "definition": "Forward reprojection error ||project(H, x_archival) - "
        "x_modern||_2, in modern WORKING-image pixels.",
        "over_ransac_inliers": error_summary(errors_all[inlier_mask]),
        "over_all_good_matches": error_summary(errors_all),
    }

    print(f"ransac:   inliers {n_inliers}/{len(good)} (ratio {inlier_ratio:.3f})")

    # -- 11/12. Warp + overlay ---------------------------------------------
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
        "valid warp overlap. Independent of the RANSAC correspondences, but "
        "weak evidence: a sepia print and a colour photo of the same wall are "
        "not linearly related in intensity.",
        **(overlap_ncc(registered, work_b, valid) or {}),
    }

    # -- 13. Remaining validity gates --------------------------------------
    quad = metrics["homography"]
    passed = True
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
        quad["warped_quad_is_convex"]
        and MIN_WARPED_AREA_RATIO
        <= quad["warped_quad_area_ratio_vs_modern"]
        <= MAX_WARPED_AREA_RATIO,
        {
            "convex": quad["warped_quad_is_convex"],
            "area_ratio": quad["warped_quad_area_ratio_vs_modern"],
        },
        {
            "convex": True,
            "area_ratio_bounds": [MIN_WARPED_AREA_RATIO, MAX_WARPED_AREA_RATIO],
        },
        "A folded or collapsed quadrilateral is the signature of a degenerate "
        "homography that still produces an image.",
    )

    # -- 14. Save outputs --------------------------------------------------
    if not passed:
        failed_names = [c["name"] for c in checks if not c["passed"]]
        banner = "REGISTRATION NOT VALIDATED - " + ", ".join(failed_names)
        registered = annotate_untrusted(registered, banner)
        overlay = annotate_untrusted(overlay, banner)

    cv2.imwrite(str(out_dir / "05_registered_archival.jpg"), registered)
    cv2.imwrite(str(out_dir / "06_overlay.jpg"), overlay)

    if not passed:
        return finish(
            "partial",
            "A homography was estimated and the warp/overlay were written for "
            "inspection, but geometric verification was inadequate: "
            + ", ".join(c["name"] for c in checks if not c["passed"])
            + ". The saved images carry a warning banner and must not be "
            "treated as a valid alignment.",
        )

    return finish("success", None)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="SIFT archival-to-modern registration baseline."
    )
    parser.add_argument("--data-dir", default=str(repo_root / "data" / "humayun"))
    parser.add_argument(
        "--output-dir",
        default=str(repo_root / "outputs" / "registration" / "sift_baseline"),
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
