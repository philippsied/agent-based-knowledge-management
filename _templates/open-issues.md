---
type: meta
title: "Open Issues"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - meta
  - issues
  - tracking
status: developing
---

# Open Issues

Known issues across the vault, tooling, and plugin layer. Each entry: **WHAT** — WHY. WHERE.

Resolved issues stay in [[log]]; this page is for what is *still* broken or deferred.

LIFO stack: `/wiki:handoff` pushes new bullets to the top of their category. `/wiki:fix-issues` pops from the top, verifies the issue still exists, and either deletes it (already resolved) or fixes-then-deletes it. Exactly one issue per `/wiki:fix-issues` invocation.

## Hook / enforcement layer

<!-- Issues touching .claude/hooks/*.sh, plugin hooks, or enforcement gaps. -->

## Lint

<!-- Issues with scripts/lint/, run-lint.sh, missing checks, false positives. -->

## Vault state

<!-- Stale pages, broken wikilinks, duplicate concepts, content drift. -->

## Tooling gaps

<!-- Missing automation, scripts that should exist, manual workarounds. -->

## Memory / cross-session

<!-- hot.md / index.md / log.md drift, coordinator-vs-sub-agent confusion. -->
