# agentic-knowledge-management Makefile
# Test runner entry points for DragonScale, lint tooling, and the vault-root resolver.

.PHONY: test test-address test-tiling test-boundary test-vault-root test-terminology test-title-overlap test-lint-orphans test-run-lint test-sync-versions test-wiki-path-safety lint sync-versions release setup-dragonscale clean clean-test-state help

help:
	@echo "agentic-knowledge-management developer targets:"
	@echo "  make test                  Run all tests"
	@echo "  make lint                  Run the canonical wiki-quality lint aggregator"
	@echo "  make sync-versions         Mirror plugin.json version into marketplace.json"
	@echo "  make release VERSION=X.Y.Z Prepare a new release (test + lint + bump + commit + tag)"
	@echo "  make test-vault-root       lib/vault_root.py resolver tests"
	@echo "  make test-address          scripts/allocate-address.py tests (python)"
	@echo "  make test-tiling           scripts/tiling-check.py tests (python, no ollama required)"
	@echo "  make test-boundary         scripts/boundary-score.py tests (python, no prereqs)"
	@echo "  make test-terminology      scripts/lint-terminology.py tests"
	@echo "  make test-title-overlap    scripts/lint-title-overlap.py tests"
	@echo "  make test-lint-orphans     scripts/lint-orphans.py tests"
	@echo "  make test-run-lint         scripts/run-lint.py aggregator tests (python)"
	@echo "  make test-sync-versions    bin/sync-versions.py tests"
	@echo "  make setup-dragonscale     Run bin/setup-dragonscale.py against this vault"
	@echo "  make clean                 Remove local Python caches and .DS_Store"
	@echo "  make clean-test-state      Remove runtime lockfiles and tiling cache"

test: test-vault-root test-address test-tiling test-boundary test-terminology test-title-overlap test-lint-orphans test-run-lint test-sync-versions test-wiki-path-safety
	@echo ""
	@echo "All tests passed."

lint:
	@python3 scripts/run-lint.py

test-vault-root:
	@echo "=== test_vault_root.py ==="
	@python3 tests/test_vault_root.py

test-address:
	@echo "=== test_allocate_address.py ==="
	@python3 tests/test_allocate_address.py

test-tiling:
	@echo "=== test_tiling_check.py ==="
	@python3 tests/test_tiling_check.py

test-boundary:
	@echo "=== test_boundary_score.py ==="
	@python3 tests/test_boundary_score.py

test-terminology:
	@echo "=== test_lint_terminology.py ==="
	@python3 tests/test_lint_terminology.py

test-title-overlap:
	@echo "=== test_lint_title_overlap.py ==="
	@python3 tests/test_lint_title_overlap.py

test-lint-orphans:
	@echo "=== test_lint_orphans.py ==="
	@python3 tests/test_lint_orphans.py

test-run-lint:
	@echo "=== test_run_lint.py ==="
	@python3 tests/test_run_lint.py

test-sync-versions:
	@echo "=== test_sync_versions.py ==="
	@python3 tests/test_sync_versions.py

test-wiki-path-safety:
	@echo "=== test_wiki_path_safety.py ==="
	@python3 tests/test_wiki_path_safety.py

sync-versions:
	@python3 bin/sync-versions.py

release:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release VERSION=X.Y.Z"; exit 2; fi
	@python3 bin/release.py $(VERSION)

setup-dragonscale:
	@python3 bin/setup-dragonscale.py

clean:
	@rm -rf lib/__pycache__ scripts/__pycache__ */__pycache__ .DS_Store
	@echo "Cleaned local caches."

clean-test-state:
	@rm -f .vault-meta/.address.lock .vault-meta/.tiling.lock .vault-meta/tiling-cache.json .vault-meta/tiling-cache.*.tmp
	@echo "Runtime lockfiles and tiling cache removed."
