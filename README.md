# ToosPoint — Company Repository

Everything ToosPoint needs to run the consulting practice, **except the
public website** (which lives in `~/toospoint`).

## Layout

| Folder | What lives here |
|---|---|
| [`company/`](./company) | ToosPoint's own assets — brand, document templates, master legal docs, internal SOPs |
| [`clients/`](./clients) | One folder per active consulting client. Contracts, proposals, invoices, work logs, deliverables |
| [`prospects/`](./prospects) | Active leads that haven't signed yet — moves into `clients/` once a contract exists |
| [`research/`](./research) | Standalone analyses, market research, data work that isn't tied to a single client |
| [`tools/`](./tools) | Internal tools and small apps (RFP search, etc.) |
| [`inbox/`](./inbox) | Unclassified files waiting to be sorted — empty this regularly |

## Conventions

- **Folder names are kebab-case** (`one-world-global`, not `One World Global`).
- **Client folders use the company's full legal name**, kebab-cased.
- **Invoice files use `YYYY-MM-DD_<CCY><AMOUNT>_<TERMS>.{tex,pdf}`** so they
  sort chronologically and the metadata is in the filename.
- **LaTeX class files are kept in two places**: the canonical version sits
  in [`company/templates/`](./company/templates); per-document snapshots
  live alongside each `.tex` so individual documents stay reproducible
  even if the master changes.
- **Build artefacts** (`.aux`, `.log`, `.out`, `.DS_Store`) are not
  committed and should not be checked into git.

## Adding a new client

1. Copy the structure of an existing client folder (e.g. `clients/lingotec/`).
2. Rename the folder to the client's legal name (kebab-cased).
3. Drop in a `README.md` with engagement terms (see existing clients for
   the template) and a `work-log/activity.md`.
4. Pull the right `.cls` template from `company/templates/` for any new
   contract, proposal, or invoice.

## Adding a new prospect

Same shape as a client folder, but put it under `prospects/`. Move it to
`clients/` the day the contract is signed.
