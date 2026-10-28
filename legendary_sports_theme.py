#!/usr/bin/env python3
"""
legendary_sports_theme.py -- procedural "legendary sports theme" generator.

Pure Python + numpy. No Suno, no samples, no network, no ML model: every sound
(stomps, claps, timpani, brass, choir, crowd, risers, crash) is synthesized
from scratch and written to a 16-bit stereo WAV.

Arrangement (8 bars, 4/4, then a ring-out tail):
    bars 0-1  TUNNEL    heartbeat kick, rising crowd, riser, timpani roll
    bars 2-3  FANFARE   solo brass states the motif over timpani
    bars 4-5  ANTHEM    stomp-stomp-clap, harmonised brass, choir pads, sub bass
    bars 6-7  FINAL     octave-up brass, driving stomps, snare roll, last hit

Usage
-----
    python legendary_sports_theme.py --sport football
    python legendary_sports_theme.py --prompt "legendary basketball entrance, 96 bpm, in F minor, endless"
    python legendary_sports_theme.py --sport soccer --endless 4 --seed 7
    python legendary_sports_theme.py --list
    python legendary_sports_theme.py --sport boxing --recipes my_recipes.py --recipe-names stereo_cat_cut
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import wave
from dataclasses import dataclass, replace
from typing import List, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_hooks as hooks  # noqa: E402

SR = 44100
MINOR = [0, 2, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
NOTE_NAMES = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5,
              "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9, "A#": 10,
              "BB": 10, "B": 11}


# --------------------------------------------------------------------------
# Theme definition
# --------------------------------------------------------------------------
@dataclass
class Theme:
    sport: str
    bpm: float
    root: int                      # MIDI note of the tonic (octave ~3)
    mode: str                      # "minor" | "major"
    motif: List[Tuple[int, float]]  # (scale degree, beats) -- must total 8 beats
    prog: List[int]                # chord-root scale degrees for bars 4-7
    swing: float = 0.0             # 0..0.5, delays off-beat eighths
    intensity: float = 1.0         # scales drums, crowd and bus drive
    crowd: float = 1.0
    recipes: Tuple = ()            # engine_hooks recipe names (or (name, params))
    blurb: str = ""


PRESETS = {
    "football": Theme("football", 104, 50, "minor",
                      [(0, 1), (0, .5), (2, .5), (4, 1.5), (2, .5), (4, 1), (7, 1), (5, 2)],
                      [0, 5, 6, 0], 0.0, 1.0, 1.0,
                      blurb="Gridiron stadium roar: D minor, heavy stomps, brass call to the field."),
    "basketball": Theme("basketball", 92, 53, "minor",
                        [(0, .5), (0, .5), (3, 1), (2, .5), (0, .5), (4, 1.5), (3, .5), (2, .5), (7, 2.5)],
                        [0, 3, 5, 6], 0.28, 1.0, 0.9,
                        blurb="Arena swagger: F minor, swung hats, syncopated brass hook."),
    "soccer": Theme("soccer", 120, 55, "major",
                    [(0, 1), (0, 1), (2, 1), (4, 1), (4, 1), (2, 1), (0, 2)],
                    [0, 4, 5, 3], 0.0, 1.0, 1.2,
                    blurb="Terrace chant: G major, singable motif, big crowd bed."),
    "boxing": Theme("boxing", 84, 48, "minor",
                    [(0, 2), (0, 1), (3, 1), (4, 2), (3, 1), (0, 1)],
                    [0, 0, 5, 6], 0.0, 1.15, 0.8,
                    blurb="Ring walk: C minor, slow and heavy, timpani-driven menace."),
    "baseball": Theme("baseball", 108, 48, "major",
                      [(0, 1), (2, 1), (4, 1), (7, 1), (4, 1), (2, 1), (0, 2)],
                      [0, 3, 4, 0], 0.12, 0.95, 1.0,
                      blurb="Ballpark charge: C major, bright rising arpeggio, organ-like warmth."),
}


# --------------------------------------------------------------------------
# Music helpers
# --------------------------------------------------------------------------
def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12.0)


def degree_midi(root: int, degree: int, mode: str) -> int:
    scale = MINOR if mode == "minor" else MAJOR
    octv, idx = divmod(degree, 7)
    return root + 12 * octv + scale[idx]


# --------------------------------------------------------------------------
# DSP helpers
# --------------------------------------------------------------------------
def tvec(n: int) -> np.ndarray:
    return np.arange(n) / SR


def bandpass(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(X * ((f >= lo) & (f <= hi)), len(x))


def norm(x: np.ndarray) -> np.ndarray:
    p = np.max(np.abs(x))
    return x / p if p > 1e-9 else x


class Mix:
    def __init__(self, seconds: float):
        self.n = int(seconds * SR)
        self.buf = np.zeros((self.n, 2))

    def add(self, sig: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0):
        i = max(0, int(t * SR))
        if i >= self.n:
            return
        sig = sig[: self.n - i]
        ang = (pan + 1.0) * math.pi / 4.0
        self.buf[i:i + len(sig), 0] += sig * gain * math.cos(ang)
        self.buf[i:i + len(sig), 1] += sig * gain * math.sin(ang)


# --------------------------------------------------------------------------
# Instruments
# --------------------------------------------------------------------------
def kick(rng, f0=150.0, f1=44.0, dur=0.42):
    n = int(dur * SR); t = tvec(n)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    y = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 8.5)
    y += 0.25 * bandpass(rng.standard_normal(n), 1500, 6000) * np.exp(-t * 120)
    return np.tanh(y * 1.8) * 0.9


def stomp(rng, dur=0.34):
    n = int(dur * SR); t = tvec(n)
    body = np.sin(2 * math.pi * np.cumsum(38 + 90 * np.exp(-t * 35)) / SR) * np.exp(-t * 11)
    thud = bandpass(rng.standard_normal(n), 60, 700) * np.exp(-t * 16)
    slap = bandpass(rng.standard_normal(n), 900, 4200) * np.exp(-t * 55) * 0.35
    return np.tanh((body + thud * 1.2 + slap) * 1.6) * 0.85


def clap(rng, dur=0.45):
    n = int(dur * SR); t = tvec(n)
    noise = bandpass(rng.standard_normal(n), 900, 3800)
    env = np.zeros(n)
    for k, off in enumerate((0.0, 0.011, 0.023)):
        i = int(off * SR)
        env[i:] += np.exp(-(t[: n - i]) * 150) * (1.0 - 0.15 * k)
    env += np.exp(-t * 16) * 0.5
    return norm(noise * env) * 0.8


def snare(rng, dur=0.3):
    n = int(dur * SR); t = tvec(n)
    tone = np.sin(2 * math.pi * 190 * t) * np.exp(-t * 28)
    noise = bandpass(rng.standard_normal(n), 1200, 9000) * np.exp(-t * 22)
    return norm(tone * 0.6 + noise) * 0.8


def hat(rng, dur=0.07):
    n = int(dur * SR); t = tvec(n)
    return norm(bandpass(rng.standard_normal(n), 6500, 16000) * np.exp(-t * 70)) * 0.5


def timpani(rng, freq, dur=1.6):
    n = int(dur * SR); t = tvec(n)
    ph = 2 * math.pi * np.cumsum(freq * (1 + 0.06 * np.exp(-t * 25))) / SR
    y = np.sin(ph) * np.exp(-t * 3.2) + 0.35 * np.sin(1.5 * ph) * np.exp(-t * 5.5)
    y += 0.5 * bandpass(rng.standard_normal(n), 80, 900) * np.exp(-t * 40)
    return np.tanh(y * 1.4) * 0.8


def crash(rng, dur=3.4):
    n = int(dur * SR); t = tvec(n)
    y = bandpass(rng.standard_normal(n), 3000, 18000) * (np.exp(-t * 2.0) + 0.3 * np.exp(-t * 0.6))
    return norm(y) * 0.6


def riser(rng, dur):
    n = int(dur * SR); t = tvec(n); u = t / dur
    noise = bandpass(rng.standard_normal(n), 2500, 15000) * u ** 2.2
    sweep = np.sin(2 * math.pi * np.cumsum(180 + 2400 * u ** 2) / SR) * u ** 2.5 * 0.4
    return norm(noise * 0.9 + sweep) * 0.55


def crowd(rng, dur, swell_to=1.0):
    n = int(dur * SR); t = tvec(n); u = t / dur
    base = bandpass(rng.standard_normal(n), 250, 3200)
    wob = bandpass(rng.standard_normal(n), 0.4, 6.0)
    wob = 0.75 + 0.25 * norm(wob)
    env = (0.18 + 0.82 * u ** 1.6) * swell_to
    return norm(base * wob * env) * 0.6


def brass(rng, freq, dur, vel=0.8):
    n = int((dur + 0.18) * SR); t = tvec(n)
    vib = 1 + 0.0028 * np.sin(2 * math.pi * 5.2 * t) * np.minimum(1, t / 0.4)
    out = np.zeros(n)
    for det in (0.9985, 1.0015):
        ph = 2 * math.pi * np.cumsum(freq * det * vib) / SR
        for h in range(1, 15):
            gate = np.clip((t - 0.004 * h) / 0.05, 0, 1)
            amp = 1.0 / h ** 1.05 * (1.0 if h <= 3 else vel)
            out += amp * gate * np.sin(h * ph)
    env = np.minimum(1, t / 0.035) * np.where(t > dur, np.exp(-(t - dur) * 22), 1.0)
    return np.tanh(norm(out) * env * 1.5) * 0.7 * (0.55 + 0.45 * vel)


def choir(rng, freq, dur):
    n = int((dur + 0.7) * SR); t = tvec(n)
    vib = 1 + 0.004 * np.sin(2 * math.pi * 5.3 * t + rng.uniform(0, 6.28))
    ph = 2 * math.pi * np.cumsum(freq * vib) / SR
    y = sum(w * np.sin((k + 1) * ph) for k, w in enumerate((1.0, 0.6, 0.8, 0.35, 0.2)))
    breath = bandpass(rng.standard_normal(n), 2000, 6500) * 0.03
    env = np.minimum(1, t / 0.5) * np.where(t > dur, np.exp(-(t - dur) * 5), 1.0)
    return norm(y + breath) * env * 0.5


def bass(rng, freq, dur):
    n = int((dur + 0.1) * SR); t = tvec(n)
    ph = 2 * math.pi * np.cumsum(np.full(n, freq)) / SR
    y = np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    env = np.minimum(1, t / 0.01) * np.where(t > dur, np.exp(-(t - dur) * 30), 1.0)
    return np.tanh(y * 1.3) * env * 0.7


def stadium_reverb(y: np.ndarray, rng, wet=0.2, seconds=1.8):
    n_ir = int(seconds * SR); t = tvec(n_ir)
    ir = np.stack([rng.standard_normal(n_ir) * np.exp(-t * 3.0) for _ in range(2)], axis=1)
    ir = np.stack([bandpass(ir[:, c], 120, 7000) for c in range(2)], axis=1)
    ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True)) + 1e-9
    size = 1 << int(math.ceil(math.log2(len(y) + n_ir)))
    out = np.zeros_like(y)
    for c in range(2):
        conv = np.fft.irfft(np.fft.rfft(y[:, c], size) * np.fft.rfft(ir[:, c], size), size)[: len(y)]
        out[:, c] = y[:, c] * (1 - wet) + conv * wet * 2.2
    return out


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def render(theme: Theme, seed: int = 0, tail: float = 2.6, hum: float = 0.006) -> np.ndarray:
    rng = np.random.default_rng(seed)
    bpm = theme.bpm * (1 + (rng.uniform(-0.02, 0.02) if seed else 0.0))
    spb = 60.0 / bpm
    bar = 4 * spb
    total = 8 * bar + tail
    mix = Mix(total)
    iv = theme.intensity

    def j():  # tiny human timing drift
        return rng.normal(0, hum) if seed else 0.0

    def off8(i):  # swung eighth position inside a beat
        return spb * (0.5 + theme.swing * 0.5) if i % 2 else 0.0

    root = theme.root
    note = lambda deg, oct_=0: midi_hz(degree_midi(root, deg, theme.mode) + 12 * oct_)

    # ---- TUNNEL (bars 0-1) -------------------------------------------------
    mix.add(crowd(rng, 4 * bar, 1.0 * theme.crowd), 0, 0.9)
    mix.add(riser(rng, 2 * bar), 0, 0.5)
    for b in range(4):  # heartbeat lub-dub
        t0 = b * 2 * spb
        g = 0.35 + 0.1 * b
        mix.add(kick(rng), t0, g * iv); mix.add(kick(rng), t0 + 0.34 * spb * 2, g * 0.7 * iv)
    mix.add(timpani(rng, midi_hz(root - 12)), bar, 0.8 * iv)
    for k in range(8):  # timpani roll into fanfare, last 2 beats of bar 1
        mix.add(timpani(rng, midi_hz(root - 12), 0.6), 2 * bar - 2 * spb + k * spb / 4,
                (0.25 + 0.08 * k) * iv, pan=-0.2)

    # ---- FANFARE (bars 2-3) -----------------------------------------------
    t = 2 * bar
    for deg, beats in theme.motif:
        mix.add(brass(rng, note(deg, 1), beats * spb * 0.92, 0.8), t + j(), 0.8, pan=0.0)
        t += beats * spb
    for b in range(2):
        for beat in (0, 2):
            tt = (2 + b) * bar + beat * spb
            mix.add(timpani(rng, midi_hz(root - 12)), tt, 0.65 * iv)
            mix.add(stomp(rng), tt, 0.35 * iv)
    mix.add(crash(rng), 2 * bar, 0.5)
    mix.add(riser(rng, bar), 3 * bar, 0.45)  # riser through bar 3 into the anthem

    # ---- ANTHEM (bars 4-7) --------------------------------------------------
    for b in range(4, 8):
        bt = b * bar
        final = b >= 6
        # stomp-stomp-clap
        if final and b == 6:
            for e in range(8):
                mix.add(stomp(rng), bt + e * spb / 2 + (off8(e) if theme.swing else 0) + j(),
                        (0.75 if e % 2 == 0 else 0.5) * iv)
        else:
            mix.add(stomp(rng), bt + j(), 0.9 * iv)
            mix.add(stomp(rng), bt + spb + j(), 0.9 * iv)
        mix.add(clap(rng), bt + 2 * spb + j(), 0.85 * iv, pan=0.1)
        if b == 7:  # snare roll on the last beat leading to the final hit
            for k in range(8):
                mix.add(snare(rng), bt + 3 * spb + k * spb / 8, (0.3 + 0.09 * k) * iv)
        # hats on the off-beats
        for e in range(8):
            mix.add(hat(rng), bt + e * spb / 2 + (off8(e) if theme.swing else 0),
                    0.22 if e % 2 else 0.12, pan=0.25 if e % 2 else -0.25)
        # sub bass pumping on the chord root
        croot = theme.prog[b - 4]
        for q in range(4):
            mix.add(bass(rng, note(croot, -1), spb * 0.85), bt + q * spb, 0.55)
        # choir pad on the chord triad
        for k, off in enumerate((0, 2, 4)):
            f = note(croot + off, 0)
            mix.add(choir(rng, f * 1.004, bar), bt, 0.28, pan=-0.55)
            mix.add(choir(rng, f * 0.996, bar), bt, 0.28, pan=0.55)
    # anthem brass (bars 4-5) and final brass (bars 6-7, octave up)
    for start_bar, octv in ((4, 1), (6, 2)):
        t = start_bar * bar
        for deg, beats in theme.motif:
            d = beats * spb * 0.92
            mix.add(brass(rng, note(deg, octv), d, 0.95), t + j(), 0.85)
            mix.add(brass(rng, note(deg + 2, octv), d, 0.8), t + j(), 0.5, pan=-0.45)
            mix.add(brass(rng, note(deg + 4, octv), d, 0.8), t + j(), 0.45, pan=0.45)
            t += beats * spb
    mix.add(crash(rng), 4 * bar, 0.6)
    mix.add(crash(rng), 6 * bar, 0.7)
    mix.add(crowd(rng, 4 * bar + tail, 1.25 * theme.crowd), 4 * bar, 0.75)

    # ---- FINAL HIT (t = 8 bars) -------------------------------------------
    tf = 8 * bar
    mix.add(crash(rng, 3.8), tf, 0.9)
    mix.add(timpani(rng, midi_hz(root - 12), 2.4), tf, 1.0 * iv)
    mix.add(stomp(rng), tf, 1.0 * iv)
    mix.add(kick(rng), tf, 0.8 * iv)
    for k, off in enumerate((0, 2, 4)):
        mix.add(brass(rng, note(off, 2), 1.6, 1.0), tf, 0.8, pan=(-0.4, 0.0, 0.4)[k])
    for k, off in enumerate((0, 4)):
        mix.add(choir(rng, note(off, 0), 2.0), tf, 0.4, pan=(-0.5, 0.5)[k])

    # ---- master -------------------------------------------------------------
    y = mix.buf
    ctx = {"sr": SR, "bpm": bpm, "sport": theme.sport, "seed": seed, "rng": rng}
    y = hooks.apply(theme.recipes, y, ctx)
    y = stadium_reverb(y, rng, wet=0.2)
    y = norm(y) * 0.8
    y = np.tanh(y * (1.5 + 0.3 * iv)) / math.tanh(1.5 + 0.3 * iv)
    fade = int(0.35 * SR)
    y[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return norm(y) * 0.89


def write_wav(path: str, y: np.ndarray) -> None:
    pcm = (np.clip(y, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# --------------------------------------------------------------------------
# Prompt -> Theme (keyword parsing; edit magic_phrases.json to extend)
# --------------------------------------------------------------------------
def load_phrases() -> dict:
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magic_phrases.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def theme_from_prompt(prompt: str, base: Theme | None = None) -> Theme:
    ph = load_phrases()
    low = prompt.lower()
    theme = base
    if theme is None:
        theme = PRESETS["football"]
        for sport, aliases in ph["sports"].items():
            if any(a in low for a in aliases):
                theme = PRESETS[sport]
                break
    m = re.search(r"(\d{2,3})\s*bpm", low)
    if m:
        theme = replace(theme, bpm=float(m.group(1)))
    m = re.search(r"\bin\s+([a-g][#b]?)\s+(major|minor)\b", low)
    if m:
        pc = NOTE_NAMES[m.group(1).upper()]
        theme = replace(theme, root=48 + pc, mode=m.group(2))
    recipes = list(theme.recipes)
    for phrase, effect in ph["phrases"].items():
        if phrase in low:
            for key in ("intensity", "crowd", "swing"):
                if key in effect:
                    theme = replace(theme, **{key: effect[key]})
            recipes += [r for r in effect.get("recipes", []) if r not in recipes]
    return replace(theme, recipes=tuple(recipes))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Legendary sports theme generator (no Suno).")
    ap.add_argument("--sport", choices=sorted(PRESETS), help="preset to render")
    ap.add_argument("--prompt", help="free-text prompt, e.g. 'legendary boxing walkout 80 bpm in A minor'")
    ap.add_argument("--seed", type=int, default=0, help="0 = exact/quantised, >0 = humanised variation")
    ap.add_argument("--endless", type=int, default=0, metavar="N", help="render N seeded variations")
    ap.add_argument("--out", default="out", help="output directory or .wav path")
    ap.add_argument("--recipes", help="python file defining register(RECIPES) for your own engine recipes")
    ap.add_argument("--recipe-names", nargs="*", default=[], help="recipe names to apply (built-in or yours)")
    ap.add_argument("--list", action="store_true", help="list presets and recipes")
    a = ap.parse_args(argv)

    if a.recipes:
        hooks.load_user_recipes(a.recipes)
    if a.list:
        for k, v in PRESETS.items():
            print(f"{k:11s} {v.bpm:5.0f} bpm  {NOTE_ROOT(v)}  {v.blurb}")
        print("recipes:", ", ".join(sorted(hooks.RECIPES)))
        return 0

    base = PRESETS.get(a.sport) if a.sport else None
    theme = theme_from_prompt(a.prompt, base) if a.prompt else (base or PRESETS["football"])
    if a.recipe_names:
        theme = replace(theme, recipes=tuple(theme.recipes) + tuple(a.recipe_names))
    if theme.sport == "football" and not a.sport and not a.prompt:
        pass

    single = a.out.lower().endswith(".wav")
    outdir = os.path.dirname(a.out) or "." if single else a.out
    os.makedirs(outdir, exist_ok=True)
    n = max(1, a.endless)
    for i in range(n):
        seed = a.seed + i if (a.endless or a.seed) else 0
        y = render(theme, seed)
        path = a.out if (single and n == 1) else os.path.join(
            outdir, f"{theme.sport}_theme_s{seed}.wav")
        write_wav(path, y)
        print(f"wrote {path}  ({len(y) / SR:.1f}s, {theme.bpm:.0f} bpm, seed {seed})")
    return 0


def NOTE_ROOT(t: Theme) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[t.root % 12]} {t.mode}"


if __name__ == "__main__":
    raise SystemExit(main())
