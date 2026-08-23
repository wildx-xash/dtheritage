"""Load tracked DTHeritage provenance and verification artifacts into Supabase.

Run locally from the repository root:
    python scripts/seed_supabase.py

The script uses SUPABASE_SERVICE_ROLE_KEY from .env.local.  Never commit that
file or use this key in the frontend.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    path = ROOT / ".env.local"
    if not path.exists():
        raise RuntimeError("Missing .env.local in the repository root.")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise RuntimeError(f"Missing values in .env.local: {', '.join(missing)}")
    return values


def api(env: dict[str, str], method: str, table: str, payload: object | None = None, query: dict[str, str] | None = None) -> object:
    url = env["SUPABASE_URL"].rstrip("/") + "/rest/v1/" + table
    if query:
        url += "?" + urlencode(query, safe=".,()")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if method == "POST":
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"Supabase {method} {table} failed: {detail}") from error


def monument_id(name: str) -> str | None:
    lowered = name.lower()
    if "humayun" in lowered:
        return "humayun"
    if "sanchi" in lowered:
        return "sanchi"
    if "qutb" in lowered or "qutub" in lowered:
        return "qutb"
    return None


def seed_images(env: dict[str, str]) -> int:
    manifest = ROOT / "data/source_data/Data/manifest.csv"
    count = 0
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            identifier = monument_id(row.get("monument", ""))
            filename = (row.get("filename") or "").strip()
            if not identifier or not filename:
                continue
            record = {
                "monument_id": identifier,
                "image_key": filename,
                "era": "Archival" if "h" in filename.lower().split("_")[-2:-1] else "Reference image",
                "year_date": row.get("year_date"),
                "author": row.get("photographer"),
                "source": row.get("archive_source"),
                "source_url": row.get("source_url"),
                "license": row.get("license"),
                "viewpoint": row.get("viewpoint"),
                "notes": row.get("notes"),
                "storage_path": None,
            }
            api(env, "POST", "images", [record], {"on_conflict": "image_key"})
            count += 1
    return count


def registration_record(monument: str, metrics: dict) -> dict:
    corr = metrics.get("correspondences", {})
    ransac = metrics.get("ransac", {})
    homography = metrics.get("homography", {})
    reprojection = (metrics.get("geometric_error", {}) or {}).get("over_ransac_inliers", {})
    return {
        "monument_id": monument,
        "pair_name": metrics.get("pair_id") or metrics.get("experiment") or f"{monument}_verified_pair",
        "status": metrics.get("status", "unknown"),
        "decision": metrics.get("decision") or metrics.get("technical_conclusion"),
        "predicted_correspondences": corr.get("total_predicted"),
        "filtered_correspondences": corr.get("filtered_count"),
        "ransac_inliers": ransac.get("inlier_count"),
        "inlier_ratio": ransac.get("inlier_ratio"),
        "hull_coverage": ransac.get("inlier_hull_area_fraction_of_archival_inference"),
        "reprojection_rmse_px": reprojection.get("rmse_px"),
        "condition_number": homography.get("condition_number"),
        "failure_reason": metrics.get("failure_reason"),
        "metrics": metrics,
    }


def get_or_create_registration(env: dict[str, str], record: dict) -> str:
    rows = api(env, "GET", "registrations", query={
        "monument_id": f"eq.{record['monument_id']}",
        "pair_name": f"eq.{record['pair_name']}",
        "select": "id",
    })
    if rows:
        registration_id = rows[0]["id"]
        api(env, "PATCH", "registrations", record, {"id": f"eq.{registration_id}"})
        return registration_id
    created = api(env, "POST", "registrations", [record])
    return created[0]["id"]


def seed_verification(env: dict[str, str], monument: str, metric_file: str) -> int:
    base = ROOT / "artifacts/verification" / monument
    metrics = json.loads((base / metric_file).read_text(encoding="utf-8"))
    registration_id = get_or_create_registration(env, registration_record(monument, metrics))
    evidence = json.loads((base / "candidate_evidence.json").read_text(encoding="utf-8"))
    candidates = []
    for candidate in evidence.get("candidates", []):
        candidates.append({
            "candidate_id": candidate["candidate_id"],
            "monument_id": monument,
            "registration_id": registration_id,
            "registration_region": candidate.get("registration_region"),
            "registration_trust": candidate.get("registration_trust"),
            "bbox_xywh": candidate.get("bbox_xywh_in_inference_image"),
            "change_type": candidate.get("change_type"),
            "evidence_strength": candidate.get("evidence_strength"),
            "review_status": candidate.get("review_status", "PENDING_REVIEW"),
            "signals": candidate.get("signals"),
            "registration_support": candidate.get("registration_support"),
            "uncertainty_indicators": candidate.get("uncertainty_indicators"),
            "provenance": candidate.get("provenance"),
        })
    if candidates:
        api(env, "POST", "evidence_candidates", candidates, {"on_conflict": "candidate_id"})
    return len(candidates)


def main() -> int:
    env = read_env()
    image_count = seed_images(env)
    evidence_count = sum((
        seed_verification(env, "humayun", "registration_metrics_pair02.json"),
        seed_verification(env, "sanchi", "registration_metrics_gateway.json"),
        seed_verification(env, "qutb", "registration_metrics_full_height.json"),
    ))
    print(f"Imported {image_count} image records and {evidence_count} candidate-evidence records.")
    print("Expected result: 19 candidates (8 Humayun, 11 Sanchi, 0 Qutb).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
