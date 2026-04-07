"""
Jupyter widgets for interactive equation input and animation display.

EquationWidget   — text box with live AST validation + submit button
AnimationWidget  — wraps BaseAnimator and renders inline as jshtml or HTML5

Usage in a notebook cell:
    from manifold.jupyter.widgets import EquationWidget, AnimationWidget
    from manifold.animations.graph2d import Graph2DAnimator
    from manifold.core.animator import AnimationConfig

    eq = EquationWidget(variable='x', placeholder='sin(x + t) * exp(-0.1 * x**2)')
    eq.display()
    # user types equation, hits Submit

    config = AnimationConfig(fps=30, duration_seconds=10.0)
    anim = AnimationWidget.from_name('graph2d', config, equation=eq.equation)
    anim.display()
"""

from __future__ import annotations

from typing import Callable

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.equation_parser import EquationParser
from manifold.core.registry import AnimationRegistry


class EquationWidget:
    """
    Interactive equation input widget for Jupyter notebooks.

    Displays an ipywidgets text input with live validation and a Submit button.
    After submission, the validated equation string is available via .equation.
    """

    def __init__(
        self,
        variable: str = "x",
        placeholder: str = "",
        on_submit: Callable[[str], None] | None = None,
        label: str = "",
    ) -> None:
        self.variable = variable
        self.on_submit = on_submit
        self._equation: str = placeholder
        self._valid: bool = False
        self._parser = EquationParser()

        # Build widgets lazily (avoids import error outside Jupyter)
        self._text = None
        self._button = None
        self._status = None
        self._box = None
        self._label_str = label or f"f({variable}) ="

    def _build_widgets(self) -> None:
        import ipywidgets as w

        self._text = w.Text(
            value=self._equation,
            placeholder=f"e.g. sin({self.variable} + t)",
            description=self._label_str,
            layout=w.Layout(width="420px"),
            style={"description_width": "initial"},
        )
        self._button = w.Button(
            description="Validate & Set",
            button_style="primary",
            layout=w.Layout(width="130px"),
        )
        self._status = w.HTML(value="<i>Enter equation above and click Validate.</i>")

        self._button.on_click(self._on_click)
        self._text.observe(self._on_type, names="value")

        self._box = w.VBox([
            w.HBox([self._text, self._button]),
            self._status,
        ])

    def _on_type(self, change) -> None:
        """Live validation as user types."""
        expr = change["new"]
        error = self._parser.validate(expr, variables={self.variable, "t"})
        if error:
            self._status.value = f'<span style="color:#ff6b6b">✗ {error}</span>'
            self._valid = False
        else:
            self._status.value = '<span style="color:#69db7c">✓ Valid equation</span>'
            self._valid = True
            self._equation = expr

    def _on_click(self, _btn) -> None:
        expr = self._text.value
        error = self._parser.validate(expr, variables={self.variable, "t"})
        if error:
            self._status.value = f'<span style="color:#ff6b6b">✗ {error}</span>'
            self._valid = False
        else:
            self._equation = expr
            self._valid = True
            self._status.value = (
                f'<span style="color:#69db7c">✓ Set: <b>f({self.variable}) = {expr}</b></span>'
            )
            if self.on_submit:
                self.on_submit(expr)

    def display(self) -> None:
        """Render the widget in the current Jupyter cell output."""
        from IPython.display import display as ipy_display
        if self._box is None:
            self._build_widgets()
        ipy_display(self._box)

    @property
    def equation(self) -> str:
        """The currently validated equation string."""
        return self._equation

    @equation.setter
    def equation(self, value: str) -> None:
        self._equation = value
        if self._text is not None:
            self._text.value = value


class AnimationWidget:
    """
    Renders a BaseAnimator animation inline in Jupyter notebooks.

    Supports jshtml (interactive scrubber) and html5_video (requires ffmpeg).
    """

    def __init__(self, animator: BaseAnimator) -> None:
        self._animator = animator
        self._built = False

    @classmethod
    def from_name(
        cls,
        name: str,
        config: AnimationConfig,
        **kwargs,
    ) -> "AnimationWidget":
        """Convenience: look up animator by registry name and instantiate."""
        animator_cls = AnimationRegistry.get(name)
        animator = animator_cls(config, **kwargs)
        return cls(animator)

    def display(self, mode: str = "jshtml") -> None:
        """
        Render animation inline.

        Parameters:
            mode: "jshtml" (default, interactive scrubber) or "html5_video" (requires ffmpeg)
        """
        from IPython.display import HTML, display as ipy_display

        if not self._built:
            self._animator.build()
            self._built = True

        if mode == "jshtml":
            html = self._animator.to_jshtml()
        elif mode == "html5_video":
            html = self._animator.to_html5_video()
        else:
            raise ValueError(f"Unknown mode '{mode}'. Use 'jshtml' or 'html5_video'.")

        ipy_display(HTML(html))

    def save(self, path: str) -> None:
        """Save animation to file (.mp4, .gif, .webm)."""
        if not self._built:
            self._animator.build()
            self._built = True
        self._animator.save(path)
        print(f"Saved to {path}")


def list_animations() -> None:
    """Print all available animations (for use in notebooks)."""
    from IPython.display import HTML, display as ipy_display

    rows = "".join(
        f"<tr><td><code>{name}</code></td><td>{desc}</td></tr>"
        for name, desc in AnimationRegistry.list_all()
    )
    table = f"""
    <table>
      <thead><tr><th>Name</th><th>Description</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """
    ipy_display(HTML(table))
