%% Extract valid data
idx = find(tvalid_out > 0.5);

R = double(real_out(idx(end-4095:end)));
I = double(img_out(idx(end-4095:end)));

fpga_result = reshape(complex(R, I), [64, 64]);

%% -------- CORRECT RECONSTRUCTION --------

% 1. IFFT (MANDATORY)
recon = ifft2(fpga_result);

% 2. Shift
recon = fftshift(recon);

% 3. Visualization
figure;
imagesc(log(1 + abs(recon)));
colormap(hot);
axis image;
colorbar;
title('Reconstructed Letter T (Simulink FFT Output)');
xlabel('Spatial X'); ylabel('Spatial Y');