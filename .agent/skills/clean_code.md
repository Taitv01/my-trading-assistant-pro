---
name: clean-code
description: Enforce Clean Code principles and Python best practices
---

# Clean Code Guidelines for Python

## 1. Naming Conventions

- **Variables/Functions**: Use `snake_case` (e.g., `calculate_rsi`, `user_data`).
- **Classes**: Use `PascalCase` (e.g., `DataFetcher`, `MarketScanner`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `API_DELAY`).

## 2. Functions

- **Single Responsibility**: Each function should do one thing only.
- **Length**: Keep functions short (< 50 lines ideal).
- **Arguments**: Limit arguments to 3-4 max. Use data classes or dictionaries for more.
- **Type Hinting**: ALWAYS use type hints (e.g., `def fetch_data(symbol: str) -> pd.DataFrame:`).

## 3. Code Structure

- **Imports**: Group imports: Standard lib -> Third party -> Local application.
- **Docstrings**: Add docstrings to all modules, classes, and public functions using Google or NumPy style.
- **Comments**: Explain "Why", not "What". Code should be self-documenting.

## 4. Error Handling

- Use specific exceptions (e.g., `ValueError`, `ConnectionError`) instead of bare `Exception`.
- Fail fast and utilize early returns to reduce nesting.
- Log errors contextually.

## 5. Refactoring Checklist

- [ ] Are variable names descriptive? (Avoid `d`, `x`, `temp`)
- [ ] Is there duplicated code? (DRY principle)
- [ ] Are magic numbers replaced with named constants?
- [ ] Is the code complexity low? (Cyclomatic complexity)

## 6. Python Specifics

- Use list comprehensions where readable.
- Use `f-strings` for string formatting.
- Use `pathlib` over `os.path` where possible.
- Use context managers (`with` statement) for file/resource handling.
