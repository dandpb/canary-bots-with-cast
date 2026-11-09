# Integration update after upstream merges — 2026-11-05

Upstream `main` reached `2a66d4de9`, integrating #16, #20 and #17. The remaining
branches were updated without rebasing, force-pushing, resetting the checkout or
changing the original stash.

| PR | Head after integration | Base |
|---|---|---|
| #18 | `418e0727f` | main |
| #19 | `f579249cc` | fix/11-complete-bot-checkpoints |
| #15 | `863572165` | main |
| #21 | `1f962e77c` | feat/lifetime-replay-benchmark |

The only manual conflict was the player-unit CMake registration in #18. The
resolved list preserves protocol, save queue, scoped database and cast publisher
tests. The result was propagated through #19 and the integration branch.

The complete integration trees before/after those merges (`5aac5a834` and
`6777cb780`) are identical:

```text
c954c4e56c36f9e7b659d751a3ab6af9654b3bb8
```

Thus the upstream composition changed ancestry, not the validated integration's
native or Python behavior. `git diff --check` passed. The existing integrated
unit-test binary was rerun without filtering in a network-disabled container with
the checkout mounted readonly: **155/155 native tests passed**. This is explicitly
a rerun of the previously compiled binary, not an unperformed new build. Earlier
matching Release builds, four CTests, Lua and live lifecycle regressions remain
documented in [lifecycle acceptance](LIFECYCLE_ACCEPTANCE.md).

The latest Python implementation passed **98 tests**, Ruff and strict mypy in
18 modules. New evidence covers [video export isolation/recovery](../../deployment/brain/evidence/2026-11-05/video-review-followup.md),
elapsed-clock metric correctness and [native scenario qualification](../../deployment/brain/evidence/2026-11-05/scenario-qualification.md).
Video follow-up's earlier 95-test count predates the three elapsed-clock regressions.

Both new native qualification campaigns completed with no inference or AI charges;
their Compose containers were removed. Lifecycle QA services remain stopped with
evidence retained. No production deployment or branch merge to `main` was performed
by this execution. Paid M5 and human gameplay acceptance remain separate gates.
