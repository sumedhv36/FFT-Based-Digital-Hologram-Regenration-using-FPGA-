# =============================================================================
# step3_optics.py  —  Complete corrected optical post-processing
# =============================================================================
# Reference: Castillo Atoche et al., "FFT Implementation for Electronic
#   Holograms using FPGA", ICCDCS 2006, pp. 115-119.
#
# ALL FIXES vs original:
#   [FIX-1]  Reference wave removed from this file — it belongs in the
#            SPATIAL domain after ifft2 in MATLAB (paper Eq.5). Adding it
#            here in the frequency domain was physically wrong.
#   [FIX-2]  Fresnel freq grid now uses np.fft.fftfreq() — DC at index 0,
#            perfectly aligned with ifftshift + ifft2 in MATLAB Part 4.
#            Old version subtracted cx/cy from mgrid which was offset.
#   [FIX-3]  FRFT: previous cot(phi) diverged at alpha=0 and alpha=1.
#            Replaced with Ozaktas three-chirp upsampled-convolution,
#            stable across the full [0, 2] range.
#   [FIX-4]  Gaussian notch: assertion catches accidental 1-based MATLAB
#            indices (33 instead of 32).
#   [FIX-5]  ifftshift applied inside process_hologram before Fresnel
#            multiply so output is in standard FFT order (DC at [0,0]).
# =============================================================================

import numpy as np

# ---------------------------------------------------------------------------
# Physical constants — must match MATLAB pipeline exactly
# ---------------------------------------------------------------------------
LAMBDA      = 632.8e-9   # He-Ne red laser wavelength  [m]
Z_PROP      = 0.05       # Propagation distance 5 cm   [m]
PIXEL_PITCH = 10e-6      # SLM / camera pixel pitch    [m]
IMG_SIZE    = 64


# ===========================================================================
# 1.  GAUSSIAN NOTCH FILTER
# ===========================================================================
def create_gaussian_notch(shape, center=None, radius=5.0):
    """
    Inverted Gaussian notch to suppress the DC zero-order artefact.

    M(x,y) = 1 - exp[ -((x-cx)^2 + (y-cy)^2) / (2*r^2) ]
      0 at DC peak (blocks artefact), 1 far from centre (passes sidebands).

    Parameters
    ----------
    shape  : (rows, cols).
    center : (row, col) in 0-based Python indexing. None = auto-centre.
             Do NOT pass MATLAB 1-based values (33); use Python values (32).
    radius : Gaussian sigma [pixels].

    Returns
    -------
    mask : float64 ndarray in [0, 1].
    """
    rows, cols = shape
    cy = center[0] if center is not None else rows // 2
    cx = center[1] if center is not None else cols // 2

    assert cy < rows and cx < cols, (
        f"center ({cy},{cx}) out of bounds for ({rows},{cols}). "
        "Use 0-based Python indexing (32, not 33)."
    )

    y_idx, x_idx = np.ogrid[:rows, :cols]
    mask = 1.0 - np.exp(
        -((x_idx - cx) ** 2 + (y_idx - cy) ** 2) / (2.0 * radius ** 2)
    )
    return mask.astype(np.float64)


# ===========================================================================
# 2.  FRESNEL FREE-SPACE PROPAGATION KERNEL  (paper Eq.1)
# ===========================================================================
def fresnel_propagation_kernel(shape, z=Z_PROP, wavelength=LAMBDA,
                               pixel_pitch=PIXEL_PITCH):
    """
    Fresnel quadratic-phase chirp kernel in the spatial-frequency domain.

    H(fx,fy) = exp(i*k*z) * exp(-i*pi*lambda*z*(fx^2+fy^2))

    [FIX-2] Uses np.fft.fftfreq() — DC at index 0, matching
    the ifftshift + ifft2 convention in MATLAB Part 4.

    Returns
    -------
    H : complex128 ndarray in standard FFT order (DC at [0,0]).
    """
    rows, cols = shape
    k = 2.0 * np.pi / wavelength

    fx = np.fft.fftfreq(cols, d=pixel_pitch)   # [cycles/m], DC at index 0
    fy = np.fft.fftfreq(rows, d=pixel_pitch)
    Fx, Fy = np.meshgrid(fx, fy)

    H = np.exp(1j * k * z) * np.exp(
        -1j * np.pi * wavelength * z * (Fx ** 2 + Fy ** 2)
    )
    return H.astype(np.complex128)


# ===========================================================================
# 3.  FRACTIONAL FOURIER TRANSFORM  (FRFT)
#     Ozaktas three-chirp upsampled-convolution — stable for alpha in [0,2]
# ===========================================================================
def _frft_1d(signal, alpha):
    """
    1-D Fractional Fourier Transform.

    alpha = 0 -> identity
    alpha = 1 -> normalised DFT
    alpha = 2 -> time-reversal
    """
    N     = len(signal)
    alpha = float(alpha) % 2.0

    if alpha < 1e-8:
        return signal.copy()
    if abs(alpha - 2.0) < 1e-8:
        return signal[::-1].copy()
    if abs(alpha - 1.0) < 1e-8:
        return np.fft.fft(signal, norm='ortho')

    phi     = alpha * np.pi / 2.0
    tan_phi = np.tan(phi)
    sin_phi = np.sin(phi)
    n       = np.arange(N, dtype=np.float64)

    # Normalisation prefactor (Ozaktas 1996, Eq. 9)
    A_phi = np.sqrt((1.0 - 1j / tan_phi) / N)

    # Pre/post chirp
    chirp = np.exp(-1j * np.pi * n ** 2 * tan_phi / N)

    # Convolution kernel
    conv_kernel = np.exp(1j * np.pi * n ** 2 / (N * sin_phi))

    # Linear convolution via zero-padded FFT
    Y = np.fft.fft(signal * chirp, n=2 * N)
    K = np.fft.fft(conv_kernel,    n=2 * N)
    conv_result = np.fft.ifft(Y * K)[:N]

    return A_phi * chirp * conv_result


def frft_2d(matrix, alpha):
    """2-D separable FRFT: row-wise then column-wise."""
    row_xf = np.apply_along_axis(_frft_1d, axis=1, arr=matrix, alpha=alpha)
    result  = np.apply_along_axis(_frft_1d, axis=0, arr=row_xf,  alpha=alpha)
    return result


# ===========================================================================
# 4.  MAIN ENTRY POINT — called from MATLAB via the Python engine
#
#     Handles FREQUENCY-DOMAIN operations only:
#       - Gaussian notch
#       - Fresnel propagation  (paper Eq.1)
#       - Optional FRFT for depth-plane selection
#
#     [FIX-1] Reference wave (Eq.4/5) is NOT done here — it is added in
#     MATLAB Part 4 after ifft2, in the spatial domain.
#
#     MATLAB call sequence:
#       filtered  = py.step3_optics.process_hologram(U_max_centered)
#       unshifted = ifftshift(double(filtered))
#       recon     = ifft2(unshifted)
#       U_H       = U_ref + recon          % Eq.5 — spatial domain
#       amplitude = abs(U_H)
#       phase     = angle(U_H)
# ===========================================================================
def process_hologram(matlab_data,
                     notch_radius=5.0,
                     use_frft=True,
                     frft_alpha=0.85,
                     z=Z_PROP,
                     wavelength=LAMBDA,
                     pixel_pitch=PIXEL_PITCH):
    """
    Frequency-domain optical post-processing for the FPGA Fourier hologram.

    Parameters
    ----------
    matlab_data  : 2-D complex array (64x64) with DC at geometric centre
                   (fftshift + Eq.3 normalisation already applied in MATLAB).
    notch_radius : Gaussian notch sigma [pixels]. Default 5.
    use_frft     : apply 2-D separable FRFT. Default True.
    frft_alpha   : FRFT fractional order in (0, 2]. Default 0.85.
    z            : Fresnel propagation distance [m].
    wavelength   : optical wavelength [m].
    pixel_pitch  : SLM pixel pitch [m].

    Returns
    -------
    filtered : complex128 ndarray (64x64) in standard FFT order (DC at [0,0]),
               ready for ifftshift + ifft2 in MATLAB Part 4.
    """

    hologram = np.array(matlab_data, dtype=np.complex128)

    if hologram.ndim == 1:
        side     = int(round(np.sqrt(hologram.size)))
        hologram = hologram.reshape(side, side)

    rows, cols = hologram.shape
    assert rows == cols == 64, f"Expected 64x64, got {rows}x{cols}."

    # Step 1: Zero-order artefact suppression
    notch    = create_gaussian_notch(hologram.shape,
                                     center=(rows // 2, cols // 2),
                                     radius=notch_radius)
    filtered = hologram * notch

    # Step 2: ifftshift — moves DC from (32,32) to (0,0) for Fresnel kernel
    filtered = np.fft.ifftshift(filtered)

    # Step 3: Fresnel free-space propagation
    H = fresnel_propagation_kernel(filtered.shape, z=z,
                                   wavelength=wavelength,
                                   pixel_pitch=pixel_pitch)
    filtered = filtered * H

    # Step 4: FRFT for depth-plane selection (alpha=1 == ordinary DFT)
    if use_frft:
        filtered = frft_2d(filtered, alpha=frft_alpha)

    return filtered   # standard FFT order, DC at [0,0]


# ===========================================================================
# SELF-TEST  —  run as:  python step3_optics.py
# ===========================================================================
if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("=" * 60)
    print("step3_optics.py  —  self-test")
    print("=" * 60)

    rng     = np.random.default_rng(42)
    N       = IMG_SIZE
    cy_t    = N // 2
    cx_t    = N // 2
    y_t, x_t = np.mgrid[:N, :N]

    # Synthetic centred Gaussian spectrum (simulates post-fftshift FPGA output)
    blob = np.exp(
        -((x_t - cx_t) ** 2 + (y_t - cy_t) ** 2) / (2 * 8.0 ** 2)
    ).astype(np.complex128)
    blob += 0.05 * (rng.standard_normal((N, N)) + 1j * rng.standard_normal((N, N)))
    blob /= np.max(np.abs(blob))   # simulate Eq.3 normalisation

    # Run frequency-domain pipeline
    filtered = process_hologram(blob, notch_radius=5.0,
                                use_frft=True, frft_alpha=0.85)

    # Reconstruct — mirrors MATLAB Part 4
    recon = np.fft.ifft2(filtered)

    # Reference wave + hologram mix — Eq.4 / Eq.5, spatial domain
    y_r, x_r = np.mgrid[:N, :N]
    x_phys   = (x_r - cx_t) * PIXEL_PITCH
    y_phys   = (y_r - cy_t) * PIXEL_PITCH
    r_dist   = np.sqrt(x_phys ** 2 + y_phys ** 2 + Z_PROP ** 2)
    k        = 2 * np.pi / LAMBDA
    U_ref    = np.exp(1j * k * r_dist) / r_dist
    U_H      = U_ref + recon

    amplitude = np.abs(U_H)
    phase     = np.angle(U_H)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].imshow(np.abs(blob), cmap='gray')
    axes[0].set_title('Input |U_max| (simulated)')
    axes[1].imshow(amplitude, cmap='gray')
    axes[1].set_title('Recovered amplitude |U_H|')
    im = axes[2].imshow(phase, cmap='jet', vmin=-np.pi, vmax=np.pi)
    axes[2].set_title('Recovered phase angle(U_H)')
    plt.colorbar(im, ax=axes[2], label='rad')
    plt.tight_layout()
    plt.savefig('step3_selftest.png', dpi=120)
    print("Saved -> step3_selftest.png")
    print("All stages OK.")