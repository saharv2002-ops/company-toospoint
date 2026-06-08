# ToosPoint — Company Assets

Everything that belongs to ToosPoint itself, not to any one client.

| Folder | Purpose |
|---|---|
| [`brand/`](./brand) | Logos and brand assets (PNG, SVG, etc.) |
| [`templates/`](./templates) | Master LaTeX class files for contracts, proposals, and invoices |
| [`legal/`](./legal) | Master legal documents — blank NDAs, MSAs, contractor agreements |
| [`operations/`](./operations) | Internal SOPs, playbooks, runbooks |

## Brand

- `toospoint-logo.png` — primary logo (with white background)
- `toospoint-logo-clean.png` — clean variant (transparent / cleaner edge)

## Templates

Three LaTeX classes drive all client documents:

| Template | File | Used by |
|---|---|---|
| Contracts (NDA, consulting agreement) | `templates/contract/toospoint.cls` | Per-client `contracts/` folders |
| Consulting proposals | `templates/proposal/proposal.cls` | Per-client `proposals/` folders |
| Invoices | `templates/invoice/toospoint-invoice.cls` | Per-client `invoices/` folders |

When you produce a new client document, **copy the relevant `.cls` into
the client's folder** alongside the new `.tex` so the document stays
reproducible even if this master version changes later. Edit the
client-name string in the `.cls` header for the per-client copy.
