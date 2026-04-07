"""BaseAnimator ABC and AnimationConfig dataclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import matplotlib
import matplotlib.animation as animation
import matplotlib.pyplot as plt


@dataclass
class AnimationConfig:
    fps: int = 30
    duration_seconds: float = 10.0
    figsize: tuple[float, float] = (12.0, 6.0)
    dpi: int = 100
    title: str = ""
    output_path: str | None = None  # None → display inline in Jupyter
    dark_mode: bool = True
    extra: dict = field(default_factory=dict)


class BaseAnimator(ABC):
    """
    Contract every animation type must fulfill.

    Subclasses define:
      - NAME: str          — registry key (e.g. "riemann.zeros")
      - DESCRIPTION: str   — shown in notebook widget menus
      - setup()            — create fig, axes, initial artists
      - update(frame)      — mutate artists, return list of changed ones (blit=True)
    """

    NAME: str = ""
    DESCRIPTION: str = ""

    def __init__(self, config: AnimationConfig) -> None:
        self.config = config
        self.fig: plt.Figure | None = None
        self.axes: list[plt.Axes] = []
        self._anim: animation.FuncAnimation | None = None

        if config.dark_mode:
            plt.style.use("dark_background")

    @abstractmethod
    def setup(self) -> None:
        """Create figure, axes, and initial artists. Called once before animation starts."""
        ...

    @abstractmethod
    def update(self, frame: int) -> list[Any]:
        """
        Advance animation by one frame.
        Must return list of matplotlib artists that changed (required for blit=True).
        """
        ...

    def total_frames(self) -> int:
        return int(self.config.fps * self.config.duration_seconds)

    def build(self) -> animation.FuncAnimation:
        """Run setup() and create the FuncAnimation object."""
        self.setup()
        if self.config.title and self.fig is not None:
            self.fig.suptitle(self.config.title, color="white" if self.config.dark_mode else "black")
        self._anim = animation.FuncAnimation(
            self.fig,
            self.update,
            frames=self.total_frames(),
            interval=1000 // self.config.fps,
            blit=True,
        )
        return self._anim

    def to_jshtml(self) -> str:
        """Render animation as interactive JS HTML (best for Jupyter inline display)."""
        if self._anim is None:
            self.build()
        return self._anim.to_jshtml()

    def to_html5_video(self) -> str:
        """Render animation as HTML5 video tag (requires ffmpeg)."""
        if self._anim is None:
            self.build()
        return self._anim.to_html5_video()

    def save(self, path: str) -> None:
        """Save animation to file (.mp4, .gif, .webm)."""
        if self._anim is None:
            self.build()
        suffix = path.rsplit(".", 1)[-1].lower()
        if suffix == "gif":
            writer = animation.PillowWriter(fps=self.config.fps)
        elif suffix in ("mp4", "webm"):
            writer = animation.FFMpegWriter(fps=self.config.fps)
        else:
            raise ValueError(f"Unsupported format: .{suffix}. Use .mp4, .gif, or .webm")
        self._anim.save(path, writer=writer, dpi=self.config.dpi)
