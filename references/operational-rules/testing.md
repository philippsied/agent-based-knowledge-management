---
paths:
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/__tests__/**"
---

# Testing Standards

- Every new function or endpoint gets at least one test
- Test the behavior, not the implementation
- Name tests descriptively: "returns 401 when token is expired",
  not "test auth"
- Include at least one edge case per test file
- Do not mock what you can test directly
- Run the test suite after writing tests to confirm they pass
