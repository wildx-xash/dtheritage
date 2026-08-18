"""
Multi-pair driver for the validated LoFTR registration baseline.

Phase question: does archival-modern pair / viewpoint selection materially
improve the geometry produced by the EXACT SAME validated LoFTR + global
homography pipeline?

This driver is deliberately thin and purely additive. It implements no
registration logic of its own. It:

  1. discovers and validates the canonical pair directories,
  2. runs src/registration/loftr_baseline.py once per pair,
  3. leaves the existing validated baseline result untouched (it is READ, and
     used as the reference row -- never re-run, never overwritten),
  4. writes each experimental run to its own output directory,
  5. reads back each metrics.json,
  6. emits a cross-pair comparison (comparison.json + comparison.md).

Why a subprocess rather than an import
--------------------------------------
loftr_baseline.py builds its argparse parser inside main(), so importing and
calling run() would mean re-declaring its defaults here -- and any future drift
between the two copies would silently change what "unchanged parameters" means.
Invoking the script as a subprocess with ONLY --data-dir and --output-dir
overridden guarantees that max-dim, confidence threshold, RANSAC method and
threshold, iteration count and seed all come from the validated file itself.

Nothing in loftr_baseline.py is modified, imported, or re-parameterised.

Run from the repository root:

    python src/registration/loftr_pairs.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Canonical pairs, in report order. Provenance is recorded here because source
# filenames are NOT recoverable from the copied pair directories, where every
# file is called archival.jpg / modern.jpg.
PAIRS = [
    {
        "pair_id": "pair01_archA_close_front",
        "archival_source": "archival.jpg",
        "modern_source": "Front_View.jpg",
        "purpose": "Validated archival plate against a closer/tighter modern "
        "frontal framing.",
    },
    {
        "pair_id": "pair02_archA_wide_front",
        "archival_source": "archival.jpg",
        "modern_source": "in_Delhi-Front_view.jpg",
        "purpose": "Same archival plate, wider / different camera distance. "
        "Isolates framing and camera-distance sensitivity.",
    },
    {
        "pair_id": "pair03_1880_best_front",
        "archival_source": "1880.jpg",
        "modern_source": "from_front.jpg",
        "purpose": "A second archival plate with a plausibly compatible modern "
        "frontal viewpoint.",
    },
    {
        "pair_id": "pair04_barber_viewpoint_mismatch",
        "archival_source": "Barber.jpg",
        "modern_source": "from_front.jpg",
        "purpose": "Deliberately harder viewpoint/scene-geometry case, used as "
        "a negative-control-style pair.",
    },
]

COVERAGE_CAVEAT = (
    "ransac.inlier_hull_area_fraction_of_archival_inference is computed by the "
    "validated pipeline as the inlier convex-hull area divided by the FULL "
    "archival inference frame. An archival plate containing a lot of sky, "
    "garden or unrelated foreground therefore scores lower than a tightly "
    "framed plate for the same quality of registration. It is NOT comparable "
    "across differently framed archival images and must be read as secondary "
    "context only, never as a ranking statistic."
)

INTERPRETATION_GUIDANCE = (
    "Primary interpretation comes from RANSAC support, inlier ratio, geometric "
    "validity, spatial distribution and the alignment visualisations. Raw "
    "predicted-correspondence count and hull coverage are secondary contextual "
    "measurements. No aggregate score is computed, and the pair with the "
    "highest raw correspondence count is not thereby the best."
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_pair_dir(directory: Path) -> list[str]:
    """Return a list of problems; empty means the pair is runnable."""
    problems = []
    if not directory.is_dir():
        return [f"missing directory {directory}"]
    for role in ("archival", "modern"):
        candidates = sorted(p for p in directory.glob(f"{role}*") if p.is_file())
        if not candidates:
            problems.append(f"no '{role}*' file in {directory}")
        elif len(candidates) > 1:
            # loftr_baseline.resolve_input raises on ambiguity; catching it
            # here gives a clear message instead of a stack trace mid-run.
            problems.append(
                f"ambiguous '{role}*' in {directory}: "
                f"{[p.name for p in candidates]}"
            )
    return problems


def run_pair(script: Path, data_dir: Path, out_dir: Path) -> dict:
    """Invoke the unchanged baseline pipeline for one pair.

    A non-zero exit code is EXPECTED when a pair fails registration validation
    (loftr_baseline returns 1 for any non-success status). That is a result,
    not a driver error, so it is recorded rather than raised.
    """
    cmd = [
        sys.executable,
        str(script),
        "--data-dir",
        str(data_dir),
        "--output-dir",
        str(out_dir),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "wall_seconds": elapsed,
        "stdout_tail": proc.stdout.strip().splitlines()[-6:] if proc.stdout else [],
        "stderr_tail": proc.stderr.strip().splitlines()[-6:] if proc.stderr else [],
    }


def _dims(metrics: dict, which: str) -> str | None:
    g = (metrics.get("inference_images") or {}).get(which)
    if not g:
        return None
    return f"{g.get('resized_width')}x{g.get('resized_height')}"


def extract_row(pair_id: str, role: str, metrics: dict) -> dict:
    """Pull the comparison fields out of one metrics.json.

    Uses .get() throughout: a run that fails early legitimately lacks the
    homography / geometric_error blocks, and the comparison must still show it.
    """
    corr = metrics.get("correspondences", {})
    ransac = metrics.get("ransac", {})
    hom = metrics.get("homography", {})
    geo = metrics.get("geometric_error", {})
    photo = metrics.get("photometric_check", {})
    inl = (geo.get("over_ransac_inliers") or {}) if geo else {}
    allf = (geo.get("over_all_filtered") or {}) if geo else {}

    return {
        "pair_id": pair_id,
        "role": role,
        "predicted_correspondences": corr.get("total_predicted"),
        "filtered_correspondences": corr.get("filtered_count"),
        "ransac_inliers": ransac.get("inlier_count"),
        "inlier_ratio": ransac.get("inlier_ratio"),
        "hull_coverage": ransac.get("inlier_hull_area_fraction_of_archival_inference"),
        "status": metrics.get("status"),
        "failure_reason": metrics.get("failure_reason"),
        "checks_failed": [
            c["name"] for c in metrics.get("checks", []) if not c.get("passed")
        ],
        "condition_number": hom.get("condition_number"),
        "warped_quad_is_convex": hom.get("warped_quad_is_convex"),
        "corner_w_all_same_sign": hom.get("corner_w_all_same_sign"),
        "warped_quad_area_ratio": hom.get("warped_quad_area_ratio_vs_modern"),
        "overlap_fraction": photo.get("overlap_fraction_of_modern"),
        "pearson_ncc": photo.get("pearson_ncc"),
        "reproj_inliers_rmse_px": inl.get("rmse_px"),
        "reproj_inliers_median_px": inl.get("median_px"),
        "reproj_all_filtered_rmse_px": allf.get("rmse_px"),
        "inference_archival": _dims(metrics, "archival"),
        "inference_modern": _dims(metrics, "modern"),
        "runtime_seconds": (metrics.get("timings_seconds") or {}).get("total"),
    }


def fmt(value, spec: str = "") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "**NO**"
    if isinstance(value, float) and spec:
        return format(value, spec)
    return str(value)


def write_comparison_md(path: Path, payload: dict) -> None:
    rows = payload["rows"]
    lines: list[str] = []
    a = lines.append

    a("# LoFTR multi-pair viewpoint comparison")
    a("")
    a(f"Generated: {payload['generated_utc']}")
    a("")
    a(
        "Question under test: **does archival-modern pair / viewpoint selection "
        "materially improve the geometry produced by the same validated LoFTR + "
        "global homography pipeline?**"
    )
    a("")
    a(
        f"Pipeline: `{payload['pipeline']['script']}` "
        f"(sha256 `{payload['pipeline']['sha256'][:16]}...`) - "
        f"{payload['pipeline']['parameters_source']}"
    )
    a("")

    a("## Provenance")
    a("")
    a("| pair_id | archival source | modern source | purpose |")
    a("|---|---|---|---|")
    for p in payload["provenance"]:
        a(
            f"| `{p['pair_id']}` | `{p['archival_source']}` | "
            f"`{p['modern_source']}` | {p['purpose']} |"
        )
    a("")
    for note in payload.get("provenance_notes", []):
        a(f"> **Note.** {note}")
        a("")

    a("## Primary metrics")
    a("")
    a(
        "| pair | status | predicted | filtered | inliers | inlier ratio | "
        "cond(H) | quad convex | corner-w sane |"
    )
    a("|---|---|---:|---:|---:|---:|---:|---|---|")
    for r in rows:
        a(
            f"| `{r['pair_id']}` | {fmt(r['status'])} | "
            f"{fmt(r['predicted_correspondences'])} | "
            f"{fmt(r['filtered_correspondences'])} | "
            f"{fmt(r['ransac_inliers'])} | {fmt(r['inlier_ratio'], '.3f')} | "
            f"{fmt(r['condition_number'], '.3g')} | "
            f"{fmt(r['warped_quad_is_convex'])} | "
            f"{fmt(r['corner_w_all_same_sign'])} |"
        )
    a("")

    a("## Secondary / contextual metrics")
    a("")
    a(
        "| pair | hull coverage | overlap | NCC | reproj RMSE inliers | "
        "reproj RMSE all filtered | infer archival | infer modern | runtime s |"
    )
    a("|---|---:|---:|---:|---:|---:|---|---|---:|")
    for r in rows:
        a(
            f"| `{r['pair_id']}` | {fmt(r['hull_coverage'], '.4f')} | "
            f"{fmt(r['overlap_fraction'], '.3f')} | "
            f"{fmt(r['pearson_ncc'], '.3f')} | "
            f"{fmt(r['reproj_inliers_rmse_px'], '.3f')} | "
            f"{fmt(r['reproj_all_filtered_rmse_px'], '.1f')} | "
            f"{fmt(r['inference_archival'])} | {fmt(r['inference_modern'])} | "
            f"{fmt(r['runtime_seconds'], '.2f')} |"
        )
    a("")

    a("## Validation outcome")
    a("")
    a("| pair | status | failed checks |")
    a("|---|---|---|")
    for r in rows:
        failed = ", ".join(r["checks_failed"]) if r["checks_failed"] else "none"
        a(f"| `{r['pair_id']}` | {fmt(r['status'])} | {failed} |")
    a("")

    a("## How to read these numbers")
    a("")
    a(f"- {INTERPRETATION_GUIDANCE}")
    a(f"- **Hull coverage caveat.** {payload['coverage_caveat']}")
    a(
        "- Geometric registration is a prerequisite for change analysis. "
        "Nothing here is evidence of monument damage, deterioration or "
        "conservation change."
    )
    a("")

    a("## Experimental conclusion")
    a("")
    a("_Pending visual inspection of the per-pair alignment outputs._")
    a("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Run the validated LoFTR baseline across multiple "
        "archival-modern pairs and emit a cross-pair comparison."
    )
    parser.add_argument("--repo-root", default=str(repo_root))
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Only rebuild the comparison from existing metrics.json files.",
    )
    args = parser.parse_args()

    root = Path(args.repo_root)
    script = root / "src" / "registration" / "loftr_baseline.py"
    source_dir = root / "data" / "humayun"
    pairs_dir = source_dir / "pairs"
    out_root = root / "outputs" / "registration" / "loftr_pairs"
    baseline_metrics = (
        root / "outputs" / "registration" / "loftr_baseline" / "metrics.json"
    )

    if not script.is_file():
        print(f"FATAL: validated pipeline not found at {script}")
        return 2
    if not baseline_metrics.is_file():
        print(f"FATAL: baseline reference metrics not found at {baseline_metrics}")
        return 2

    out_root.mkdir(parents=True, exist_ok=True)

    # --- discover + validate ------------------------------------------------
    print("=== validating pair directories ===")
    runnable = []
    for spec in PAIRS:
        d = pairs_dir / spec["pair_id"]
        problems = validate_pair_dir(d)
        if problems:
            print(f"  SKIP {spec['pair_id']}: {'; '.join(problems)}")
        else:
            print(f"  OK   {spec['pair_id']}")
            runnable.append(spec)

    # --- run ----------------------------------------------------------------
    run_log = {}
    if not args.skip_run:
        print("\n=== running the unchanged LoFTR pipeline per pair ===")
        for spec in runnable:
            pid = spec["pair_id"]
            print(f"  -> {pid}")
            result = run_pair(script, pairs_dir / pid, out_root / pid)
            run_log[pid] = result
            for line in result["stdout_tail"]:
                print(f"       {line}")
            if result["returncode"] not in (0, 1):
                print(f"       UNEXPECTED exit {result['returncode']}")
                for line in result["stderr_tail"]:
                    print(f"       ! {line}")

    # --- collect ------------------------------------------------------------
    rows = [
        extract_row(
            "BASELINE (loftr_baseline)",
            "reference",
            json.loads(baseline_metrics.read_text(encoding="utf-8")),
        )
    ]
    for spec in runnable:
        mp = out_root / spec["pair_id"] / "metrics.json"
        if not mp.is_file():
            print(f"WARNING: no metrics.json for {spec['pair_id']}")
            continue
        rows.append(
            extract_row(
                spec["pair_id"],
                "experimental",
                json.loads(mp.read_text(encoding="utf-8")),
            )
        )

    # --- provenance, including duplicate-source detection --------------------
    provenance = []
    notes: list[str] = []
    seen: dict[str, str] = {}
    for spec in PAIRS:
        entry = dict(spec)
        for role in ("archival", "modern"):
            src = source_dir / spec[f"{role}_source"]
            if src.is_file():
                digest = sha256(src)
                entry[f"{role}_sha256"] = digest
                if digest in seen and seen[digest] != src.name:
                    notes.append(
                        f"`{src.name}` is byte-identical to `{seen[digest]}` "
                        "(sha256 match), so those runs share that image."
                    )
                seen.setdefault(digest, src.name)
        provenance.append(entry)

    # The validated baseline modern image participates in the duplicate check
    # too, since a new candidate may simply be a copy of it.
    for extra in ("archival.jpg", "modern.jpg"):
        p = source_dir / extra
        if p.is_file():
            d = sha256(p)
            if d in seen and seen[d] != p.name:
                notes.append(
                    f"`{seen[d]}` is byte-identical to the validated baseline "
                    f"`{extra}` (sha256 match)."
                )
            seen.setdefault(d, p.name)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "question": "Does archival-modern pair/viewpoint selection materially "
        "improve the geometry produced by the same validated LoFTR + global "
        "homography pipeline?",
        "pipeline": {
            "script": "src/registration/loftr_baseline.py",
            "sha256": sha256(script),
            "parameters_source": "all parameters other than --data-dir and "
            "--output-dir come from the validated script's own argparse "
            "defaults (invoked as a subprocess; nothing overridden)",
        },
        "baseline_reference": baseline_metrics.relative_to(root).as_posix(),
        "coverage_caveat": COVERAGE_CAVEAT,
        "interpretation_guidance": INTERPRETATION_GUIDANCE,
        "provenance": provenance,
        "provenance_notes": sorted(set(notes)),
        "rows": rows,
        "run_log": run_log,
    }

    (out_root / "comparison.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    write_comparison_md(out_root / "comparison.md", payload)

    print("\n=== summary ===")
    header = (
        f"{'pair':<34}{'status':<10}{'pred':>6}{'filt':>6}{'inl':>6}{'ratio':>8}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['pair_id']:<34}{fmt(r['status']):<10}"
            f"{fmt(r['predicted_correspondences']):>6}"
            f"{fmt(r['filtered_correspondences']):>6}"
            f"{fmt(r['ransac_inliers']):>6}"
            f"{fmt(r['inlier_ratio'], '.3f'):>8}"
        )
    print(f"\ncomparison: {out_root / 'comparison.json'}")
    print(f"comparison: {out_root / 'comparison.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
