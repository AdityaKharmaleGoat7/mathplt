"""AnimationRegistry — auto-discovery and registration of animator classes."""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from manifold.core.animator import BaseAnimator


class AnimationRegistry:
    """
    Central registry for all animator classes.

    Usage:
        @AnimationRegistry.register
        class MyAnimator(BaseAnimator):
            NAME = "my_animation"
            ...

    Then at startup:
        AnimationRegistry.discover()   # auto-imports all animation modules

    Look up:
        cls = AnimationRegistry.get("my_animation")
    """

    _registry: dict[str, Type[BaseAnimator]] = {}

    @classmethod
    def register(cls, animator_class: Type[BaseAnimator]) -> Type[BaseAnimator]:
        """Class decorator — registers the animator by its NAME."""
        if not animator_class.NAME:
            raise ValueError(f"{animator_class.__name__} must define a non-empty NAME attribute")
        cls._registry[animator_class.NAME] = animator_class
        return animator_class

    @classmethod
    def get(cls, name: str) -> Type[BaseAnimator]:
        """Return the animator class for the given name."""
        if name not in cls._registry:
            available = ", ".join(cls.list_names()) or "(none registered)"
            raise KeyError(f"Unknown animation '{name}'. Available: {available}")
        return cls._registry[name]

    @classmethod
    def list_names(cls) -> list[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def list_all(cls) -> list[tuple[str, str]]:
        """Return list of (name, description) pairs, sorted by name."""
        return [
            (name, cls._registry[name].DESCRIPTION)
            for name in cls.list_names()
        ]

    @classmethod
    def discover(cls) -> None:
        """
        Walk the manifold.animations package and import every module.
        Each module's @AnimationRegistry.register decorators fire on import,
        populating the registry automatically.
        """
        import manifold.animations as animations_pkg
        for _finder, module_name, _ispkg in pkgutil.walk_packages(
            path=animations_pkg.__path__,
            prefix=animations_pkg.__name__ + ".",
            onerror=lambda name: None,
        ):
            importlib.import_module(module_name)
