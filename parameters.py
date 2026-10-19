"""
PA 7: The Parameter Simulator -- starter.

Complete bind_parameters, commit_value_result, and Closure below.
Cell, evaluate(), and FunctionDecl are already provided -- do not
modify them. See the assignment, Part B, for the
full requirements.

Value-result binding has two steps: bind_parameters runs at call time
and records each caller destination; commit_value_result runs after
the simulated body and copies the final local values back in parameter
order. The handout specifies both steps.

Design note 2: variables are stored as Cell objects (a mutable box),
not raw values, specifically so reference-mode parameters can share
the exact same storage as the caller's variable -- see Part A,
Questions 1-2, for why "bind directly to the caller's slot" requires
this instead of just copying a plain value.
"""

from typing import Any, List, Tuple

from parser import BinOp, Number, Variable
from symtable import Environment


class Cell:
    """Given: a mutable box. Two names that share the SAME Cell are aliased."""

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value


class FunctionDecl:
    """Given: a minimal function declaration -- params and a single expr body."""

    __slots__ = ("params", "body")

    def __init__(self, params: List[str], body) -> None:
        self.params = params
        self.body = body


def evaluate(node, env: Environment):
    """Given: evaluate a PA3 expression AST node against `env` (Cells are transparently dereferenced)."""
    if isinstance(node, Number):
        return node.value
    if isinstance(node, Variable):
        val = env.resolve(node.name)
        return val.value if isinstance(val, Cell) else val
    if isinstance(node, BinOp):
        if node.op == "neg":
            return -evaluate(node.left, env)
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        return {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b, "/": lambda a, b: a / b}[node.op](left, right)
    raise ValueError(f"cannot evaluate node: {node!r}")


def assign_through(env: Environment, name: str, value: Any) -> None:
    """Given: write `value` into whatever Cell `name` resolves to (mutates in place, does not rebind)."""
    cell = env.resolve(name)
    if not isinstance(cell, Cell):
        raise TypeError(f"'{name}' is not bound to a Cell -- did you forget to wrap it?")
    cell.value = value


VALID_MODES = ("value", "reference", "value-result")


def _require_variable(arg_node, param_name: str, mode: str) -> str:
    """Reference and value-result arguments need a writable caller destination."""
    if not isinstance(arg_node, Variable):
        raise TypeError(
            f"parameter '{param_name}' is {mode} mode: its argument must be a caller "
            f"variable, not {arg_node!r}"
        )
    return arg_node.name


def _caller_cell(caller_env: Environment, name: str) -> Cell:
    cell = caller_env.resolve(name)
    if not isinstance(cell, Cell):
        raise TypeError(f"caller variable '{name}' is not bound to a Cell")
    return cell


def bind_parameters(param_specs: List[Tuple[str, str]], arg_nodes: list, caller_env: Environment, callee_record) -> None:
    """
    Populate callee_record.locals_env according to each parameter's
    mode ("value", "reference", or "value-result"). For value-result
    parameters, also record what commit_value_result needs to do the
    delayed write-back later -- store it whichever way you like (e.g.
    an attribute on callee_record such as callee_record.pending_writeback).
    """
    if len(param_specs) != len(arg_nodes):
        raise TypeError(f"expected {len(param_specs)} argument(s), got {len(arg_nodes)}")

    locals_env = callee_record.locals_env
    # (param_name, caller_name, caller_cell) in parameter declaration order
    pending_writeback: List[Tuple[str, str, Cell]] = []

    for (param_name, mode), arg_node in zip(param_specs, arg_nodes):
        if mode == "value":
            # Fresh callee-owned Cell: writes to the parameter never reach the caller.
            cell = Cell(evaluate(arg_node, caller_env))
        elif mode == "reference":
            # Alias the caller's own Cell: writes are visible immediately.
            cell = _caller_cell(caller_env, _require_variable(arg_node, param_name, mode))
        elif mode == "value-result":
            # Copy in now to a private Cell; remember the destination for return time.
            caller_name = _require_variable(arg_node, param_name, mode)
            destination = _caller_cell(caller_env, caller_name)
            cell = Cell(destination.value)
            pending_writeback.append((param_name, caller_name, destination))
        else:
            raise ValueError(f"unknown parameter mode {mode!r} for '{param_name}' (expected one of {VALID_MODES})")

        locals_env.define(param_name, cell)
        callee_record.parameters[param_name] = cell.value

    callee_record.pending_writeback = pending_writeback


def commit_value_result(callee_record, caller_env: Environment) -> None:
    """
    For every value-result parameter bound by bind_parameters on this
    callee_record, copy its FINAL local value back into the caller's
    corresponding variable now (call this only after the callee's body
    has finished running).
    """
    pending = getattr(callee_record, "pending_writeback", [])
    # Left to right in parameter declaration order: with aliased arguments
    # such as P(a, a), the last parameter's copy-back wins.
    for param_name, _caller_name, destination in pending:
        destination.value = evaluate(Variable(param_name, 0), callee_record.locals_env)
    callee_record.pending_writeback = []


class Closure:
    def __init__(self, declaration: FunctionDecl, defining_env: Environment) -> None:
        self.declaration = declaration
        self.defining_env = defining_env

    def call(self, args: list, caller_env: Environment):
        """
        Create the callee Environment as a child of self.defining_env
        (NOT caller_env) -- this is what makes closure capture work.
        Bind each declaration.params[i] to args[i] (already-evaluated
        values, wrapped in a Cell), then evaluate declaration.body in
        that new environment and return the result.
        """
        params = self.declaration.params
        if len(args) != len(params):
            raise TypeError(f"expected {len(params)} argument(s), got {len(args)}")
        # caller_env is deliberately unused: free names resolve lexically.
        call_env = Environment(parent=self.defining_env)
        for name, value in zip(params, args):
            call_env.define(name, Cell(value))
        return evaluate(self.declaration.body, call_env)
