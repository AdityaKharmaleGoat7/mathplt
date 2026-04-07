"""
Animation package — importing this module auto-discovers all animators.
Each module uses @AnimationRegistry.register to self-register.
"""

from manifold.core.registry import AnimationRegistry

AnimationRegistry.discover()
