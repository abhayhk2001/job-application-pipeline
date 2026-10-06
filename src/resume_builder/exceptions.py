"""Custom exceptions raised by the resume builder."""


class ResumeBuilderError(Exception):
    """Base error for the resume_builder package."""


class TemplateRenderError(ResumeBuilderError):
    """A Jinja2 template failed to render."""


class TemplateNotFound(ResumeBuilderError):
    """No template by that name is on the search path.

    Carries ``available`` so the message can name the valid choices: that list
    is what an agent needs in order to retry, and printing it is cheaper than
    making the caller run ``--list-templates`` to find out.
    """

    def __init__(self, name, available):
        self.name = name
        self.available = list(available)
        choices = ", ".join(self.available) if self.available else "none found"
        super().__init__(f"unknown template {name!r}; available: {choices}")


class TectonicNotFound(ResumeBuilderError):
    """The tectonic binary is not on PATH."""


class CompileError(ResumeBuilderError):
    """tectonic exited non-zero while compiling a .tex file."""


class ValidationError(ResumeBuilderError):
    """A resume JSON failed validation. Carries every problem found."""

    def __init__(self, problems):
        self.problems = list(problems)
        detail = "\n".join(f"  {p}" for p in self.problems)
        super().__init__(f"{len(self.problems)} validation problem(s):\n{detail}")
