"""Reproducible Person 2/3 runner for the three-monument portfolio."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(root: Path, *parts: str, allowed: set[int] = {0}) -> None:
    command = [sys.executable, *parts]
    result = subprocess.run(command, cwd=root, env=os.environ.copy())
    if result.returncode not in allowed:
        raise SystemExit(result.returncode)


def registration(root: Path, monument: str, pair: str) -> None:
    run(
        root,
        "src/registration/loftr_baseline.py",
        "--data-dir", f"data/{monument}/pairs/{pair}",
        "--output-dir", f"outputs/registration/{monument}/loftr_pairs/{pair}",
        allowed={0, 1},  # Non-zero means the measured pair failed a validity gate.
    )


def humayun(root: Path) -> None:
    run(root, "src/registration/loftr_baseline.py")
    run(root, "src/registration/loftr_pairs.py")
    run(root, "src/registration/trust_region_analysis.py")
    run(root, "src/registration/change_evidence_humayun.py")
    run(root, "src/registration/person2_3_final_audit.py")


def sanchi(root: Path) -> None:
    for pair in ("gateway_front_1863_2015", "stupa_front_1880_2015", "stupa_front_1880_2013"):
        registration(root, "sanchi", pair)
    run(root, "src/registration/trust_region_analysis.py", "--data-dir", "data/sanchi/pairs/gateway_front_1863_2015", "--output-dir", "outputs/registration/sanchi/trust_region_gateway_1863_2015", "--pair-metrics", "outputs/registration/sanchi/loftr_pairs/gateway_front_1863_2015/metrics.json", "--pair-id", "gateway_front_1863_2015", "--regions-json", "data/sanchi/gateway_trust_regions.json")
    run(root, "src/registration/change_evidence_humayun.py", "--trust-dir", "outputs/registration/sanchi/trust_region_gateway_1863_2015", "--output-dir", "outputs/change_evidence/sanchi", "--monument", "Sanchi Stupa / Eastern Torana", "--monument-id", "sanchi", "--candidate-prefix", "SANCHI_CE", "--method-version", "change_evidence_sanchi_v1", "--foreground-region", "", "--provenance-json", "data/sanchi/gateway_provenance.json", "--base-uncertainty", "archival_photographic_print_and_photometric_variation", "--base-uncertainty", "residual_viewpoint_and_scale_difference")


def qutb(root: Path) -> None:
    for pair in ("tower_full_1858_2008", "tower_detail_1860_2015", "tower_full_1858_2017_negative"):
        registration(root, "qutb", pair)
    run(root, "src/registration/three_monument_audit.py", "--qutb-only")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reproducible Person 2/3 monument workflows.")
    parser.add_argument("--monument", choices=("humayun", "sanchi", "qutb", "audit", "all"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("TORCH_HOME", str(root / ".torch-cache"))
    actions = {"humayun": humayun, "sanchi": sanchi, "qutb": qutb}
    if args.monument == "audit":
        run(root, "src/registration/three_monument_audit.py")
    elif args.monument == "all":
        for action in (humayun, sanchi, qutb):
            action(root)
        run(root, "src/registration/three_monument_audit.py")
    else:
        actions[args.monument](root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
