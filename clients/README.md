# Clients

One folder per active consulting client. Each client folder follows the
same shape so anything you need is in a predictable place.

## Active clients

| Client | Engagement | Status |
|---|---|---|
| [iCall International](./icall-international) | Hourly ($95 USD / hr, Net 15) | Contracted |
| [Language Group Provider LLC](./language-group-provider) | Proposed: $5,000 USD / mo, 40 hrs / mo, Net 15 | Proposal drafted (2026-06-08) |
| [Lingotec](./lingotec) | Director of Partnerships — $7,000 / month | Active since 2026-04-15 |
| [One World Global](./one-world-global) | Proposed: $6,000 USD / mo, 25–30 hrs / wk, Net 15 | Proposal delivered |
| [Simplified Group BPO](./simplified-group) | $4,000 USD / mo retainer + 10% commission on net new revenue, 40+ hrs / mo, Net 15 | Contracted, active |

## Standard client folder layout

```
<client-name>/
├── README.md             # Engagement terms, contacts, status, links
├── contracts/            # NDA + consulting agreement (.tex + .pdf) + cls snapshot
├── proposals/            # Consulting proposals (.tex + .pdf) + cls snapshot
├── invoices/             # YYYY-MM-DD_<CCY><AMOUNT>_<TERMS>.{tex,pdf}
├── sales-deck/           # If we built a deck for them (pptx, html, slides_png)
├── work-log/             # activity.md — running log of work done
└── deliverables/         # Final reports, analyses, frameworks handed to client
```

Not every client has every folder. Create folders as the engagement
produces artefacts; don't pre-create empty ones.
