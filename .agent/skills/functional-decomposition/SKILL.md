---
name: functional-decomposition
description: Break down complex functions into smaller, pure functions using AST analysis.
---

# Functional Decomposition

## The Problem

Large functions with high Cyclomatic Complexity (many nested `if/else`, loops, or mixed responsibilities) are hard to test and maintain.

## The Process

When you identify a function that is too complex (e.g., handles validation, database operations, notifications, and logic all in one):

1. **Analyze**: Understand the function's flow, inputs, outputs, and side effects.
2. **Decompose**: Propose a chain of **Pure Functions** that handle specific responsibilities.
    * Examples: `validate_lift_specs()`, `calculate_ranking_delta()`, `persist_to_leaderboard()`.
3. **Refactor**: Create a "Foundational Engineer" solution.
    * The original function becomes a high-level orchestrator calling the new pure functions.
    * The new functions should be small, focused, and testable.

## The Foundational Engineer Twist (AST)

**CRITICAL:** You must ensure that the logic remains *identical* during refactoring.

* Mentally (or using tools if available) map the **Abstract Syntax Tree (AST)** of the original code to the new code.
* Ensure that every branch and condition in the original AST has an equivalent path in the refactored code.
* If you move logic, verify that variable scope and data flow are preserved.

## Example

**Before:**

```python
def process_data(data):
    if not data.valid:
        return error
    if data.type == 'A':
        # ... complex logic ...
        db.save(result)
    else:
        # ... other logic ...
        db.save(other_result)
```

**After:**

```python
def validate_data(data):
    return data.valid

def calculate_result(data):
    if data.type == 'A':
        return complex_logic(data)
    return other_logic(data)

def process_data(data):
    if not validate_data(data):
        return error
    result = calculate_result(data)
    db.save(result)
```
