"""Custom exceptions raised by the resume builder."""


class ResumeBuilderError(Exception):
    """Base error for the resume_builder package."""


class TemplateRenderError(ResumeBuilderError):
    """A Jinja2 template failed to render."""


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
