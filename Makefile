# agentic-knowledge-management Makefile
# Test runner entry points for DragonScale, lint tooling, and the vault-root resolver.

.PHONY: test test-address test-tiling test-boundary test-vault-root test-terminology test-title-overlap setup-dragonscale clean-test-state help

help:
	@echo "agentic-knowledge-management developer targets:"
	@echo "  make test                  Run all tests"
	@echo "  make test-vault-root       lib/vault_root.{py,sh} resolver tests"
	@echo "  make test-address          scripts/allocate-address.sh tests (shell)"
	@echo "  make test-tiling           scripts/tiling-check.py tests (python, no ollama required)"
	@echo "  make test-boundary         scripts/boundary-score.py tests (python, no prereqs)"
	@echo "  make test-terminology      scripts/lint-terminology.py tests"
	@echo "  make test-title-overlap    scripts/lint-title-overlap.py tests"
	@echo "  make setup-dragonscale     Run bin/setup-dragonscale.sh against this vault"
	@echo "  make clean-test-state      Remove runtime lockfiles and tiling cache"

test: test-vault-root test-address test-tiling test-boundary test-terminology test-title-overlap
	@echo ""
	@echo "All tests passed."

test-vault-root:
	@echo "=== test_vault_root.py ==="
	@python3 tests/test_vault_root.py
	@echo "=== test_vault_root.sh ==="
	@bash tests/test_vault_root.sh

test-address:
	@echo "=== test_allocate_address.sh ==="
	@bash tests/test_allocate_address.sh

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

setup-dragonscale:
	@bash bin/setup-dragonscale.sh

clean-test-state:
	@rm -f .vault-meta/.address.lock .vault-meta/.tiling.lock .vault-meta/tiling-cache.json .vault-meta/tiling-cache.*.tmp
	@echo "Runtime lockfiles and tiling cache removed."
