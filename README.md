# PA 7: The Parameter Simulator

Full assignment: `PA_07_The_Parameter_Simulator.md` (course handout; copy it alongside this starter when staging the repository).

## GitHub workflow
Use **Use this template** to create your own repository, clone it, add your
completed prior-stage dependencies, and commit and push your PA 7 work. Submit
the files and evidence listed in the assignment through Blackboard.

## Setup
Paste your own completed `lexer.py`/`parser.py`/`symtable.py`/`frames.py`
in first.
The PA 7 preflight exercises `Environment` and `ActivationRecord` before the
PA 7 cases. `lexer.py` and `parser.py` supply imported AST types; this harness
does not retest their full implementations. Run your earlier-stage tests separately.

## Run
```bash
python test_parameters.py
```
Complete `bind_parameters`, `commit_value_result`, and `Closure` in
`parameters.py` (`Cell`, `evaluate()`, and `FunctionDecl` are already
given). Success Token: prints the literal string
`PARAMETER_BINDING_VERIFIED` once every check passes.

PA 4's `Environment` stored declaration line numbers. PA 7 uses the same
`define`/`resolve` interface to store mutable `Cell` objects. Reference and
value-result arguments must name caller variables; value arguments may be
expressions. `Closure.call` receives already-evaluated values and binds them
in a fresh child of the saved defining environment.

For value-result, `bind_parameters` records destinations at call time and
`commit_value_result` copies final values back at return, left to right in
parameter order. The asymmetric `P(a,a)` test distinguishes this from reference.

## Submit
1. `PA7_Theory.pdf` (or `.md`)
2. `parameters.py`, `lexer.py`, `parser.py`, `symtable.py`, `frames.py`
3. Full `python test_parameters.py` transcript, including swap, asymmetric `P(a,a)`, closure checks, and `PARAMETER_BINDING_VERIFIED`
