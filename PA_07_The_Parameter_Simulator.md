# PA 7: The Parameter Simulator
## CS 379: Programming Languages (Fall 2026)

**Starter repository (GitHub template):** [https://github.com/cwillpinto/cs379-pa07-parameter-simulator](https://github.com/cwillpinto/cs379-pa07-parameter-simulator)

### 🔧 Pipeline Context
This is the **argument-binding stage** of the USILang pipeline. It builds on the `ActivationRecord` model from PA 6: the Python harness creates a call frame, and your code decides how arguments occupy its parameter slots. It also introduces **closures**, functions that carry their defining environment with them. PA 7 uses Python AST objects and a simulated call body; the supplied parser does not parse function calls. This call model prepares the dispatch target for PA 8's VTable work.

**Schedule:** The Week 8 PA 7 lesson meets Tuesday, October 13, 2026. This is a complete 100-point Project-Oriented Assignment. Due Monday, October 19, 2026 at 11:59 PM Central.

**Verification question:** For each binding mode, identify who owns the writable cell, when the caller can observe an assignment to the parameter name, and which test would expose an incorrect implementation. Python's sharing of a mutable list object is a separate object-aliasing example; it is not itself USILang pass-by-reference.

---

### Part A: The Specification (50 Points)
**Instructions:** Answer the following in a separate document (PDF or Markdown).

1. **Three Modes, One Function:**
   Given the USILang function `swap(a, b) { let t = a; a = b; b = t; }` called as `swap(x, y)` where `x = 1` and `y = 2` beforehand, trace the values of `x` and `y` **in the caller's scope** after the call returns, under each of these binding modes:
   - Pass-by-value
   - Pass-by-reference
   - Pass-by-value-result
   Show the intermediate state of the callee's activation record (from PA 6) for each mode, not just the final answer.

2. **Asymmetric Aliasing:**
   Let `P(x, y) { x = x + 1; y = y + 1; }` and call `P(a, a)` with caller `a = 10`. Trace each assignment under pass-by-reference and pass-by-value-result. For value-result, copy back at return in parameter order, `x` then `y`. Explain why the final caller values are 12 and 11. A symmetric `swap(a,a)` leaves `a` unchanged in both modes and does not demonstrate the difference.

3. **Closures and Capture:**
   Consider building three closures inside a loop:
   ```
   let makers = [];
   for (i = 0; i < 3; i = i + 1) {
       makers.push(func() { return i; });
   }
   ```
   If each closure captures the **environment**, not a snapshot of `i`'s value at creation time, what do all three closures return when called after the loop finishes? Explain why, referencing the static link concept from PA 6. Then describe the minimal change to USILang's `for` semantics (not the closure mechanism) that would make each closure capture a *different* value of `i`, the way `let`-per-iteration works in JavaScript.

---

### Part B: The Implementation (50 Points)
**Instructions:** Implement parameter-mode binding and closures in `parameters.py`, using the PA 6 frame model. The harness simulates calls; PA 6 did not supply a function-call evaluator.

**Requirements:**
1. Implement the binder:
   ```python
   def bind_parameters(param_specs: list[tuple[str, str]], arg_nodes: list, caller_env, callee_record) -> None:
       # param_specs: [("a", "value"), ("b", "reference"), ...]
       ...
   ```
   `bind_parameters` must populate `callee_record.locals_env` (the PA 6 `Environment`) according to each parameter's declared mode:
   - `"value"`: place the evaluated argument in a new callee `Cell`; assignment to the parameter name must not change the caller's variable `Cell`. Mutating a shared object held inside a `Cell` is a separate issue.
   - `"reference"`: bind the callee's parameter name directly to the caller's variable slot, so writes inside the callee are visible in the caller immediately.
   - `"value-result"`: copy the value in on call, and copy the (possibly mutated) local value back out to the caller's variable **only when the function returns** — not on every intermediate write.
   - Reference and value-result arguments must be caller variables, because they need writable destinations; value mode may receive an expression. Record value-result destinations at call time and use `commit_value_result(callee_record, caller_env)` after the body. Copy back left to right in parameter declaration order.
   - The PA 4 `Environment` interface remains the name-to-value mapping, but PA 7 stores `Cell` objects in it instead of declaration line numbers. Its `define` and `resolve` methods must preserve those objects. The PA 6 `ActivationRecord` supplies `locals_env`; the closure's lexical parent is an `Environment` link.
2. Represent each function parameter's mode in `param_specs` (for example, `[('a', 'reference'), ('b', 'reference')]` for `func swap(ref a, ref b)`). Represent an unannotated parameter as `('name', 'value')`; the Python harness supplies these tuples directly. The supplied parser does not implement function-call syntax or infer the default mode.
3. Implement `Closure`:
   ```python
   class Closure:
       def __init__(self, declaration, defining_env):
           ...
       def call(self, args, caller_env):
           ...
   ```
   `Closure.call` receives already-evaluated Python values in `args`. It must create a fresh callee `Environment` as a child of `defining_env` (the environment captured at closure-creation time), **not** a child of `caller_env`; bind each parameter to a new `Cell` there. This environment parent acts as the lexical link modeled in PA 6.
4. **Aliasing Safety:** your implementation must reproduce the asymmetric `P(a,a)` divergence from Part A. The harness checks both modes and the defined copy-back order.

**Dependency preflight:** Before running the harness, replace the placeholder `lexer.py`, `parser.py`, `symtable.py`, and `frames.py` with your completed prior-stage files. The PA 7 preflight exercises `Environment` and `ActivationRecord`; the lexer and parser provide imported AST types but their full behavior is not retested here. Run your earlier-stage tests separately.

**Verification:** Run `python test_parameters.py`. The harness checks `swap` under all three modes, asymmetric `P(a,a)`, cell sharing and return-time visibility, closure capture, and closure argument binding. If those checks pass, the script prints:
```
PARAMETER_BINDING_VERIFIED
```

---

### 🚀 Submission
1. `PA7_Theory.pdf` (or `.md`) — Part A answers.
2. `parameters.py`, `lexer.py`, `parser.py`, `symtable.py`, and `frames.py` — your implementation and completed dependencies.
3. The full `python test_parameters.py` transcript, including the mode, asymmetric `P(a,a)`, and closure checks, ending with the **`PARAMETER_BINDING_VERIFIED`** Success Token.

### Grading Rubric (100 Points)

| Criterion | Points | Evidence |
| :--- | ---: | :--- |
| Three-mode `swap` trace | 20 | Caller and callee states under value, reference, and value-result. |
| Asymmetric `P(a,a)` trace | 20 | Assignment-by-assignment reasoning and left-to-right copy-back; final values 12 and 11. |
| Closure explanation | 10 | Captured environment, static link, and per-iteration-cell alternative. |
| Parameter binder | 25 | Correct private `Cell`, shared caller `Cell`, and recorded value-result destinations. |
| Ordered copy-back | 10 | Final callee values copied to caller at return, in parameter order. |
| Closure implementation | 10 | New call environment is a child of `defining_env`; free names resolve lexically. |
| Reproducible verification | 5 | Completed PA6 dependencies, full test transcript, and Success Token. |
