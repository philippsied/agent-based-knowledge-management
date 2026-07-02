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
| plan-commands | plan | verified | spec-commands,test-design | yes | — |
| plan-lint | plan | verified | spec-lint,test-design | yes | — |
| plan-ingest | plan | verified | spec-ingest,test-design | yes | — |
| plan-setup | plan | verified | spec-setup,test-design | yes | — |
| plan-dragonscale | plan | verified | spec-dragonscale,test-design | yes | — |
| tasks-commands | task | todo | plan-commands | yes | — |
| tasks-lint | task | todo | plan-lint | yes | — |
| tasks-ingest | task | todo | plan-ingest | yes | — |
| tasks-setup | task | todo | plan-setup | yes | — |
| tasks-dragonscale | task | todo | plan-dragonscale,tasks-lint,tasks-ingest | no | — |
| adr-0003 | adr | verified | prd | yes | — |

## Ready now
- tasks-commands -> docs/tasks/cmd-script-consolidation-commands.md
- tasks-lint -> docs/tasks/cmd-script-consolidation-lint.md
- tasks-ingest -> docs/tasks/cmd-script-consolidation-ingest.md
- tasks-setup -> docs/tasks/cmd-script-consolidation-setup.md

