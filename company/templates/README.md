# Document Templates

Canonical LaTeX class files driving every client document ToosPoint
produces. **Never edit a client's document by hacking the master here**
— each client folder keeps its own snapshot of the relevant `.cls`
alongside the `.tex`, so per-client customisations (e.g. the client name
in the header) live with the document, not the master.

| Template | Header style | Typical use |
|---|---|---|
| [`contract/toospoint.cls`](./contract/toospoint.cls) | "ToosPoint Consulting × `<Client>`" header bar | NDAs, consulting agreements, MSAs |
| [`proposal/proposal.cls`](./proposal/proposal.cls) | Coloured banner with "Prepared for `<Client>`" | Consulting proposals |
| [`invoice/toospoint-invoice.cls`](./invoice/toospoint-invoice.cls) | Minimal modern invoice layout | Monthly invoices |

## How to start a new client document

1. Copy the relevant `.cls` from here into the client's
   `contracts/` (or `proposals/`, `invoices/`) folder.
2. Edit the client-name string in the `.cls` header so the running
   header is correct for that client.
3. Write the document `.tex` next to the snapshot `.cls`.
4. Compile with `xelatex` (proposal class requires `fontspec`; the
   others use either `pdflatex` or `xelatex` depending on the source —
   check the comment block at the top of the `.tex`).

## When to update a master

Only when you want the change to apply to **every future client
document**. Per-client tweaks belong in the client's snapshot.
