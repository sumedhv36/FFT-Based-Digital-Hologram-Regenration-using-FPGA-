# FFT-Based Electronic Hologram Reconstruction (MATLAB + Simulink)

##  Overview
This project demonstrates the generation and reconstruction of digital holograms using the **Fast Fourier Transform (FFT)**. The implementation mimics an FPGA-style hardware processing pipeline by simulating data streaming and FFT cores within the MATLAB and Simulink environment.

A 64×64 binary object (the letter "T") is used to generate an **off-axis hologram**. This hologram is then processed through a simulated FFT core to validate hardware-level reconstruction logic.

---

## Objectives
* **Generate** an off-axis hologram using MATLAB mathematical modeling.
* **Simulate** an FPGA-based FFT processing pipeline using Simulink blocks.
* **Reconstruct** the original object using Inverse FFT (IFFT).
* **Analyze** the advantages of off-axis holography over on-axis methods.

---

##  Methodology

### 1. Object Generation
A $64 \times 64$ binary image of the letter "T" is created as the source object.

### 2. Off-Axis Hologram Formation
To prevent overlapping components during reconstruction, a carrier frequency is applied to shift the object in the frequency domain:
$$U(x,y) = \text{obj}(x,y) \cdot e^{j(k_x x + k_y y)}$$

### 3. FPGA Simulation (Simulink)
The system simulates hardware constraints by:
* **Serializing** 2D data into a stream.
* Utilizing the **FFT IP Core** simulation block.
* Implementing control signals: `tvalid` and `tlast` for synchronization.

### 4. Reconstruction
The output from the simulated hardware core is processed using:
$$\text{recon} = \text{IFFT}(\text{FFT}_{output})$$
Visualization is enhanced using log-scaling to handle the dynamic range:
`imagesc(log(1 + abs(recon)))`

---

##  Key Concepts: On-Axis vs. Off-Axis
| Feature | On-Axis | Off-Axis |
| :--- | :--- | :--- |
| **Shift applied** | ❌ No | ✅ Yes |
| **Reconstruction quality** | Low (DC bias interference) | High |
| **Filtering required** | ❌ No | ✅ Yes |
| **Overlapping components** | Yes | No |

---

##  Project Structure
```text
project/
├── matlab/
│   ├── generate_hologram.m      # Hologram creation script
│   ├── reconstruct_output.m     # Final image visualization
│   └── fixed_point_conversion.m # Quantization for hardware logic
├── simulink/
│   └── fft_model.slx            # FPGA-style FFT simulation
├── verilog/                     # (Optional) FPGA Extension
│   ├── fft_top.v
│   └── tb_fft.v
├── data/
│   └── input_data.txt           # Serialized test vectors
└── README.md
```
---
## Expected Output
* *A reconstructed image of the letter "T"*
* *Slight blur/noise* (normal in holography)
* *Heatmap visualization*

---


## 📚 Reference
Based on the paper:  
FFT Implementation for Electronic Holograms using Field Programmable Gate Array

---

## 👨‍💻 Author
---
Sumedh V Bhat and
Sachin V Nagaraddi

---

## ⭐ Conclusion
This project successfully demonstrates digital hologram generation and reconstruction using FFT. The simulation validates FPGA-based processing and highlights the importance of off-axis techniques for accurate image recovery.
