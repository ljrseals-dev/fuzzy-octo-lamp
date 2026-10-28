# Legendary Sports Theme Generator

A pure-Python (numpy only) generator for stadium-sized sports entrance themes.
No Suno, no sample packs, no network, no ML model: stomps, claps, timpani,
brass, choir, crowd, risers and reverb are all synthesized, then written as
16-bit stereo WAV.

## Quick start

```bash
pip install -r requirements.txt
python legendary_sports_theme.py --sport football
python legendary_sports_theme.py --prompt "legendary boxing walkout, 80 bpm, in A minor, stadium roar"
python legendary_sports_theme.py --sport soccer --endless 4 --seed 7   # 4 variations
python legendary_sports_theme.py --list
python tests/test_smoke.py
```

Output goes to `out/` (or `--out path.wav`). Presets: football, basketball,
soccer, boxing, baseball.

## What's in the repo

| Path | Purpose |
|---|---|
| `legendary_sports_theme.py` | Synth, arranger, prompt parser, CLI |
| `engine_hooks.py` | Recipe registry + loader for your own Endless Engine / Stereo Cat code |
| `magic_phrases.json` | Prompt phrases that tweak intensity, crowd, swing and recipes |
| `samples/` | Six rendered demos (about 20 s each) |
| `docs/MUSIC_DESCRIPTIONS.md` | Section-by-section and per-sport descriptions of the music |
| `docs/ENDLESS_ENGINE_INTEGRATION.md` | How to plug in your real recipes and phrases |
| `docs/GITHUB_PUSH.md` | Publishing steps |
| `prompts/` | Design spec, and a slot for the X-post prompt |
| `tests/test_smoke.py` | Basic checks (motif length, determinism, prompt parsing) |

## Known gaps (please read)

- **The X-post prompt is not included.** X blocked automated access, so
  `prompts/x_post_prompt.md` is a paste-in placeholder. The arrangement here is
  my own design (`prompts/legendary_sports_theme_spec.md`).
- **The Endless Engine / Stereo Cat code is not included.** The built-in
  recipes and the phrases in `magic_phrases.json` are generic placeholders;
  see `docs/ENDLESS_ENGINE_INTEGRATION.md` to swap in the real ones.
- Sounds are synthesized, so expect a stylized, game-like result rather than
  a recorded orchestra.

## License

MIT (see `LICENSE`).
