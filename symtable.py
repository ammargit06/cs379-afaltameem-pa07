"""
PA 4: The USILang Symbol Table -- starter.

Complete Environment and check_program below. See
PA_04_The_USILang_Symbol_Table.md, Part B, for the full requirements.
"""

from typing import Optional

from parser import Assignment, BinOp, Declaration, Number, Program, Variable


class SemanticError(Exception):
    pass


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent = parent
        self._names: dict = {}  # name -> declaration line (PA 4) or Cell (PA 7), THIS scope only

    def define(self, name: str, line: object) -> None:
        """
        Store name -> line in THIS scope. Raise SemanticError if `name`
        is already defined in THIS scope (not a parent scope --
        shadowing a parent name is allowed).
        """
        if name in self._names:
            original_line = self._names[name]
            raise SemanticError(
                f"Duplicate declaration of '{name}' (line {line}; "
                f"originally declared line {original_line})."
            )
        self._names[name] = line

    def resolve(self, name: str) -> object:
        """
        Look up `name` in this scope, then climb `parent` links.
        Return the stored value unchanged (a declaration line in PA 4,
        the very same Cell object in PA 7), or raise SemanticError if
        not found anywhere in the chain.
        """
        if name in self._names:
            return self._names[name]
        if self.parent is not None:
            return self.parent.resolve(name)
        raise SemanticError(f"Use of undeclared variable '{name}'.")


def _resolve_reference(env: Environment, name: str, line: int) -> int:
    """Resolve `name`, but stamp the offending reference's own line onto
    the error -- Environment.resolve doesn't know which line asked."""
    try:
        return env.resolve(name)
    except SemanticError:
        raise SemanticError(f"Use of undeclared variable '{name}' (line {line}).")


def _check_expr(node: object, env: Environment) -> None:
    if isinstance(node, Number):
        return
    if isinstance(node, Variable):
        _resolve_reference(env, node.name, node.line)
        return
    if isinstance(node, BinOp):
        _check_expr(node.left, env)
        _check_expr(node.right, env)
        return
    raise TypeError(f"check_expr: unknown expression node {node!r}")


def check_program(ast: Program) -> Environment:
    """
    Walk `ast.statements` in order, using one top-level Environment.
    For a Declaration: resolve every Variable in its expr BEFORE
    defining the new name (so `let x = x;` fails as use-before-decl).
    For an Assignment: resolve the assigned-to name, then resolve
    every Variable in its expr. Errors must surface at the first
    offending statement, not be collected and reported together.
    """
    env = Environment()
    for stmt in ast.statements:
        if isinstance(stmt, Declaration):
            _check_expr(stmt.expr, env)
            env.define(stmt.name, stmt.line)
        elif isinstance(stmt, Assignment):
            _resolve_reference(env, stmt.name, stmt.line)
            _check_expr(stmt.expr, env)
        else:
            raise TypeError(f"check_program: unknown statement node {stmt!r}")
    return env
