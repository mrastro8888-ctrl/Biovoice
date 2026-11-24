"""Real evaluation of speaker-verification trials. Run from the repo root:
    python evaluate.py --data_root <folder that contains id10324\\... wav files> [--vad]
Trial file format (params/eval_list.txt): <label> <wav1> <wav2>   (1 = same speaker)
Writes real metrics + figures to Report_Assets/ (overwrites the simulated ones)."""
import argparse, os, json
import numpy as np, torch, librosa
from sklearn import metrics
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--data_root", required=True)
ap.add_argument("--trials", default="params/eval_list.txt")
ap.add_argument("--out", default="Report_Assets")
ap.add_argument("--vad", action="store_true", help="apply energy VAD from vad_utils.py")
ap.add_argument("--engine", choices=["speechbrain","own"], default="speechbrain")
ap.add_argument("--ckpt", default="exps/exp1/model_0001.model", help="own-model checkpoint (engine=own)")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

if a.engine == "speechbrain":
    from speechbrain.inference.speaker import SpeakerRecognition
    model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                            savedir="pretrained_ecapa", run_opts={"device": "cpu"})
    def encode(t): return model.encode_batch(t).squeeze().numpy()
else:  # your own 2025 checkpoint, run from the repo root that contains base_model.py
    from base_model import ECAPA_TDNN
    enc = ECAPA_TDNN(C=1024)
    sd = torch.load(a.ckpt, map_location="cpu", weights_only=True)
    sd = {k.replace("speaker_encoder.", "", 1): v for k, v in sd.items() if k.startswith("speaker_encoder.") and not k.startswith("speaker_encoder.torchfbank.")}
    print("load:", enc.load_state_dict(sd, strict=True))
    enc.eval()
    def encode(t):
        with torch.no_grad(): return enc(t, aug=False).squeeze().cpu().numpy()
if a.vad:
    from vad_utils import trim_silence_energy
_cache = {}
def emb(p):
    if p in _cache: return _cache[p]
    path = os.path.join(a.data_root, p.replace("\\", os.sep))
    w, _ = librosa.load(path, sr=16000, mono=True)
    if a.vad:
        out = trim_silence_energy(torch.tensor(w), 16000)
        out = out[0] if isinstance(out, tuple) else out
        w = np.asarray(out, dtype=np.float32).squeeze()
    with torch.no_grad():
        e = encode(torch.tensor(w).unsqueeze(0))
    _cache[p] = e / np.linalg.norm(e)
    return _cache[p]

y, s = [], []
for line in open(a.trials):
    t = line.split()
    if len(t) < 3: continue
    y.append(int(t[0])); s.append(float(np.dot(emb(t[1]), emb(t[2]))))
y, s = np.array(y), np.array(s)

fpr, tpr, thr = metrics.roc_curve(y, s)
fnr = 1 - tpr
i = np.nanargmin(np.abs(fnr - fpr)); eer = (fpr[i] + fnr[i]) / 2; th = thr[i]
auc = metrics.auc(fpr, tpr)
pred = (s >= th).astype(int)
tn, fp, fn, tp = metrics.confusion_matrix(y, pred).ravel()
def mindcf(p=0.01, cm=1, cf=1):
    c = cm * fnr * p + cf * fpr * (1 - p); return float(np.min(c) / min(cm * p, cf * (1 - p)))
res = dict(n_trials=len(y), engine=a.engine, vad=a.vad, threshold=float(th), eer_pct=float(eer * 100), auc=float(auc),
           accuracy_pct=float(metrics.accuracy_score(y, pred) * 100),
           precision_pct=float(metrics.precision_score(y, pred) * 100),
           recall_pct=float(metrics.recall_score(y, pred) * 100),
           f1_pct=float(metrics.f1_score(y, pred) * 100), minDCF=mindcf(), TP=int(tp), FN=int(fn), TN=int(tn), FP=int(fp),
           genuine_mean=float(s[y==1].mean()), genuine_std=float(s[y==1].std()),
           impostor_mean=float(s[y==0].mean()), impostor_std=float(s[y==0].std()))
tag = a.engine + ("_vad" if a.vad else "_novad")
json.dump(res, open(f"{a.out}/real_metrics_{tag}.json", "w"), indent=2); print(json.dumps(res, indent=2))

plt.figure(figsize=(5,4.5)); plt.imshow([[tn, fp],[fn, tp]], cmap="Blues")
for (r,c),v in {(0,0):tn,(0,1):fp,(1,0):fn,(1,1):tp}.items(): plt.text(c,r,v,ha="center",va="center",fontsize=16)
plt.xticks([0,1],["Impostor","Target"]); plt.yticks([0,1],["Impostor","Target"])
plt.xlabel("Predicted"); plt.ylabel("Actual"); plt.title(f"Confusion matrix (d_th={th:.3f})")
plt.tight_layout(); plt.savefig(f"{a.out}/confusion_matrix_{tag}.png", dpi=300); plt.close()
plt.figure(figsize=(8,4.5)); plt.hist(s[y==0],bins=30,alpha=.7,density=True,label="Impostor"); plt.hist(s[y==1],bins=30,alpha=.7,density=True,label="Genuine")
plt.axvline(th,ls="--",c="k",label=f"EER threshold ({th:.3f})"); plt.xlabel("Cosine similarity"); plt.ylabel("Density"); plt.legend()
plt.tight_layout(); plt.savefig(f"{a.out}/score_distribution_{tag}.png", dpi=300); plt.close()
plt.figure(figsize=(5,4.5)); plt.plot(fpr,tpr,label=f"AUC={auc:.3f}"); plt.plot([0,1],[0,1],"--"); plt.scatter(fpr[i],tpr[i],c="k",label=f"EER={eer*100:.2f}%")
plt.xlabel("FAR"); plt.ylabel("TAR (1-FRR)"); plt.legend(); plt.tight_layout(); plt.savefig(f"{a.out}/roc_{tag}.png", dpi=300); plt.close()
