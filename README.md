# BioVoice: Acoustic Identity Verification via Multi-Scale Attentive Deep Neural Embeddings

[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C.svg?style=flat&logo=pytorch)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00E5C0.svg)](LICENSE)
[![Domain](https://img.shields.io/badge/Domain-Speech%20Biometrics%20%26%20Audio%20DL-blue.svg)]()
[![Interface](https://img.shields.io/badge/UI-Gradio%20Interactive%20App-00E5C0.svg)]()

**BioVoice** is an end-to-end deep learning framework designed for text-independent speaker verification and biometric identification. Built upon an advanced **ECAPA-TDNN (Emphasized Channel Attention, Propagation and Aggregation Time-Delay Neural Network)** architecture, the pipeline converts raw human speech into compact 256-dimensional identity vectors (voiceprints) via fc6 (3072 -> 256); 192-dimensional embeddings belong to the SpeechBrain reference baseline.

---

## 🏛️ System Architecture

```
Raw Waveform (16 kHz)
       │
       ▼
[Phase 1: Energy-based Voice Activity Detection (VAD)] ──▶ Silence Stripping
       │
       ▼
[Phase 2: Custom Mel-Filterbank Layer]                 ──▶ 80-channel log Mel-Spectrograms (STFT)
       │
       ▼
[Conv1D + ReLU + BatchNorm Front-End]
       │
       ▼
[SE-Res2Block Stage 1] ── (Scale = 8, Dilation = 2)   ──▶ Multi-receptive field temporal modeling
       │
       ▼
[SE-Res2Block Stage 2] ── (Scale = 8, Dilation = 3)   ──▶ Channel-wise Squeeze-and-Excitation
       │
       ▼
[SE-Res2Block Stage 3] ── (Scale = 8, Dilation = 4)   ──▶ Feature aggregation across frames
       │
       ▼
[Attentive Statistics Pooling]                         ──▶ Frame-level importance weighting (Mean + Std Dev)
       │
       ▼
[Dense Compression Projection]                         ──▶ 256-dimensional Voiceprint Vector (fc6: 3072->256; SpeechBrain: 192-d)
       │
       ▼
[Metric Learning: AAM-Softmax / Cosine Metric]         ──▶ Impostor Rejection & Target Verification
```

---

## 🚀 Key Modules & Contributions

1. **Inference-Time Voice Activity Detection (`vad_utils.py`)**:
   Strips unvoiced/silent frames from incoming audio without requiring model retraining, preventing silence from diluting pooled representations.
2. **Mathematical Mel Frontend (`base_model.py`)**:
   Hardware-accelerated custom PyTorch Short-Time Fourier Transform (STFT) with custom triangular Mel filter-bank calculation ($f_{\text{min}} = 20\,\text{Hz}$, $f_{\text{max}} = 7600\,\text{Hz}$).
3. **SE-Res2Net Dilated Blocks (`base_model.py`)**:
   Multi-scale feature extraction at diverse temporal granularities, coupled with channel recalibration to emphasize speaker-distinctive formants.
4. **Attentive Statistical Pooling (`base_model.py`)**:
   Self-attention mechanism weighting voiced phonetic segments to compute frame-level mean and standard deviation.
5. **Interactive Web Interface (`app.py`)**:
   A dark-mode Gradio interface providing **1-to-1 Voice Verification** and **1-to-N Speaker Gallery Enrollment & Identification** running on localhost.
6. **Real Evaluation Suite (`evaluate.py` & `make_trials.py`)**:
   Generates balanced evaluation trials and executes real verification benchmarks, outputting empirical JSON metrics and plots to `Report_Assets/`.

---

## 📊 Experimental Setup & Dataset

* **Evaluation Benchmark**: LibriSpeech test-clean corpus, formatted into 240 balanced pairwise trials across 40 speakers (120 genuine pairs, 120 impostor pairs) using `make_trials.py`.
* **Custom Model Training (2025 Checkpoint)**: Trained on 24 VoxCeleb1-style speakers' single-word clips using AAM-Softmax ($m = 0.20$, $s = 30$, channel capacity $C = 1024$, 256-dimensional embedding, batch size 128, Adam optimizer).
* **Evaluation Regime**: Cross-domain test (isolated word utterance training vs. continuous read audiobook speech).
* **Audio Format**: 16,000 Hz, single-channel monophonic PCM.
* **Window Configuration**: 25 ms Hamming window with 10 ms hop size (80 Mel bins, $N_{\text{FFT}} = 512$).

---

## 📈 Quantitative Evaluation & Empirical Metrics

Empirical verification performance measured on the 240 LibriSpeech trial pairs (`Report_Assets/real_metrics_*.json`):

| Evaluated Architecture | Frontend VAD | Embedding Dim | Threshold ($d_{th}$) | Accuracy (%) | Precision (%) | Recall (%) | EER (%) | minDCF |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Custom Checkpoint (2025, 1-epoch)** | No | 256 | 0.933 | 72.92% | 72.73% | 73.33% | 27.08% | 0.825 |
| **Custom Checkpoint (2025, 1-epoch)** | With VAD | 256 | 0.876 | 70.00% | 70.00% | 70.00% | 30.00% | 0.742 |
| **Pretrained SpeechBrain ECAPA-TDNN** | No | 192 | 0.309 | 98.33% | 97.54% | 99.17% | 1.67% | 0.050 |
| **Pretrained SpeechBrain ECAPA-TDNN** | With VAD | 192 | 0.303 | 96.67% | 96.67% | 96.67% | 3.33% | 0.058 |

---

## ⚠️ System Limitations

1. **Small Test Set**: Evaluated on 240 structured trials across 40 human speakers from LibriSpeech test-clean.
2. **Cross-Domain Evaluation**: Model was trained on isolated single-word clips, while evaluation evaluated continuous read speech.
3. **1-Epoch Custom Checkpoint**: The custom model represents an initial single-epoch training checkpoint exhibiting wider cosine score overlap.
4. **Demo Pretrained Weights**: The localhost interactive web demo (`app.py`) utilizes pre-trained SpeechBrain VoxCeleb weights to provide low-error real-time inference.
5. **No Anti-Spoofing**: The system does not currently incorporate presentation attack detection against synthetic deepfakes or replay attacks.

---

## 📁 Project Directory Structure

```
├── app.py                     # Interactive Gradio UI (runs on http://localhost:7860)
├── evaluate.py                # Empirical evaluation on audio trials (writes real_metrics_*.json)
├── make_trials.py             # Generates balanced trial lists from audio directories
├── vad_utils.py               # Energy Voice Activity Detection & Audio Normalization
├── base_model.py              # Custom STFT Mel-frontend, SEModule, Res2Net & ECAPA-TDNN core (256-D)
├── main_model.py              # Metric scoring (EER, minDCF), AAM-Softmax & optimizer wrapper
├── train_model.py             # Training loop, checkpointing, and latent space visualizer
├── plot_attention.py          # Attention heatmap generation over phonetic spectrograms
├── build_word_report.py       # Automated BIT Mesra Minor Project Word report generator
├── BioVoice_Minor_Project_Report.docx # Official B.Tech Minor Project Report
├── LICENSE                    # MIT License file
├── cfg.py / config.yaml       # Hyperparameters, audio parameters, and system paths
├── requirements.txt           # Python dependency requirements
├── helperFiles/
│   ├── losses.py              # Additive Angular Margin (AAM) Softmax loss implementation
│   ├── tools.py               # Threshold tuning, ROC/DET curves & error rate calculators
│   └── dataLoader.py          # Fixed-frame temporal audio loader & augmentation pipeline
├── params/                    # Speaker mappings, trial lists, and t-SNE cluster plots
├── Results/                   # Real attention spectrograms and output plots
├── Report_Assets/             # Output folder for real_metrics_*.json and real evaluation plots
└── exps/                      # Trained model checkpoints (.model) and execution logs
```

---

## 💻 Quick Start Guide

### 1. Requirements Installation
```bash
pip install -r requirements.txt
```

### 2. Launch the Interactive Web Application (Localhost)
```bash
python app.py
```
Open `http://localhost:7860` in any web browser to test voice verification or register speakers into the local biometric gallery.

### 3. Run Empirical Evaluation on Trials
```bash
python evaluate.py --data_root <path_to_audio_dataset> --trials params/eval_list.txt
```
This computes real metrics and outputs:
* `Report_Assets/real_metrics_<engine>.json` (Measured EER, minDCF, precision, recall, AUC, confusion matrix)
* Real evaluation figures (`roc_*.png`, `score_distribution_*.png`, `confusion_matrix_*.png`)

---

## 📚 References
1. Desplanques, B., Thienpondt, J., & Demuynck, K. (2020). *ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification*. Interspeech 2020.
2. Deng, J., Guo, J., Xue, N., & Zafeiriou, S. (2019). *ArcFace: Additive Angular Margin Loss for Deep Face Recognition*. IEEE CVPR.
