# Design spec used for this generator (written for this repo)

Goal: a short, instantly recognisable "legendary" sports entrance theme that
builds from near-silence to a stadium-wide hit, rendered offline with no
external music model (no Suno).

Emotional arc: nerves -> call to arms -> communal chant -> triumph.

| Section | Bars | Job |
|---|---|---|
| Tunnel | 0-1 | Tension: heartbeat, crowd, riser, timpani roll |
| Fanfare | 2-3 | Identity: solo brass states the motif |
| Anthem | 4-5 | Unity: stomp-stomp-clap, harmonised brass, choir, sub |
| Final | 6-7 + hit | Release: octave-up brass, driving stomps, snare roll, last hit |

Design rules: the motif is 8 beats long and singable; each sport changes
tempo, key/mode, motif, swing and crowd weight; rendering is deterministic for
seed 0 and humanised for seed > 0.
