"""
engine_hooks.py -- plug-in points for Endless Engine / Stereo Cat style recipes.

IMPORTANT (honesty note)
------------------------
The recipes registered below are *generic placeholder processors* written for
this repo (mid/side width, Haas-style channel cut, slow auto-drift). They are
NOT copied from the Endless Engine, "Cutting the Stereo Cat", or any other
ljrseals-dev code. Drop your real recipes in through `--recipes my_recipes.py`
(see `load_user_recipes`) and they will be applied by name.

A recipe is a function:  recipe(y, ctx, **params) -> y
    y    : float array shaped (n_samples, 2)
    ctx  : dict with keys  sr, bpm, sport, seed, rng
"""
from __future__ import annotations

import importlib.util
import math
from typing import Callable, Dict, Iterable

import numpy as np

RECIPES: Dict[str, Callable] = {}


def recipe(name: str):
    """Decorator that registers a recipe under `name`."""
    def deco(fn: Callable) -> Callable:
        RECIPES[name] = fn
        return fn
    return deco


@recipe("mid_side_width")
def mid_side_width(y, ctx, width: float = 1.3):
    """Scale the side signal. width>1 widens, width<1 narrows."""
    mid = (y[:, 0] + y[:, 1]) * 0.5
    side = (y[:, 0] - y[:, 1]) * 0.5 * width
    return np.stack([mid + side, mid - side], axis=1)


@recipe("haas_cut")
def haas_cut(y, ctx, ms: float = 11.0, mix: float = 0.35):
    """Blend in a short-delayed copy on the opposite channel (Haas-style spread)."""
    d = max(1, int(ctx["sr"] * ms / 1000.0))
    out = y.copy()
    out[d:, 0] += mix * y[:-d, 1]
    out[d:, 1] += mix * y[:-d, 0]
    return out / (1.0 + mix * 0.5)


@recipe("endless_drift")
def endless_drift(y, ctx, depth: float = 0.18, cycles_per_bar: float = 0.25):
    """Very slow auto-pan so long renders never sit perfectly still."""
    n = len(y)
    bar = 4 * 60.0 / ctx["bpm"]
    t = np.arange(n) / ctx["sr"]
    lfo = np.sin(2 * math.pi * (cycles_per_bar / bar) * t + ctx["rng"].uniform(0, 6.28))
    gl = 1.0 - depth * 0.5 * (1 + lfo)
    gr = 1.0 - depth * 0.5 * (1 - lfo)
    return np.stack([y[:, 0] * gl, y[:, 1] * gr], axis=1)


def load_user_recipes(path: str) -> None:
    """
    Import a python file that defines `register(RECIPES)`; use it to add your
    own recipes, e.g.

        # my_recipes.py
        def register(RECIPES):
            def my_cut(y, ctx, amount=0.5):
                ...
                return y
            RECIPES["stereo_cat_cut"] = my_cut
    """
    spec = importlib.util.spec_from_file_location("user_recipes", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load recipes from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "register"):
        raise AttributeError(f"{path} must define register(RECIPES)")
    mod.register(RECIPES)


def apply(names: Iterable, y, ctx):
    """Apply recipes in order. Each item is 'name' or ('name', {params})."""
    for item in names:
        name, params = (item, {}) if isinstance(item, str) else item
        if name not in RECIPES:
            raise KeyError(f"unknown recipe '{name}'. Known: {sorted(RECIPES)}")
        y = RECIPES[name](y, ctx, **params)
    return y
