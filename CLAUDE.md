# Working conventions

## Git

- **Always commit changes when a task is complete.** Do not wait for an explicit "please commit" from the user — treat committing as part of finishing the work.
- **The commit message must summarize what was actually done.** Not "update" or "add files" — spell out the scope: which files/folders were created or changed, what they contain, and any counts (e.g. "45 emails across 15 folders"). A reader scanning `git log` should understand the change without opening the diff.
- Include a short "why" line when the change reflects a decision (fact-check pass, brand tweak, requested redesign) — not required for pure additions.
- Group related edits into a single commit; separate unrelated work into separate commits.
