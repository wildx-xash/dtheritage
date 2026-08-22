# Verification Bundle

This directory is the tracked, compact review bundle. It is authoritative for
reported Person 2/3 verification results when `outputs/` is absent.

- `humayun/`: best-pair registration metrics, bounded trust summary, candidate
  evidence, and one candidate overlay.
- `sanchi/`: successful gateway registration metrics, trust summary, candidate
  evidence with provenance, and one candidate overlay.
- `qutb/`: full-height/detail failure metrics, the zero-candidate hard-case
  export, and an invalid-geometry overlay.
- `three_monument/`: cross-monument audit and integration-oriented summary.

Bulk images and every intermediate remain reproducible under `outputs/` using:

```bash
python src/registration/run_pipeline.py --monument all
```

`Data.zip` is the original supplied archive. Runtime experiments use the
tracked pair directories under `data/`; the raw extraction remains in
`data/source_data/Data/` for provenance verification.
