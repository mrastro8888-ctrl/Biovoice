"""
Generates publication-quality technical diagrams for the BioVoice project report:
- Figure 1.1: Conceptual Paradigm of Text-Independent Acoustic Biometric Verification
- Figure 1.2: Geodesic Hyperspherical Decision Boundary of AAM-Softmax vs. Standard Euclidean Cross-Entropy
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_ASSETS_DIR = os.path.join(BASE_DIR, "Report_Assets")
os.makedirs(REPORT_ASSETS_DIR, exist_ok=True)


def generate_figure_1_1():
    """Generates Figure 1.1: Conceptual Paradigm of Text-Independent Acoustic Biometric Verification"""
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9.0)
    ax.axis('off')

    # Main Title
    ax.text(7.5, 8.6, 'Conceptual Paradigm of Text-Independent Acoustic Biometric Verification',
            ha='center', va='center', fontsize=16, fontweight='bold', color='#0F172A')
    ax.text(7.5, 8.25, 'Enrollment Mode (Feature Registration) vs. Verification Mode (Real-Time 1:1 Authentication)',
            ha='center', va='center', fontsize=11, fontstyle='italic', color='#475569')

    # Background Panels
    panel_enroll = patches.FancyBboxPatch((0.5, 4.4), 14.0, 3.5, boxstyle='round,pad=0.1,rounding_size=0.2',
                                         facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.5, zorder=1)
    ax.add_patch(panel_enroll)
    ax.text(0.8, 7.55, 'PHASE A: BIOMETRIC SPEAKER ENROLLMENT PIPELINE',
            fontsize=11.5, fontweight='bold', color='#1E40AF', zorder=2)

    panel_verif = patches.FancyBboxPatch((0.5, 0.4), 14.0, 3.7, boxstyle='round,pad=0.1,rounding_size=0.2',
                                        facecolor='#FFFDF7', edgecolor='#FDE68A', linewidth=1.5, zorder=1)
    ax.add_patch(panel_verif)
    ax.text(0.8, 3.8, 'PHASE B: REAL-TIME VERIFICATION & IMPOSTOR REJECTION PIPELINE',
            fontsize=11.5, fontweight='bold', color='#B45309', zorder=2)

    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color, text_color='#1E293B', title_size=9.5, sub_size=8.0):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08,rounding_size=0.15',
                                     facecolor=bg_color, edgecolor=border_color, linewidth=1.5, zorder=3)
        ax.add_patch(box)
        ax.text(x + w/2, y + h*0.64, title, ha='center', va='center', fontsize=title_size, fontweight='bold', color=text_color, zorder=4)
        ax.text(x + w/2, y + h*0.30, subtitle, ha='center', va='center', fontsize=sub_size, color=text_color, zorder=4)

    def draw_arrow(x1, y1, x2, y2, color='#64748B', lw=1.8):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->,head_width=0.4,head_length=0.6', color=color, lw=lw), zorder=5)

    # ─── ENROLLMENT TRACK ──────────────────────────────────────────────────────
    draw_box(0.8, 4.8, 1.9, 2.1, 'Raw Enrollment Speech', '16,000 Hz Mono PCM\nWaveform $x_{enroll}(t)$', '#FFFFFF', '#3B82F6')
    draw_arrow(2.7, 5.85, 3.1, 5.85)

    draw_box(3.1, 4.8, 2.0, 2.1, 'Acoustic Frontend', 'Energy VAD Filter\n512 STFT | 80 Mel Bins', '#FFFFFF', '#0EA5E9')
    draw_arrow(5.1, 5.85, 5.5, 5.85)

    draw_box(5.5, 4.8, 2.4, 2.1, 'Deep Neural Extractor', 'Dilated SE-Res2Blocks (d=2,3,4)\nAttentive Statistics Pooling', '#FFFFFF', '#6366F1')
    draw_arrow(7.9, 5.85, 8.3, 5.85)

    draw_box(8.3, 4.8, 2.3, 2.1, 'Speaker Embedding', 'Fixed 256-D Voiceprint\n$L_2$ Hypersphere Normalized', '#FFFFFF', '#8B5CF6')
    draw_arrow(10.6, 5.85, 11.2, 5.85)

    draw_box(11.2, 4.8, 2.9, 2.1, 'Biometric Gallery Vault', 'Secure Profile Storage\nTemplate $\\mathcal{G} = \\{(ID_k, \\mathbf{e}_k)\\}$', '#EFF6FF', '#2563EB',
             text_color='#1E3A8A', title_size=10.5)

    # ─── VERIFICATION TRACK ────────────────────────────────────────────────────
    draw_box(0.8, 1.0, 1.9, 2.1, 'Probe Utterance', 'Claimed Identity $S_k$\nWaveform $x_{probe}(t)$', '#FFFFFF', '#F97316')
    draw_arrow(2.7, 2.05, 3.1, 2.05)

    draw_box(3.1, 1.0, 2.0, 2.1, 'Shared Frontend', 'VAD Silence Stripping\n80 Mel Filterbank Matrix', '#FFFFFF', '#F59E0B')
    draw_arrow(5.1, 2.05, 5.5, 2.05)

    draw_box(5.5, 1.0, 2.4, 2.1, 'Frozen Backbone', 'Identical Pretrained Net\n256-D Probe Vector $\\mathbf{e}_{probe}$', '#FFFFFF', '#EC4899')
    draw_arrow(7.9, 2.05, 8.4, 2.05)

    # Connect Gallery down to Acoustic Metric Engine
    ax.annotate('', xy=(9.4, 3.15), xytext=(12.6, 4.8),
                arrowprops=dict(arrowstyle='->,head_width=0.4,head_length=0.6', color='#2563EB', lw=2.0,
                                connectionstyle='arc3,rad=0.18'), zorder=5)
    ax.text(11.4, 3.9, 'Retrieve Enrolled Profile $\\mathbf{e}_{target}$', ha='center', va='center',
            fontsize=8.5, fontweight='bold', color='#1D4ED8', zorder=6,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#EFF6FF', edgecolor='#93C5FD', lw=1))

    draw_box(8.4, 1.0, 2.0, 2.1, 'Acoustic Metric Engine', 'Cosine Similarity:\n$s = \\frac{\\mathbf{e}_{target} \\cdot \\mathbf{e}_{probe}}{\\|\\mathbf{e}_{target}\\| \\|\\mathbf{e}_{probe}\\|}$',
             '#FFFFFF', '#D97706')
    draw_arrow(10.4, 2.05, 10.9, 2.05)

    draw_box(10.9, 1.15, 1.5, 1.8, 'Comparator', 'Decision Rule:\n$s \\geq d_{th}$ ?', '#FEF3C7', '#B45309')

    # Output Branches
    draw_arrow(12.4, 2.4, 12.8, 2.7, color='#16A34A', lw=2.0)
    ax.text(12.55, 2.85, 'YES ($s \\geq d_{th}$)', fontsize=8, fontweight='bold', color='#15803D')
    draw_box(12.8, 2.25, 1.5, 1.2, 'TARGET ACCEPT', 'Identity Verified\nAccess Granted', '#DCFCE7', '#16A34A', text_color='#14532D', title_size=9.0, sub_size=7.5)

    draw_arrow(12.4, 1.6, 12.8, 1.3, color='#DC2626', lw=2.0)
    ax.text(12.55, 1.15, 'NO ($s < d_{th}$)', fontsize=8, fontweight='bold', color='#B91C1C')
    draw_box(12.8, 0.65, 1.5, 1.2, 'IMPOSTOR REJECT', 'Access Denied\nFraud Flagged', '#FEE2E2', '#DC2626', text_color='#7F1D1D', title_size=9.0, sub_size=7.5)

    plt.tight_layout()
    output_path = os.path.join(REPORT_ASSETS_DIR, "figure_1_1_asv_paradigm.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"✅ Generated: {output_path}")


def generate_figure_1_2():
    """Generates Figure 1.2: Geodesic Hyperspherical Decision Boundary of AAM-Softmax vs. Standard Euclidean Cross-Entropy"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), dpi=300)

    # ─── PANEL A: Standard Euclidean Softmax ──────────────────────────────────
    ax1.set_xlim(-0.5, 4.0)
    ax1.set_ylim(-0.5, 4.0)
    ax1.set_aspect('equal')
    ax1.axhline(0, color='#CBD5E1', lw=1.2)
    ax1.axvline(0, color='#CBD5E1', lw=1.2)

    # Class Weight Vectors W1 and W2
    ax1.arrow(0, 0, 3.2, 1.4, head_width=0.12, head_length=0.15, fc='#2563EB', ec='#2563EB', lw=2.2, zorder=4)
    ax1.text(3.3, 1.45, '$\\mathbf{W}_1$ (Class 1)', fontsize=11, fontweight='bold', color='#1D4ED8')

    ax1.arrow(0, 0, 1.4, 3.2, head_width=0.12, head_length=0.15, fc='#DC2626', ec='#DC2626', lw=2.2, zorder=4)
    ax1.text(1.45, 3.3, '$\\mathbf{W}_2$ (Class 2)', fontsize=11, fontweight='bold', color='#B91C1C')

    # Linear Decision Boundary: W1^T x = W2^T x (line of slope 1.0 through origin)
    x_line = np.linspace(0, 3.8, 100)
    ax1.plot(x_line, x_line, '--', color='#475569', lw=2.0, zorder=3, label='Decision Boundary: $\\mathbf{W}_1^T \\mathbf{x} = \\mathbf{W}_2^T \\mathbf{x}$')

    # Scatter of unconstrained representations
    np.random.seed(42)
    c1_r = np.random.uniform(1.2, 3.5, 45)
    c1_theta = np.random.normal(0.40, 0.18, 45)
    c1_x = c1_r * np.cos(c1_theta)
    c1_y = c1_r * np.sin(c1_theta)

    c2_r = np.random.uniform(1.2, 3.5, 45)
    c2_theta = np.random.normal(1.17, 0.18, 45)
    c2_x = c2_r * np.cos(c2_theta)
    c2_y = c2_r * np.sin(c2_theta)

    ax1.scatter(c1_x, c1_y, c='#3B82F6', alpha=0.75, s=36, edgecolors='none', label='Class 1 Samples (Wide Radial Spread)', zorder=2)
    ax1.scatter(c2_x, c2_y, c='#EF4444', alpha=0.75, s=36, edgecolors='none', label='Class 2 Samples (Wide Radial Spread)', zorder=2)

    # Shaded ambiguity region near origin
    ambig_circ = plt.Circle((0, 0), 1.0, color='#FEF3C7', alpha=0.35, zorder=1)
    ax1.add_patch(ambig_circ)
    ax1.text(0.4, 0.2, 'Ambiguous\nRadial Region\n($\\|\\mathbf{x}\\| \\to 0$)', fontsize=8, color='#92400E', ha='center')

    ax1.set_title('(a) Standard Euclidean Softmax Loss\n(Euclidean Linear Hyperplane, $m = 0$ rad)', fontsize=12, fontweight='bold', pad=12, color='#0F172A')
    ax1.set_xlabel('Embedding Dimension 1 ($z_1$)', fontsize=10)
    ax1.set_ylabel('Embedding Dimension 2 ($z_2$)', fontsize=10)
    ax1.legend(loc='lower right', fontsize=8.2, framealpha=0.9)
    ax1.grid(True, linestyle=':', alpha=0.5)

    # ─── PANEL B: Additive Angular Margin (AAM-Softmax) ───────────────────────
    ax2.set_xlim(-0.2, 1.4)
    ax2.set_ylim(-0.2, 1.4)
    ax2.set_aspect('equal')
    ax2.axhline(0, color='#CBD5E1', lw=1.2)
    ax2.axvline(0, color='#CBD5E1', lw=1.2)

    # Unit Hypersphere Arc (radius 1.0)
    phi = np.linspace(0, np.pi/2, 200)
    ax2.plot(np.cos(phi), np.sin(phi), '-', color='#0F172A', lw=2.2, label='Unit Hypersphere Surface $\\|\\mathbf{x}\\| = 1$', zorder=3)

    # Weight Directions W1 (theta=20 deg) and W2 (theta=70 deg)
    theta1 = np.radians(18)
    theta2 = np.radians(72)
    w1_x, w1_y = np.cos(theta1), np.sin(theta1)
    w2_x, w2_y = np.cos(theta2), np.sin(theta2)

    ax2.arrow(0, 0, w1_x, w1_y, head_width=0.035, head_length=0.045, fc='#2563EB', ec='#2563EB', lw=2.2, zorder=4)
    ax2.text(w1_x + 0.05, w1_y - 0.02, '$\\mathbf{W}_1$ (Class 1)', fontsize=11, fontweight='bold', color='#1D4ED8')

    ax2.arrow(0, 0, w2_x, w2_y, head_width=0.035, head_length=0.045, fc='#DC2626', ec='#DC2626', lw=2.2, zorder=4)
    ax2.text(w2_x - 0.08, w2_y + 0.05, '$\\mathbf{W}_2$ (Class 2)', fontsize=11, fontweight='bold', color='#B91C1C')

    # Angular margin m = 12 degrees
    m_deg = 12
    margin_rad = np.radians(m_deg)

    # Decision Boundaries:
    # Class 1 decision boundary: theta1 + m = theta2  => theta = 45 - m/2
    # Class 2 decision boundary: theta2 + m = theta1  => theta = 45 + m/2
    theta_mid = np.radians(45)
    theta_b1 = theta_mid - margin_rad/2
    theta_b2 = theta_mid + margin_rad/2

    ax2.plot([0, np.cos(theta_b1)*1.08], [0, np.sin(theta_b1)*1.08], '--', color='#16A34A', lw=1.8,
             label='Class 1 Boundary: $\\cos(\\theta_1 + m) = \\cos(\\theta_2)$', zorder=3)
    ax2.plot([0, np.cos(theta_b2)*1.08], [0, np.sin(theta_b2)*1.08], '--', color='#EA580C', lw=1.8,
             label='Class 2 Boundary: $\\cos(\\theta_2 + m) = \\cos(\\theta_1)$', zorder=3)

    # Angular Margin Shaded Wedge (geodesic gap 2m)
    phi_wedge = np.linspace(theta_b1, theta_b2, 100)
    wedge_x = np.concatenate([[0], np.cos(phi_wedge), [0]])
    wedge_y = np.concatenate([[0], np.sin(phi_wedge), [0]])
    ax2.fill(wedge_x, wedge_y, color='#FDE047', alpha=0.45, label='Angular Margin Gap ($2m$ Buffer)', zorder=2)

    # Clustered Samples along the Unit Circle
    np.random.seed(42)
    s1_theta = np.random.normal(theta1, 0.045, 45)
    s1_theta = np.clip(s1_theta, 0.05, theta_b1 - 0.02)
    ax2.scatter(np.cos(s1_theta), np.sin(s1_theta), c='#3B82F6', s=38, alpha=0.85, edgecolors='black', lw=0.5,
                label='Class 1 Clustered ($\\|\\mathbf{x}\\| = 1$)', zorder=5)

    s2_theta = np.random.normal(theta2, 0.045, 45)
    s2_theta = np.clip(s2_theta, theta_b2 + 0.02, np.pi/2 - 0.05)
    ax2.scatter(np.cos(s2_theta), np.sin(s2_theta), c='#EF4444', s=38, alpha=0.85, edgecolors='black', lw=0.5,
                label='Class 2 Clustered ($\\|\\mathbf{x}\\| = 1$)', zorder=5)

    # Annotate Angular Margin Arc
    arc_phi = np.linspace(theta_b1, theta_b2, 50)
    r_arc = 0.65
    ax2.plot(r_arc * np.cos(arc_phi), r_arc * np.sin(arc_phi), '-', color='#CA8A04', lw=2.2)
    ax2.text(0.52, 0.52, 'Geodesic\nMargin $2m$', fontsize=8.5, fontweight='bold', color='#854D0E', ha='center')

    ax2.set_title('(b) Additive Angular Margin Softmax (AAM-Softmax)\n(Hyperspherical Geodesic Decision Boundary, $m = 0.20$ rad)',
                  fontsize=12, fontweight='bold', pad=12, color='#0F172A')
    ax2.set_xlabel('Normalized Embedding Dimension 1 ($e_1$)', fontsize=10)
    ax2.set_ylabel('Normalized Embedding Dimension 2 ($e_2$)', fontsize=10)
    ax2.legend(loc='lower right', fontsize=8.0, framealpha=0.9)
    ax2.grid(True, linestyle=':', alpha=0.5)

    plt.tight_layout()
    output_path = os.path.join(REPORT_ASSETS_DIR, "figure_1_2_aam_softmax.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"✅ Generated: {output_path}")


if __name__ == "__main__":
    generate_figure_1_1()
    generate_figure_1_2()
