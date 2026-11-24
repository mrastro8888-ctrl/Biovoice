"""Build a balanced trial list from a folder laid out as <root>/<speaker>/**/<utt>.wav|.flac
Usage: python make_trials.py --root DATA --n 240 --out params/my_trials.txt
Writes lines: <label> <relpath1> <relpath2>   (1 = same speaker). Then:
    python evaluate.py --data_root DATA --trials params/my_trials.txt [--vad]"""
import argparse, os, random, itertools
ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True); ap.add_argument("--n", type=int, default=240)
ap.add_argument("--out", default="params/my_trials.txt"); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args(); random.seed(a.seed)
spk = {}
for d, _, fs in os.walk(a.root):
    for f in fs:
        if f.lower().endswith((".wav", ".flac")):
            rel = os.path.relpath(os.path.join(d, f), a.root)
            spk.setdefault(rel.split(os.sep)[0], []).append(rel)
spk = {k: v for k, v in spk.items() if len(v) >= 2}
assert len(spk) >= 2, "need >=2 speakers with >=2 clips each"
half = a.n // 2; names = list(spk); trials = set()
while len(trials) < half:
    s = random.choice(names); x, y = random.sample(spk[s], 2); trials.add((1, x, y))
while len(trials) < 2 * half:
    s1, s2 = random.sample(names, 2); trials.add((0, random.choice(spk[s1]), random.choice(spk[s2])))
trials = sorted(trials, key=lambda t: random.random())
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
open(a.out, "w").write("\n".join(f"{l} {x} {y}" for l, x, y in trials) + "\n")
print(f"{len(spk)} speakers, {len(trials)} trials -> {a.out}")
