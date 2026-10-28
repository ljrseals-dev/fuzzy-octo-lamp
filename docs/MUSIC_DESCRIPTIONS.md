# Music descriptions

All themes share one 8-bar arrangement in 4/4 followed by a ring-out tail.
Tempo, key, motif, swing and crowd weight change per sport. Scale degrees are
0-based (0 = tonic). "Seed 0" renders are exact; seeds > 0 add small timing
drift, tempo jitter (+/-2%) and variation.

## Shared arrangement

| Bars | Section | What you hear |
|---|---|---|
| 0-1 | **Tunnel** | Quiet lub-dub heartbeat kicks that grow each beat. A crowd bed fades up from far away. A noise-and-sweep riser climbs across both bars. A single low timpani hit on bar 1, then a 16th-note timpani roll crescendos through the last two beats. |
| 2-3 | **Fanfare** | Solo brass states the 8-beat motif one octave above the tonic. Timpani on beats 1 and 3 with a soft stomp doubling. Crash on bar 2. A riser through bar 3 leads into the anthem. |
| 4-5 | **Anthem** | Stomp, stomp, clap (rest) every bar. Brass plays the motif in parallel thirds and fifths, panned left and right. Choir pads sustain the triad of each bar's chord (progression per sport). Pumping sub bass on quarter notes. Off-beat hats. Crash on bar 4 and a bigger crowd bed. |
| 6-7 | **Final** | Brass jumps an octave. Bar 6 is driving eighth-note stomps; bar 7 returns to stomp-stomp-clap and ends with a snare roll on the last beat. Crash on bar 6. |
| 8 | **Final hit** | Long crash, timpani, stomp and kick together with a sustained brass triad and choir. Stadium reverb tail, 0.35 s fade. |

Mastering: light stadium-style convolution reverb (synthetic impulse response),
tanh bus saturation scaled by `intensity`, peak-normalised to about -1 dBFS.

## Instruments (all synthesized)

- **Stomp**: pitch-dropping sine body + low noise thud + short slap.
- **Clap**: three tight noise bursts plus a short tail.
- **Timpani**: pitch-bent sine with a fifth overtone and a mallet thump.
- **Brass**: two detuned additive voices (14 harmonics) whose upper harmonics
  arrive slightly after the attack, with delayed vibrato.
- **Choir**: detuned vibrato partials with a breath-noise layer.
- **Crowd**: band-limited noise with slow random swells.
- **Sub bass**: sine plus two soft harmonics, saturated.

## Sport variants (samples in `samples/`)

| File | Length | Tempo | Key | Motif (degree, beats) | Chord roots, bars 4-7 | Character |
|---|---|---|---|---|---|---|
| `football_theme_s0.wav` | 21.1 s | 104 | D minor | (0,1)(0,.5)(2,.5)(4,1.5)(2,.5)(4,1)(7,1)(5,2) | i, VI, VII, i | Gridiron stadium roar. Heavy stomps, a rising minor motif that climbs to the octave and settles on the sixth. |
| `basketball_theme_s0.wav` | 23.5 s | 92 | F minor | (0,.5)(0,.5)(3,1)(2,.5)(0,.5)(4,1.5)(3,.5)(2,.5)(7,2.5) | i, iv, VI, VII | Arena swagger. Swing 0.28 on hats and final-bar stomps, syncopated hook that resolves on a long octave. |
| `soccer_theme_s0.wav` | 18.6 s | 120 | G major | (0,1)(0,1)(2,1)(4,1)(4,1)(2,1)(0,2) | I, V, vi, IV | Terrace chant. Evenly spaced, singable motif; crowd weight 1.2. |
| `boxing_theme_s0.wav` | 25.5 s | 84 | C minor | (0,2)(0,1)(3,1)(4,2)(3,1)(0,1) | i, i, VI, VII | Ring walk. Slowest tempo, long tonic hits, intensity 1.15 for extra drum weight. |
| `baseball_theme_s0.wav` | 20.4 s | 108 | C major | (0,1)(2,1)(4,1)(7,1)(4,1)(2,1)(0,2) | I, IV, V, I | Ballpark charge. Rising major arpeggio up to the octave and back; light swing 0.12. |
| `prompt_demo_basketball_96bpm_Aminor.wav` | 22.5 s | 96 (+/-2% at seed 7) | A minor | basketball motif | basketball progression | Made with `--prompt "legendary basketball walkout, 96 bpm, in A minor, stadium roar, stereo cat, endless" --seed 7`: intensity 1.2, crowd 1.4, plus `haas_cut` and `endless_drift` recipes. |

Chord roots are scale degrees relative to each sport's tonic (Roman numerals
use that key's own scale).
