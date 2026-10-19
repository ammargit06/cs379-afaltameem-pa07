"""
PA 6: The Activation Record -- starter.

Complete ActivationRecord and CallStack below. See
PA_06_The_Activation_Record.md, Part B, for the full requirements.

Note on scope: PA1-5 never added function-call SYNTAX to USILang's
grammar (deliberately -- see PA5's pipeline-context note). PA6's
Part B interface is pure Python classes with no mention of parser
changes either, so test_frames.py drives ActivationRecord/CallStack
directly in Python (simulating what a parsed function call sequence
would do) rather than parsing real USILang function syntax. Your job
this week is the frame model itself, not a grammar extension.
"""

from typing import Dict, List, Optional

from symtable import Environment


class ActivationRecord:
    """
    One frame on the call stack: everything a single invocation of a
    function needs to run and then return control to its caller.

    - parameters:     the argument values bound for this call
    - locals_env:     a PA 5 Environment holding this call's local names
    - return_address: where execution resumes once this call returns
    - static_link:    frame of the LEXICALLY enclosing function (where
                      this function was defined); None for top-level
    - dynamic_link:   frame of the CALLER (who invoked this call);
                      None for the outermost call
    """

    def __init__(
        self,
        function_name: str,
        parameters: Dict[str, object],
        locals_env: Environment,
        return_address: str,
        static_link: Optional["ActivationRecord"],
        dynamic_link: Optional["ActivationRecord"],
    ) -> None:
        if not isinstance(locals_env, Environment):
            raise TypeError("locals_env must be a PA 5 Environment instance.")
        self.function_name = function_name
        self.parameters = dict(parameters)
        self.locals_env = locals_env
        self.return_address = return_address
        self.static_link = static_link
        self.dynamic_link = dynamic_link

    def describe(self) -> str:
        params = ", ".join(f"{k}={v!r}" for k, v in self.parameters.items())
        static = self.static_link.function_name if self.static_link else "None"
        dynamic = self.dynamic_link.function_name if self.dynamic_link else "None"
        return (
            f"{self.function_name}({params}) "
            f"ret={self.return_address!r} static={static} dynamic={dynamic}"
        )

    def __repr__(self) -> str:
        return f"<ActivationRecord {self.describe()}>"


class CallStack:
    """LIFO stack of ActivationRecords. Index 0 is the bottom (oldest call)."""

    def __init__(self) -> None:
        self._frames: List[ActivationRecord] = []

    def push(self, record: ActivationRecord) -> None:
        if not isinstance(record, ActivationRecord):
            raise TypeError("CallStack.push() expects an ActivationRecord.")
        self._frames.append(record)

    def pop(self) -> ActivationRecord:
        """Remove and return the top frame."""
        if not self._frames:
            raise IndexError("pop from empty CallStack (no active frame to return from).")
        return self._frames.pop()

    def current(self) -> ActivationRecord:
        """Return (without removing) the top frame."""
        if not self._frames:
            raise IndexError("current() on empty CallStack (no active frame).")
        return self._frames[-1]

    def trace(self) -> List[str]:
        """
        Return one formatted string per live frame, BOTTOM of the
        stack first (oldest call first). Each line includes the
        function_name and its parameters.
        """
        return [f"#{depth} {frame.describe()}" for depth, frame in enumerate(self._frames)]

    def __len__(self) -> int:
        return len(self._frames)
