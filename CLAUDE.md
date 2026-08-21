# Working conventions

## Multi-session projects

- **Every multi-session project has a `CONTINUATION.md` at its root** (e.g. `prototypes/<name>/CONTINUATION.md`, `clients/<name>/CONTINUATION.md`). Its purpose is to make the next session (or a fresh Claude after `/clear`) resumable without re-deriving context.
- Structure: quick orient (branch, dirs, purpose), "Where we are right now", Done list, Immediate next actions, Locked decisions, Open questions, How-to-resume, dated session log.
- **Update it at the end of every working session** — move finished items to Done, refresh next actions, note new decisions. If you edit code during a session and forget to update `CONTINUATION.md`, the session isn't finished.
- Never treat `CONTINUATION.md` as append-only. It's a living state file — prune stale entries, keep it under ~150 lines.

## Git

- **Always commit changes when a task is complete.** Do not wait for an explicit "please commit" from the user — treat committing as part of finishing the work.
- **The commit message must summarize what was actually done.** Not "update" or "add files" — spell out the scope: which files/folders were created or changed, what they contain, and any counts (e.g. "45 emails across 15 folders"). A reader scanning `git log` should understand the change without opening the diff.
- Include a short "why" line when the change reflects a decision (fact-check pass, brand tweak, requested redesign) — not required for pure additions.
- Group related edits into a single commit; separate unrelated work into separate commits.
