# PA 7: The Parameter Simulator — Part A

**CS 379: Programming Languages (Fall 2026)** — Ammar AlTameemy

Notation. Storage is modeled as `Cell` objects (mutable boxes), as in `parameters.py`. `C1`, `C2`, … name distinct Cells, so `a → C1(1)` means "the name `a` is bound to Cell `C1`, which currently holds 1." Two names bound to the *same* Cell are aliases.

Every callee activation record (from PA 6) has this shape:

| Field | Value for these calls |
|---|---|
| `function_name` | `swap` / `P` |
| `parameters` | values bound on entry |
| `locals_env` | the callee's `Environment` (shown below at each step) |
| `return_address` | the call site in the caller |
| `static_link` | `None` (both functions are top-level) |
| `dynamic_link` | the caller's frame (`main`) |

---

## 1. Three Modes, One Function

```
swap(a, b) { let t = a; a = b; b = t; }      caller: x = 1, y = 2;  swap(x, y)
```

Caller frame before the call in every mode: `x → C1(1)`, `y → C2(2)`.

### 1a. Pass-by-value

On entry, each argument is evaluated and placed in a **new callee-owned Cell**.

| Step | Callee `locals_env` | Caller `x`, `y` |
|---|---|---|
| bind | `a → C3(1)`, `b → C4(2)` | `C1(1)`, `C2(2)` |
| `let t = a` | `a → C3(1)`, `b → C4(2)`, `t → C5(1)` | 1, 2 |
| `a = b` | `a → C3(2)`, `b → C4(2)`, `t → C5(1)` | 1, 2 |
| `b = t` | `a → C3(2)`, `b → C4(1)`, `t → C5(1)` | 1, 2 |
| return | frame popped; C3–C5 discarded | **x = 1, y = 2** |

The callee swapped its own private copies. Nothing in the caller changed, so the swap has **no effect** on the caller.

### 1b. Pass-by-reference

On entry, each parameter name is bound to **the caller's own Cell**. No new Cell is made for `a` or `b`.

| Step | Callee `locals_env` | Caller `x`, `y` |
|---|---|---|
| bind | `a → C1(1)`, `b → C2(2)` | `C1(1)`, `C2(2)` |
| `let t = a` | `a → C1(1)`, `b → C2(2)`, `t → C3(1)` | 1, 2 |
| `a = b` | `a → C1(2)`, `b → C2(2)`, `t → C3(1)` | **2**, 2 ← visible immediately |
| `b = t` | `a → C1(2)`, `b → C2(1)`, `t → C3(1)` | 2, **1** |
| return | frame popped; only C3 (`t`) discarded | **x = 2, y = 1** |

Every write to `a` or `b` is a write to `x` or `y`, and the caller can see it as soon as it happens, even in the middle of the call. Only `t` is a true local. **The swap succeeds.**

### 1c. Pass-by-value-result (copy-in / copy-out)

On entry, each argument's value is copied into a **new private Cell**, and the callee also records the caller destination for each parameter. In the record: `pending_writeback = [(a → C1 "x"), (b → C2 "y")]`.

| Step | Callee `locals_env` | Caller `x`, `y` |
|---|---|---|
| bind (copy in) | `a → C3(1)`, `b → C4(2)`; pending `[a→x, b→y]` | 1, 2 |
| `let t = a` | `a → C3(1)`, `b → C4(2)`, `t → C5(1)` | 1, 2 |
| `a = b` | `a → C3(2)`, `b → C4(2)`, `t → C5(1)` | 1, 2 ← **not** visible yet |
| `b = t` | `a → C3(2)`, `b → C4(1)`, `t → C5(1)` | 1, 2 |
| return: copy out `a → x` | (unchanged) | **2**, 2 |
| return: copy out `b → y` | (unchanged) | 2, **1** |
| frame popped | C3–C5 discarded | **x = 2, y = 1** |

The final answer matches pass-by-reference, but the timing does not. The caller sees nothing until the call returns. Then the final local values are copied back left to right in parameter order.

### Summary and verification question

| Mode | Owner of the writable cell | When the caller sees `a = …` | Test that exposes a wrong implementation |
|---|---|---|---|
| value | the **callee** (new Cell) | never | `value mode allocates a separate Cell` and `value-mode assignment leaves caller at 10`; also `swap` must return (1, 2) |
| reference | the **caller** (shared Cell) | immediately, during the call | `reference mode shares the caller Cell` (identity check `is`) and `reference write is visible before return` |
| value-result | the **callee** during the call, then the caller's Cell is written at return | only at return | `value-result write is hidden before return` / `appears at return`, and `value-result P(a,a) … ends at 11` (copy-back order) |

(Python passing a reference to a mutable `list` lets two names share one *object*. That is object aliasing. It is not USILang pass-by-reference, which shares the *variable slot* (the Cell) itself. If the callee assigns a new value to the parameter name, the change still reaches the caller.)

---

## 2. Asymmetric Aliasing

```
P(x, y) { x = x + 1; y = y + 1; }      caller: a = 10;  P(a, a)
```

Caller frame: `a → C1(10)`.

### 2a. Pass-by-reference

Both parameters are bound to the **same** caller Cell, so `x` and `y` are both aliases of `a`.

| Step | Callee `locals_env` | Caller `a` |
|---|---|---|
| bind | `x → C1(10)`, `y → C1(10)` | 10 |
| `x = x + 1` | reads C1 = 10, writes C1 = 11 | 11 |
| `y = y + 1` | reads C1 = **11** (sees x's write), writes C1 = 12 | 12 |
| return | nothing to copy | **a = 12** |

### 2b. Pass-by-value-result (copy back x, then y)

Each parameter gets its **own private copy** of 10. Both destinations are recorded as `C1` (the caller's `a`).

| Step | Callee `locals_env` | Caller `a` |
|---|---|---|
| bind (copy in) | `x → C2(10)`, `y → C3(10)`; pending `[x→a, y→a]` | 10 |
| `x = x + 1` | `x → C2(11)`, `y → C3(10)` | 10 |
| `y = y + 1` | reads C3 = **10** (can't see x's write), `y → C3(11)` | 10 |
| return: copy out `x → a` | | 11 |
| return: copy out `y → a` | | 11 (overwrites with 11) |
| | | **a = 11** |

### Why 12 vs. 11

- **Reference (12):** There is only one storage cell. The two increments are applied **one after the other** to the same value, 10 → 11 → 12. The second statement reads the value the first one wrote.
- **Value-result (11):** There are two independent copies. Each is incremented **once from 10**, so both end at 11. When the call returns, both copies are written to the same destination. The writes happen in declaration order (`x` first, then `y`), and the last write wins. Here both values are 11, so `a = 11`. One increment is effectively lost because the copies were never aliased during the body.

The copy-back order must be defined because the final value depends on it. If the body had been `{ x = x + 1; y = y + 5; }`, then left-to-right copy-back would give `a = 15` (y's value wins), while right-to-left would give `a = 11`.

**Why `swap(a, a)` doesn't show this:** in `swap`, both parameters are used symmetrically. Under reference, `t = a; a = a; a = t` writes the original value back. Under value-result, both private copies end up holding that same value, so copying back in either order gives the same result. In both modes `a` is unchanged. The difference only shows up when the two aliased parameters are updated in *different* ways, so that one update has to read the other's write.

---

## 3. Closures and Capture

```
let makers = [];
for (i = 0; i < 3; i = i + 1) {
    makers.push(func() { return i; });
}
```

**Result: all three closures return `3`.**

**Why.** A closure is a pair: the code and a pointer to its **defining environment**. It does not store a copy of the values of its free variables. In this loop there is only **one** variable `i`, so there is one Cell, `i → C(…)`, in the environment that contains the loop. All three `func() { return i; }` closures are created while that same environment is active, so all three store a pointer to the **same** environment.

When a closure is called later, `Closure.call` creates a new call environment whose **parent is the defining environment**, not the caller's environment. This parent pointer is the **static link** from PA 6. It points to the frame where the function was *written*, not the frame that *called* it. The body looks up the free name `i`. It is not found in the call environment, so the lookup follows the static link up to the defining environment and finds the single `i` Cell. By then the loop has finished: `i` was incremented to 3, the test `3 < 3` failed, and the loop exited. So each closure reads the *current* value of that shared Cell, which is 3. The calls return `3, 3, 3`, not `0, 1, 2`. (The `test_parameters.py` check "all three closures return the CURRENT (final) value of i" tests exactly this.)

**Minimal change to `for` (closures unchanged): a fresh binding of `i` for each iteration.** Change the semantics of `for` so that **each iteration runs the body in a new child Environment that has its own new Cell for `i`**. The new Cell starts with the value `i` had at the end of the previous iteration. This works like `let` in a JavaScript `for` loop:

1. Run the initializer `i = 0` in a loop environment.
2. At the start of each iteration, create `iter_env = Environment(parent=outer)` and define `i → Cell(previous value)` in it.
3. Run the test, the body, and the closure creation in `iter_env`.
4. Before the update step `i = i + 1`, copy `i` into the *next* iteration's new Cell and increment that one. The Cell an earlier closure captured is never changed again.

The closures still capture an environment, and that mechanism stays the same. The difference is that each closure now captures a *different* environment, with its own Cell for `i`, holding 0, 1, and 2. The calls then return `0, 1, 2`. Only the `for` statement's scoping rule changed. `Closure` and the static-link lookup work exactly as before.
