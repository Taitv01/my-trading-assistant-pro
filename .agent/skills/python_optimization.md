---
name: python-optimization
description: Guidelines for optimizing Python code performance
---

# Python Performance Optimization

## 1. Data Processing (Pandas/NumPy)

- **Vectorization**: ALWAYS prefer vectorized operations over loops.
  - _Bad_: `for` loop to calculate RSI.
  - _Good_: `df['close'].diff()`, `df.rolling()`.
- **Memory Usage**:
  - Downcast numeric types if high precision isn't needed (e.g., `float64` -> `float32`).
  - Use `category` dtype for low-cardinality string columns.
- **Apply vs Vectorized**: Avoid `.apply()` on large DataFrames. Use numpy arrays or built-in pandas functions.

## 2. General Python

- **Generators**: Use generators (`yield`) for large data streams to save memory.
- **List Comprehensions**: Faster than `for` loops for creating lists.
- **Built-in Functions**: Use built-ins (`map`, `filter`, `sum`) as they are implemented in C.
- **String Concatenation**: Use `"".join(list)` instead of `+=` in loops.

## 3. I/O Operations

- **AsyncIO**: Use `async`/`await` for I/O bound tasks (network requests).
- **Batch Processing**: Process database/API calls in batches, not one-by-one.
- **Caching**: Use `functools.lru_cache` for expensive function calls with same flexible arguments.

## 4. Profiling

- Use `cProfile` to identify bottlenecks.
- Use `memory_profiler` to track memory usage.
