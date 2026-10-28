# Plugging in your Endless Engine / Stereo Cat code

This repo does **not** contain the Endless Engine, the Stereo Cat recipes, or
any other ljrseals-dev code, and the three recipes in `engine_hooks.py`
(`mid_side_width`, `haas_cut`, `endless_drift`) are generic stand-ins. Here is
how to wire in the real thing.

## 1. Write a recipe file

```python
# my_recipes.py
def register(RECIPES):
    def stereo_cat_cut(y, ctx, amount=0.5):
        # y: float array (n_samples, 2); ctx: sr, bpm, sport, seed, rng
        # ... your T = P o R o C logic here ...
        return y
    RECIPES["stereo_cat_cut"] = stereo_cat_cut
```

## 2. Apply it

```bash
python legendary_sports_theme.py --sport boxing \
    --recipes my_recipes.py --recipe-names stereo_cat_cut
```

Params can be set by editing `Theme.recipes` entries to `("name", {"amount": 0.7})`.

## 3. Map your magic phrases

Edit `magic_phrases.json`. Each phrase can set `intensity`, `crowd`, `swing`
and/or `recipes`. Anything in a `--prompt` that contains the phrase triggers it:

```json
"cut the cat": {"recipes": ["stereo_cat_cut"], "intensity": 1.1}
```

## 4. Endless mode

`--endless N --seed S` renders N variations with seeds S..S+N-1. Seed 0 is
exact; any other seed humanises timing and jitters tempo. Put your engine's
variation logic in a recipe that reads `ctx["rng"]` / `ctx["seed"]`.
