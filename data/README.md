# Dataset Contract

## Canonical Runtime Inputs

Registration code reads only the tracked, normalized pair folders:

- `data/humayun/pairs/`
- `data/sanchi/pairs/`
- `data/qutb/pairs/`

Each runnable pair contains exactly `archival.jpg` and `modern.jpg`. These are
the canonical runtime inputs for Person 2/3 experiments.

## Original Delivery and Provenance

- `../Data.zip` is the original teammate-delivered archive. Retain it; do not
  use it directly at runtime.
- `source_data/Data/` is a lossless extraction of that archive used for source
  and provenance checks. Its filenames are normalized only where necessary to
  correct an accidental embedded space.
- `source_data/Data/manifest.csv` is UTF-8 and is the source provenance index.
  It records original filename, monument, date, author, source, URL, licence,
  viewpoint, and notes.

The Sanchi gateway archival image is rotated by 90 degrees only in its runtime
pair copy for correct viewing orientation. The source extraction is otherwise
preserved unchanged; the preprocessing is recorded in
`sanchi/gateway_provenance.json`.
