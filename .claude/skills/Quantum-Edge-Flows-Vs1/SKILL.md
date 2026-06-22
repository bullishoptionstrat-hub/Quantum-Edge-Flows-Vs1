```markdown
# Quantum-Edge-Flows-Vs1 Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill provides guidance on the development patterns, coding conventions, and workflows used in the `Quantum-Edge-Flows-Vs1` TypeScript repository. It covers file naming, import/export styles, testing patterns, and suggested commands for common workflows. This resource is intended to help contributors maintain consistency and efficiency when working with the codebase.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `quantumEdgeFlow.ts`, `edgeNodeManager.ts`

### Imports
- Use **relative import paths** for internal modules.
  - Example:
    ```typescript
    import { computeFlow } from './computeFlow';
    ```

### Exports
- Use **named exports** rather than default exports.
  - Example:
    ```typescript
    // In edgeNodeManager.ts
    export function createEdgeNode() { ... }
    export const EDGE_NODE_LIMIT = 10;
    ```

### Commit Messages
- Commit messages are **freeform** (no strict prefix), with an average length of 62 characters.
  - Example:  
    ```
    Add initial implementation of quantum edge flow calculation
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to introduce a new feature or utility.
**Command:** `/add-module`

1. Create a new `.ts` file using camelCase naming.
2. Implement your logic using named exports.
3. Use relative imports to include dependencies.
4. Write corresponding tests in a `.test.ts` file.
5. Commit with a clear, descriptive message.

### Running Tests
**Trigger:** When you want to verify code correctness.
**Command:** `/run-tests`

1. Identify test files matching the `*.test.*` pattern.
2. Use the project's test runner (framework is unknown; check documentation or scripts).
3. Run all tests and review the output.
4. Fix any failing tests before merging code.

### Refactoring Code
**Trigger:** When improving or restructuring existing code.
**Command:** `/refactor`

1. Locate the relevant files using camelCase naming.
2. Update imports and exports to maintain named export style.
3. Ensure all relative paths remain valid.
4. Update or add tests as needed.
5. Commit changes with a descriptive message.

## Testing Patterns

- Test files use the `*.test.*` pattern (e.g., `computeFlow.test.ts`).
- The testing framework is **unknown**; check for documentation or scripts in the repository.
- Place tests alongside or near the modules they test.
- Example test file:
  ```typescript
  // computeFlow.test.ts
  import { computeFlow } from './computeFlow';

  describe('computeFlow', () => {
    it('should calculate correct flow value', () => {
      expect(computeFlow(2, 3)).toBe(6);
    });
  });
  ```

## Commands
| Command       | Purpose                                      |
|---------------|----------------------------------------------|
| /add-module   | Scaffold and add a new module                |
| /run-tests    | Run all test files in the repository         |
| /refactor     | Refactor code while maintaining conventions  |
```
