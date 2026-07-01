# Work Manifest — Commands->Skills-Integration + Skript-Konsolidierung

slug `cmd-script-consolidation` · created 2026-07-01 · _generated, edit the .json_

| id | type | status | deps | parallel | session |
|----|------|--------|------|----------|---------|
| prd | prd | verified | — | yes | — |
| adr-0001 | adr | verified | prd | yes | — |
| adr-0002 | adr | verified | prd | yes | — |
| test-design | test-design | verified | prd | yes | — |
| spec-commands | spec | verified | prd,adr-0001 | yes | — |
| spec-lint | spec | verified | prd,adr-0002 | yes | — |
| spec-dragonscale | spec | verified | prd,adr-0002 | yes | — |
| spec-ingest | spec | verified | prd,adr-0002 | yes | — |
| spec-setup | spec | verified | prd,adr-0002 | yes | — |
| plan-commands | plan | todo | spec-commands,test-design | yes | — |
| plan-lint | plan | todo | spec-lint,test-design | yes | — |
| plan-ingest | plan | todo | spec-ingest,test-design | yes | — |
| plan-setup | plan | todo | spec-setup,test-design | yes | — |
| plan-dragonscale | plan | todo | spec-dragonscale,test-design | yes | — |
| tasks-commands | task | todo | plan-commands | yes | — |
| tasks-lint | task | todo | plan-lint | yes | — |
| tasks-ingest | task | todo | plan-ingest | yes | — |
| tasks-setup | task | todo | plan-setup | yes | — |
| tasks-dragonscale | task | todo | plan-dragonscale,tasks-lint,tasks-ingest | no | — |
| adr-0003 | adr | verified | prd | yes | — |

## Ready now
- plan-commands -> docs/plans/PLAN-cmd-script-consolidation-commands.md
- plan-lint -> docs/plans/PLAN-cmd-script-consolidation-lint.md
- plan-ingest -> docs/plans/PLAN-cmd-script-consolidation-ingest.md
- plan-setup -> docs/plans/PLAN-cmd-script-consolidation-setup.md
- plan-dragonscale -> docs/plans/PLAN-cmd-script-consolidation-dragonscale.md

