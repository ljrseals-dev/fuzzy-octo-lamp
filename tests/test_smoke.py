import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import legendary_sports_theme as lst


def test_motifs_total_eight_beats():
    for name, th in lst.PRESETS.items():
        assert abs(sum(b for _, b in th.motif) - 8.0) < 1e-9, name


def test_render_is_finite_and_deterministic():
    th = lst.PRESETS["soccer"]
    a, b = lst.render(th, 0), lst.render(th, 0)
    assert np.isfinite(a).all() and a.shape[1] == 2
    assert np.allclose(a, b)
    assert np.abs(a).max() <= 0.9


def test_prompt_parsing():
    th = lst.theme_from_prompt("legendary boxing walkout 80 bpm in A minor, stereo cat")
    assert th.sport == "boxing" and th.bpm == 80 and th.root % 12 == 9 and th.mode == "minor"
    assert "haas_cut" in th.recipes


if __name__ == "__main__":
    test_motifs_total_eight_beats(); test_render_is_finite_and_deterministic(); test_prompt_parsing()
    print("ok")
