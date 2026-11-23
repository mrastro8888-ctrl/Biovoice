"""
BioVoice: Acoustic Preprocessing and Voice Activity Detection (VAD) Utilities
Applies energy thresholding, silence trimming, and signal normalization
without requiring any model retraining.
"""

import numpy as np
import soundfile as sf
import torch

def trim_silence_energy(waveform, sample_rate=16000, frame_length_ms=25, hop_length_ms=10, energy_threshold=0.015):
    """
    Performs Energy-based Voice Activity Detection (VAD) to strip silent frames.
    
    Args:
        waveform (np.ndarray): 1D audio signal.
        sample_rate (int): Sampling rate (default 16 kHz).
        frame_length_ms (int): Frame duration in milliseconds.
        hop_length_ms (int): Frame stride in milliseconds.
        energy_threshold (float): Energy cutoff ratio relative to signal maximum.

    Returns:
        np.ndarray: Waveform with unvoiced silence trimmed.
    """
    if len(waveform) == 0:
        return waveform

    frame_len = int(sample_rate * (frame_length_ms / 1000.0))
    hop_len = int(sample_rate * (hop_length_ms / 1000.0))

    # Compute short-time energy across frames
    num_frames = max(1, (len(waveform) - frame_len) // hop_len + 1)
    energies = []
    for i in range(num_frames):
        start = i * hop_len
        end = start + frame_len
        frame = waveform[start:end]
        energy = np.sum(frame ** 2) / float(frame_len)
        energies.append(energy)

    energies = np.array(energies)
    max_energy = np.max(energies) if len(energies) > 0 else 0.0

    if max_energy == 0:
        return waveform

    normalized_energies = energies / max_energy
    active_frame_indices = np.where(normalized_energies > energy_threshold)[0]

    if len(active_frame_indices) > 0:
        start_sample = max(0, active_frame_indices[0] * hop_len - frame_len)
        end_sample = min(len(waveform), (active_frame_indices[-1] + 1) * hop_len + frame_len)
        return waveform[start_sample:end_sample]

    return waveform


def preprocess_audio_pipeline(audio_path, target_sr=16000, max_seconds=3.0):
    """
    Loads, downmixes to mono, trims silence, rescales amplitude, and formats tensor.
    """
    audio, sr = sf.read(audio_path)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # Apply VAD
    cleaned_audio = trim_silence_energy(audio, sample_rate=sr)

    # Truncate / pad to fixed duration
    target_samples = int(target_sr * max_seconds)
    if len(cleaned_audio) < target_samples:
        cleaned_audio = np.pad(cleaned_audio, (0, target_samples - len(cleaned_audio)), mode='wrap')
    else:
        cleaned_audio = cleaned_audio[:target_samples]

    # Peak normalization
    max_val = np.max(np.abs(cleaned_audio))
    if max_val > 0:
        cleaned_audio = cleaned_audio / max_val

    return cleaned_audio, sr
