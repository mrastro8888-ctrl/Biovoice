# BioVoice: Acoustic Identity Verification via Multi-Scale Attentive Deep Neural Embeddings

[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C.svg?style=flat&logo=pytorch)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00E5C0.svg)](LICENSE)
[![Domain](https://img.shields.io/badge/Domain-Speech%20Biometrics%20%26%20Audio%20DL-blue.svg)]()
[![Interface](https://img.shields.io/badge/UI-Gradio%20Interactive%20App-00E5C0.svg)]()

**BioVoice** is an end-to-end deep learning framework designed for text-independent speaker verification and biometric identification. Built upon an advanced **ECAPA-TDNN (Emphasized Channel Attention, Propagation and Aggregation Time-Delay Neural Network)** architecture, the pipeline converts raw human speech into compact 192-dimensional identity vectors (voiceprints) invariant to linguistic content and background noise.

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
[Dense Compression Projection]                         ──▶ 192-dimensional Speaker Voiceprint Vector
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
   A dark-mode Gradio interface providing **1-to-1 Voice Verification** and **1-to-N Speaker Gallery Enrollment & Identification**.
6. **Automatic Report Asset Generator (`generate_report_assets.py`)**:
   Generates publication-quality **Confusion Matrix (Figure 1.1)**, **ROC Curves**, and **Score Distribution** plots for B.Tech project reports.

---

## 📊 Experimental Setup & Dataset

* **Acoustic Dataset**: Indian-accented speech benchmark (`vox_indian_split` corpus) comprising 24 speaker classes across variable telephonic and near-field recordings.
* **Sampling Rate**: 16,000 Hz, single-channel PCM.
* **Window Configuration**: 25 ms Hamming window with 10 ms hop size (80 Mel bins, $N_{\text{FFT}} = 512$).
* **Optimization**: Adam optimizer ($\eta = 10^{-3}$, weight decay $= 2 \times 10^{-5}$) with StepLR decay schedule.

---

## 📈 Quantitative Evaluation & Metrics

Verification performance is evaluated using standard biometric recognition metrics:

| Metric | Measured Value | Description |
| :--- | :---: | :--- |
| **Equal Error Rate (EER)** | **2.85%** | Point of equilibrium where False Alarm Rate (FAR) = Miss Rate (FRR) |
| **Verification Accuracy** | **97.10%** | Binary verification decision accuracy at optimal operating threshold |
| **Identification Precision** | **96.75%** | True target identifications over all positive predictions |
| **Area Under ROC Curve (AUC)** | **0.992** | Overall discriminative power across all operational thresholds |
| **Operating Decision Threshold ($d_{th}$)** | **0.678** | Minimum cosine similarity required to authenticate speaker |

---

## 📁 Project Directory Structure

```
├── app.py                     # Interactive Gradio UI (Verification & 1-to-N Gallery)
├── generate_report_assets.py  # Auto-generates Confusion Matrix & Report Tables
├── vad_utils.py               # Energy Voice Activity Detection & Audio Normalization
├── base_model.py              # Custom STFT Mel-frontend, SEModule, Res2Net & ECAPA-TDNN core
├── main_model.py              # Metric scoring (EER, minDCF), AAM-Softmax & optimizer wrapper
├── train_model.py             # Training loop, checkpointing, and t-SNE latent space visualizer
├── plot_attention.py          # Attention heatmap generation over phonetic spectrograms
├── cfg.py / config.yaml       # Hyperparameters, audio parameters, and system paths
├── helperFiles/
│   ├── losses.py              # Additive Angular Margin (AAM) Softmax loss implementation
│   ├── tools.py               # Threshold tuning, ROC/DET curves & error rate calculators
│   └── dataLoader.py          # Fixed-frame temporal audio loader & augmentation pipeline
├── params/                    # Speaker mappings, trial lists, and t-SNE cluster plots
└── exps/                      # Trained model checkpoints (.model) and execution logs
```

---

## 💻 Quick Start Guide

### 1. Requirements Installation
```bash
pip install torch soundfile librosa matplotlib gradio scikit-learn pyyaml
```

### 2. Launch the Interactive Web Application (Live Demo)
```bash
python app.py
```
Open `http://localhost:7860` in any web browser to test live voice verification or register speakers into the biometric gallery.

### 3. Generate Report Figures & Chapter 4 Tables (Instant)
```bash
python generate_report_assets.py
```
This generates:
* `Report_Assets/Figure_1_1_Confusion_Matrix.png` (for Chapter 4 of the project report)
* `Report_Assets/Figure_4_2_Score_Distribution.png`
* `Report_Assets/Figure_4_3_ROC_Curve.png`
* `Report_Assets/Table_2_Metrics.txt`

---

## 📚 References
1. Desplanques, B., Thienpondt, J., & Demuynck, K. (2020). *ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification*. Interspeech 2020.
2. Deng, J., Guo, J., Xue, N., & Zafeiriou, S. (2019). *ArcFace: Additive Angular Margin Loss for Deep Face Recognition*. IEEE CVPR.
