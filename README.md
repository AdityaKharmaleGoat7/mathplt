# mathplt

A mathematical animation toolkit for visualizing complex functions, 2D and 3D graphs, and Riemann Hypothesis structures. Built for Jupyter notebooks and an interactive web app.

<br>

## Setup

```bash
pip install -e ".[notebook,webapp]"
```

Run the web app:

```bash
python -m webapp.app
```

Open **http://localhost:8050** in your browser.

Run Jupyter notebooks:

```bash
jupyter lab
```

<br>

## Animations

<br>

### 2D Graph f(x, t)

Animate any equation where `x` is the spatial axis and `t` advances each frame. Every frame redraws the curve, so anything that depends on `t` becomes a live animation.

<p align="center">
  <img src="assets/graph2d.gif" width="720" alt="2D Graph Animation"/>
</p>

<p align="center">
  <img src="assets/graph2d.png" width="720" alt="2D Graph Screenshot"/>
</p>

#### How it works

| Term | What it controls | Example |
|------|-----------------|---------|
| `A * sin(...)` | Amplitude, controls peak height | `2 * sin(x)` doubles height |
| `sin(k*x)` | Spatial frequency, peaks per unit | `sin(3*x)` is 3x denser |
| `sin(x - v*t)` | Wave travelling right at speed v | `sin(x - 2*t)` |
| `sin(x + v*t)` | Wave travelling left at speed v | `sin(x + t)` |
| `sin(x) * cos(t)` | Standing wave, nodes stay fixed | nodes at multiples of π |
| `* exp(-a*x**2)` | Gaussian envelope, localises the wave | `sin(x+t) * exp(-0.1*x**2)` |
| `f(x) + g(x)` | Superposition, interference and beats | `sin(x+t) + sin(x+1.05*t)` |

#### Equations to try

```
sin(x + t)
sin(x) * cos(t)
sin(x + t) * exp(-0.1 * x**2)
cos(3*x - 2*t) + 0.5 * sin(5*x + t)
sin(x * t) / (1 + x**2)
exp(-0.05*(x - 3*t)**2)
sin(x + t) + sin(x + 1.05*t)
tanh(x - 2*t)
```

<br>

### 3D Surface f(x, y)

Rotating 3D surface plots. Drag to orbit, scroll to zoom, use the Play button for a continuous 360° rotation. Color encodes height via the colorbar.

<p align="center">
  <img src="assets/graph3d.gif" width="720" alt="3D Surface Animation"/>
</p>

<p align="center">
  <img src="assets/graph3d.png" width="720" alt="3D Surface Screenshot"/>
</p>

#### Reading the surface

| Feature | What it means |
|---------|--------------|
| Peak (local max) | ∂f/∂x = 0 and ∂f/∂y = 0, curves downward in all directions |
| Valley (local min) | Same conditions, curves upward |
| Saddle point | Curves up in one direction, down in another |
| Flat ridge | Constant along one axis, varying along the other |
| Oscillating grid | `sin(x)*cos(y)`, periodic in both directions |
| Decaying amplitude | `exp(-(x²+y²))` shrinks surface toward zero from origin |

#### Equations to try

```
sin(sqrt(x**2 + y**2))
exp(-0.1*(x**2 + y**2)) * cos(x + y)
sin(x) * cos(y)
x * exp(-x**2 - y**2)
(1 - 2*(x**2+y**2)) * exp(-(x**2+y**2))
sin(x**2 + y**2) / (x**2 + y**2 + 1)
```

> Tip: `sin(sqrt(x**2 + y**2))` with range −6 to 6 gives beautiful circular ripples from the origin.

<br>

### Complex Plane f(z)

Domain coloring maps every point in the complex plane to a color. Phase (hue) and magnitude (brightness rings) are encoded simultaneously, making zeros, poles, and winding numbers instantly visible.

<p align="center">
  <img src="assets/complex_plane.gif" width="720" alt="Complex Plane Animation"/>
</p>

<p align="center">
  <img src="assets/complex_plane.png" width="720" alt="Complex Plane Screenshot"/>
</p>

#### How to read the colors

| Visual feature | What it encodes | Formula |
|---------------|----------------|---------|
| Hue (color wheel) | Phase / argument of output | `arg(f(z))` in [−π, π] |
| Brightness rings | Magnitude on a log scale, each ring is ×e | `log(1 + |f(z)|)` |
| Dark pinch points | Zeros where f(z) = 0 | All colors converge inward |
| Bright chaos | Poles where |f(z)| → ∞ | Colors cycle rapidly outward |
| Color cycles per loop | Winding number / order | One full cycle = order 1 zero or pole |

#### Phase color reference

| Color | Phase |
|-------|-------|
| Red | 0 |
| Yellow | π/3 |
| Green | 2π/3 |
| Cyan | ±π |
| Blue | −2π/3 |
| Magenta | −π/3 |

#### Equations to try (variable `z`)

```
z**2
z**3 - 1
z**4 - 1
(z**2 - 1) / (z**2 + 1)
sin(z)
exp(z)
log(z)
1 / z
(z - 1j) / (z + 1j)
z * exp(-abs(z)**2 / 4)
```

#### Animated (include `t`, use Play button)

```
z**2 + t * 0.3
sin(z + t)
z**3 + t * z
```

<br>

### Riemann Hypothesis

> *"The nontrivial zeros of ζ(s) have real part equal to 1/2."*  Bernhard Riemann, 1859

The **Riemann zeta function** is defined for `Re(s) > 1` as the Dirichlet series:

```
ζ(s) = 1 + 1/2^s + 1/3^s + 1/4^s + ...
```

and extended to the entire complex plane via analytic continuation. It is one of the most studied functions in mathematics. Its zeros encode the distribution of prime numbers, and the **Riemann Hypothesis** (that all nontrivial zeros lie on the line `Re(s) = ½`) has been open since 1859 and carries a $1 million Millennium Prize.

<br>

#### Zeros on the Critical Line

Traces the path of `ζ(½ + it)` in the complex plane as `t` grows. Every time the orange dot crosses the origin (white cross), a nontrivial zero of ζ(s) occurs. Red dashed lines mark the zero locations on the magnitude plot at right.

<p align="center">
  <img src="assets/riemann_zeros.gif" width="720" alt="Riemann Zeros Animation"/>
</p>

<p align="center">
  <img src="assets/riemann_zeros.png" width="720" alt="Riemann Zeros Screenshot"/>
</p>

Known zeros (imaginary parts of the first eight):

| # | Im(s) |
|---|-------|
| 1 | 14.135 |
| 2 | 21.022 |
| 3 | 25.011 |
| 4 | 30.425 |
| 5 | 32.935 |
| 6 | 37.586 |
| 7 | 40.919 |
| 8 | 43.327 |

<br>

#### Critical Strip Heatmap

Shows `log(1+|ζ(s)|)` and `arg(ζ(s))` as heatmaps over the critical strip `0 < Re(s) < 1`. Zeros appear as dark spots on the magnitude map and as phase vortices on the argument map. The cyan dashed line marks the critical line `Re(s) = ½` where the Riemann Hypothesis predicts all nontrivial zeros lie.

<p align="center">
  <img src="assets/critical_strip.png" width="720" alt="Critical Strip Heatmap"/>
</p>

| Region | Significance |
|--------|-------------|
| `Re(s) < 0` | Trivial zeros at negative even integers; ζ is well understood |
| `0 < Re(s) < 1` | Critical strip, all nontrivial zeros live here |
| `Re(s) = ½` | Critical line, Riemann conjectured all zeros are exactly here |
| `Re(s) > 1` | `ζ(s) = Σ 1/nˢ` converges; no zeros exist |

<br>

#### Winding Number (Argument Principle)

The **argument principle** states the number of zeros of ζ(s) inside a closed contour C equals the winding number of the image ζ(C) around the origin:

```
N(zeros inside C) = (1/2π) × total change in arg(ζ(C))
```

As the rectangular contour expands upward in the s-plane, the image `ζ(C)` in the w-plane winds around the origin once per enclosed zero. Watch the winding count increment live as you raise the contour top slider.

<br>

## Project Structure

```
mathplt/
  core/          BaseAnimator, AnimationRegistry, EquationParser (AST safe eval)
  math/          zeta.py (mpmath), complex_ops.py (domain coloring), numerics.py
  animations/    graph2d, graph3d, complex_plane
    riemann/     zeros, critical_strip, zeta_surface, winding_number, continuation
  jupyter/       EquationWidget, AnimationWidget

notebooks/
  01_graph2d.ipynb
  02_graph3d.ipynb
  03_complex_plane.ipynb
  04_riemann.ipynb

webapp/
  app.py         Dash + Plotly web app (rotate, zoom, pan, animate)

assets/
  graph2d.png / graph2d.gif
  graph3d.png / graph3d.gif
  complex_plane.png / complex_plane.gif
  riemann_zeros.png / riemann_zeros.gif
  critical_strip.png
```

<br>

## Extending

Adding a new animation is one file:

```python
# mathplt/animations/my_animation.py
from mathplt.core.animator import BaseAnimator, AnimationConfig
from mathplt.core.registry import AnimationRegistry

@AnimationRegistry.register
class MyAnimator(BaseAnimator):
    NAME = "my_animation"
    DESCRIPTION = "What it does"

    def setup(self) -> None:
        self.fig, ax = ...

    def update(self, frame: int) -> list:
        return [self._line]
```

It will be auto discovered with no other changes needed.

<br>

## Tech Stack

| Library | Purpose |
|---------|---------|
| matplotlib | Jupyter notebook animations |
| plotly + dash | Interactive web app |
| mpmath | High precision complex math (zeta function) |
| numpy | Numerical arrays |
| scipy | Numerical utilities |
| ipywidgets | Jupyter equation input widgets |
