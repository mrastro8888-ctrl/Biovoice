"""
BioVoice: Deep Acoustic Biometric Authentication System
Interactive Multi-Mode Verification & Identification Web Interface (localhost)

Key Architecture & Processing:
1. Automatic Audio Resampling: Resamples input audio from browser mic / files to 16 kHz mono.
2. Deep ECAPA-TDNN Engine:
   - Active Engine: SpeechBrain ECAPA-TDNN (pretrained on VoxCeleb, 192-d embeddings)
   - Custom Model Architecture: BioVoice ECAPA-TDNN in base_model.py / main_model.py (256-d embeddings via fc6: 3072 -> 256)
3. Zero Simulation: Real inference over real audio spectrograms.
"""

import os
import json
import torch
import numpy as np
import librosa
import soundfile as sf
import gradio as gr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch.nn.functional as F

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[BioVoice] Compute device: {device}")

# ──────────────────────────────────────────────────────────────────────────────
# 1. MODEL ENGINE INITIALIZATION
# ──────────────────────────────────────────────────────────────────────────────
sb_model = None
local_encoder = None
ENGINE_MODE = "none"
ENGINE_DISPLAY_NAME = "None"
ENABLE_ACOUSTIC_FALLBACK = False  # Explicit off-by-default flag

# A. Load official pre-trained SpeechBrain ECAPA-TDNN (VoxCeleb, 192-d embeddings)
try:
    from speechbrain.inference.speaker import SpeakerRecognition
    print("[BioVoice] Initializing SpeechBrain ECAPA-TDNN (pretrained on VoxCeleb)...")
    sb_model = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb",
        run_opts={"device": str(device)}
    )
    ENGINE_MODE = "speechbrain_ecapa"
    ENGINE_DISPLAY_NAME = "SpeechBrain ECAPA-TDNN pretrained on VoxCeleb"
    print(f"[BioVoice] Active Engine: {ENGINE_DISPLAY_NAME}")
except Exception as e:
    print(f"[BioVoice] SpeechBrain model not available ({e}). Checking local checkpoints...")

# B. Try loading local custom checkpoint if available (256-d embeddings)
if ENGINE_MODE == "none":
    from base_model import ECAPA_TDNN
    local_encoder = ECAPA_TDNN(C=1024).to(device)
    CHECKPOINT_PATHS = [
        "exps/exp1/model_0001.model",
        "exps/exp1/model_0015.model",
        "exps/exp1/best_model.model",
    ]
    for ckpt in CHECKPOINT_PATHS:
        if os.path.exists(ckpt):
            try:
                st = torch.load(ckpt, map_location=device)
                new_st = {}
                # Strip prefix if saved as speaker_encoder.*
                for k, v in st.items():
                    if k.startswith("speaker_encoder."):
                        new_st[k.replace("speaker_encoder.", "", 1)] = v
                    else:
                        new_st[k] = v
                local_encoder.load_state_dict(new_st, strict=False)
                local_encoder.eval()
                ENGINE_MODE = "local_checkpoint"
                ENGINE_DISPLAY_NAME = f"BioVoice Custom ECAPA-TDNN (Checkpoint: {os.path.basename(ckpt)}, 256-D)"
                print(f"[BioVoice] Loaded local trained checkpoint: {ckpt}")
                break
            except Exception as err:
                print(f"[BioVoice] Failed loading {ckpt}: {err}")

# C. Off-by-default fallback check (Never present fallback as ECAPA)
if ENGINE_MODE == "none":
    if ENABLE_ACOUSTIC_FALLBACK:
        ENGINE_MODE = "acoustic_formant_fallback"
        ENGINE_DISPLAY_NAME = "Acoustic Feature Fallback (Pitch/Formants - NOT ECAPA)"
        print(f"[BioVoice] WARNING: Running with {ENGINE_DISPLAY_NAME}")
    else:
        raise RuntimeError(
            "No deep neural ECAPA-TDNN model available! Please install speechbrain "
            "('pip install speechbrain') or ensure a valid checkpoint exists in exps/exp1/."
        )

GALLERY_DB_PATH = "params/enrolled_speakers.json"
os.makedirs("params", exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# 2. AUDIO PREPROCESSING & EMBEDDING EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────
def load_and_preprocess_audio(audio_path, target_sr=16000):
    """
    Loads audio and resamples 44.1k/48k browser mic input to 16 kHz mono.
    Trims silence using energy threshold so silence does not corrupt speaker identity.
    """
    audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    # Trim silence (energy cutoff top_db = 22)
    trimmed_audio, _ = librosa.effects.trim(audio, top_db=22)
    if len(trimmed_audio) > target_sr * 0.5:
        audio = trimmed_audio
    # Peak amplitude normalization
    max_amp = np.max(np.abs(audio))
    if max_amp > 0:
        audio = audio / max_amp
    return audio, target_sr


def extract_speaker_embedding(audio_path):
    """
    Extracts a normalized acoustic voiceprint vector.
    - SpeechBrain ECAPA-TDNN: 192-d embedding vector.
    - Custom BioVoice ECAPA-TDNN (base_model.py): 256-d embedding vector (fc6: 3072 -> 256).
    """
    audio, sr = load_and_preprocess_audio(audio_path, target_sr=16000)

    if ENGINE_MODE == "speechbrain_ecapa":
        # SpeechBrain Deep ECAPA-TDNN (192-d)
        wav_tensor = torch.FloatTensor(audio).to(device)
        with torch.no_grad():
            emb = sb_model.encode_batch(wav_tensor.unsqueeze(0))
            emb = F.normalize(emb.squeeze(0), p=2, dim=1)
        return emb, audio, sr

    elif ENGINE_MODE == "local_checkpoint":
        # Custom BioVoice ECAPA-TDNN (256-d from base_model.py)
        target_len = 200 * 160 + 240
        if len(audio) < target_len:
            audio_padded = np.pad(audio, (0, target_len - len(audio)), mode="wrap")
        else:
            audio_padded = audio[:target_len]
        wav_tensor = torch.FloatTensor(audio_padded).unsqueeze(0).to(device)
        with torch.no_grad():
            emb = local_encoder(wav_tensor)
            emb = F.normalize(emb, p=2, dim=1)
        return emb, audio, sr

    elif ENGINE_MODE == "acoustic_formant_fallback" and ENABLE_ACOUSTIC_FALLBACK:
        # Explicit fallback only if flag is explicitly turned True
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=32)
        spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        
        feats = np.concatenate([
            np.mean(mfccs, axis=1),
            np.std(mfccs, axis=1),
            np.mean(spectral_contrast, axis=1),
            np.std(spectral_contrast, axis=1),
            np.mean(chroma, axis=1),
            np.std(chroma, axis=1)
        ])
        emb_tensor = torch.FloatTensor(feats).unsqueeze(0).to(device)
        emb = F.normalize(emb_tensor, p=2, dim=1)
        return emb, audio, sr

    else:
        raise RuntimeError("No active neural speaker recognition engine configured.")


def compute_spectrogram(audio, sr):
    """Renders acoustic Mel-spectrogram image for the UI."""
    fig, ax = plt.subplots(figsize=(6, 2.3), facecolor="#0e171b")
    ax.set_facecolor("#0e171b")
    ax.specgram(audio, NFFT=512, Fs=sr, noverlap=256, cmap="viridis")
    ax.axis("off")
    plt.tight_layout(pad=0)
    fig.canvas.draw()
    try:
        rgba = np.asarray(fig.canvas.buffer_rgba())
        img = rgba[:, :, :3]
    except AttributeError:
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    plt.close(fig)
    return img


# ──────────────────────────────────────────────────────────────────────────────
# 3. VERIFICATION & IDENTIFICATION LOGIC
# ──────────────────────────────────────────────────────────────────────────────
def verify_pair(audio_ref, audio_test, threshold):
    if not audio_ref or not audio_test:
        return "⚠️ Please upload or record both audio samples.", None, None, 0.0

    emb1, raw1, sr1 = extract_speaker_embedding(audio_ref)
    emb2, raw2, sr2 = extract_speaker_embedding(audio_test)

    # Cosine similarity
    cosine_sim = torch.mm(emb1, emb2.T).item()
    
    # Confidence mapping based on cosine similarity
    confidence = max(0.0, min(100.0, ((cosine_sim - 0.20) / 0.65) * 100))

    is_verified = cosine_sim >= threshold
    status_text = "AUTHENTICATED: SAME SPEAKER" if is_verified else "REJECTED: DIFFERENT SPEAKERS"
    accent_color = "#39ff8a" if is_verified else "#ff3d55"
    badge_icon = "✅" if is_verified else "🚫"

    result_html = f"""
    <div style="padding:16px; border-radius:12px; background:#101a20; border:1.5px solid {accent_color}; text-align:center;">
        <h2 style="color:{accent_color}; margin:0; font-family:'Segoe UI', sans-serif;">{badge_icon} {status_text}</h2>
        <p style="color:#cce8e4; margin:10px 0 4px; font-size:1.15rem;">
            Cosine Similarity: <b style="color:{accent_color};">{cosine_sim:.4f}</b> &nbsp;|&nbsp; 
            Biometric Confidence: <b>{confidence:.1f}%</b>
        </p>
        <p style="color:#608080; margin:0; font-size:0.85rem;">
            Decision Threshold (d_th): {threshold:.2f} &nbsp;|&nbsp; 
            Active Engine: <b>{ENGINE_DISPLAY_NAME}</b>
        </p>
    </div>
    """

    spec1 = compute_spectrogram(raw1, sr1)
    spec2 = compute_spectrogram(raw2, sr2)

    return result_html, spec1, spec2, round(confidence, 1)


def enroll_speaker(name, audio_path):
    if not name or not audio_path:
        return "⚠️ Provide both a speaker name and an audio recording."
    
    emb, _, _ = extract_speaker_embedding(audio_path)
    emb_list = emb.cpu().squeeze().tolist()

    db = {}
    if os.path.exists(GALLERY_DB_PATH):
        try:
            with open(GALLERY_DB_PATH, "r") as f:
                db = json.load(f)
        except Exception:
            db = {}

    db[name.strip()] = emb_list
    with open(GALLERY_DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

    return f"✅ Enrolled '{name}'. Gallery database now has {len(db)} speaker profiles."


def identify_speaker(audio_path, threshold):
    if not audio_path:
        return "⚠️ Provide an audio sample to identify."

    if not os.path.exists(GALLERY_DB_PATH):
        return "⚠️ No speakers enrolled yet. Enroll at least one profile first."

    with open(GALLERY_DB_PATH, "r") as f:
        db = json.load(f)

    if not db:
        return "⚠️ Database is empty. Enroll a speaker first."

    query_emb, _, _ = extract_speaker_embedding(audio_path)

    best_match = None
    best_score = -1.0

    for speaker_name, vec in db.items():
        stored_emb = torch.FloatTensor(vec).unsqueeze(0).to(device)
        score = torch.mm(query_emb, stored_emb.T).item()
        if score > best_score:
            best_score = score
            best_match = speaker_name

    confidence = max(0.0, min(100.0, ((best_score - 0.20) / 0.65) * 100))

    if best_score >= threshold:
        return f"""
        <div style="padding:14px; border-radius:10px; background:#101a20; border:1.5px solid #39ff8a; text-align:center;">
            <h3 style="color:#39ff8a; margin:0;">🎯 Speaker Identified: {best_match}</h3>
            <p style="color:#d8ecea; margin:6px 0 0;">Match Score: <b>{best_score:.4f}</b> (Confidence: <b>{confidence:.1f}%</b>)</p>
            <p style="color:#608080; margin:4px 0 0; font-size:0.8rem;">Engine: {ENGINE_DISPLAY_NAME}</p>
        </div>
        """
    else:
        return f"""
        <div style="padding:14px; border-radius:10px; background:#101a20; border:1.5px solid #ff3d55; text-align:center;">
            <h3 style="color:#ff3d55; margin:0;">❓ Unknown Impostor Voice</h3>
            <p style="color:#d8ecea; margin:6px 0 0;">Closest: {best_match} (Score: {best_score:.4f} < Threshold {threshold:.2f})</p>
            <p style="color:#608080; margin:4px 0 0; font-size:0.8rem;">Engine: {ENGINE_DISPLAY_NAME}</p>
        </div>
        """


# ──────────────────────────────────────────────────────────────────────────────
# 4. GRADIO INTERFACE LAYOUT
# ──────────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
body { background-color: #070c10; font-family: 'DM Sans', sans-serif; }
.gradio-container { max-width: 980px !important; margin: auto; }
"""

with gr.Blocks(title="BioVoice - Biometric Verification") as demo:
    gr.HTML(f"""
    <style>{CUSTOM_CSS}</style>
    <div style="text-align:center; padding: 18px 0 10px;">
        <h1 style="color:#00e5c0; font-family:'Segoe UI', sans-serif; margin-bottom:4px;">🎙️ BioVoice Biometric Security System</h1>
        <p style="color:#7fa89f; font-size:0.95rem; margin:0 0 8px 0;">
            Acoustic Identity Verification & Impostor Rejection Engine
        </p>
        <div>
            <span style="display:inline-block; padding: 4px 14px; border-radius: 16px; background: #16242c; border: 1px solid #00e5c0; color: #00e5c0; font-size: 0.88rem; font-weight: 600;">
                Active Engine: {ENGINE_DISPLAY_NAME}
            </span>
        </div>
    </div>
    """)

    with gr.Tabs():
        # TAB 1: 1-to-1 Verification
        with gr.TabItem("🔍 1-to-1 Speaker Verification"):
            gr.Markdown("Upload or record two voice samples to verify whether they originate from the same human speaker.")
            with gr.Row():
                with gr.Column():
                    audio_ref = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Reference Speaker Profile")
                    spec_1 = gr.Image(label="Reference Acoustic Spectrogram", interactive=False)
                with gr.Column():
                    audio_test = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Probe Audio Sample")
                    spec_2 = gr.Image(label="Probe Acoustic Spectrogram", interactive=False)

            thresh = gr.Slider(minimum=0.40, maximum=0.85, value=0.62, step=0.02, label="Verification Decision Threshold (d_th)")
            btn_verify = gr.Button("🛡️ Verify Speaker Identity", variant="primary")

            out_html = gr.HTML()
            conf_bar = gr.Number(label="Biometric Confidence Index (%)")

            btn_verify.click(
                fn=verify_pair,
                inputs=[audio_ref, audio_test, thresh],
                outputs=[out_html, spec_1, spec_2, conf_bar]
            )

        # TAB 2: 1-to-N Gallery
        with gr.TabItem("👥 1-to-N Enrollment & Identification"):
            gr.Markdown("Register voiceprints into a secure gallery, then identify unknown incoming audio against enrolled profiles.")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Step 1: Enroll a New Speaker")
                    enroll_name = gr.Textbox(placeholder="e.g. Student 1 / Professor", label="Speaker Identity Label")
                    enroll_audio = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Enrollment Voice Sample")
                    btn_enroll = gr.Button("➕ Register to Gallery", variant="secondary")
                    enroll_status = gr.Markdown()
                    btn_enroll.click(fn=enroll_speaker, inputs=[enroll_name, enroll_audio], outputs=[enroll_status])

                with gr.Column():
                    gr.Markdown("### Step 2: Identify an Unknown Voice")
                    query_audio = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Unknown Probe Voice")
                    id_thresh = gr.Slider(minimum=0.40, maximum=0.85, value=0.62, step=0.02, label="Identification Confidence Threshold")
                    btn_id = gr.Button("🔎 Search Voice Gallery", variant="primary")
                    id_result = gr.HTML()
                    btn_id.click(fn=identify_speaker, inputs=[query_audio, id_thresh], outputs=[id_result])

if __name__ == "__main__":
    demo.launch()
