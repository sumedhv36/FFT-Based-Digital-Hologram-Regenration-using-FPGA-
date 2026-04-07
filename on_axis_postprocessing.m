%% Extract valid data
idx = find(tvalid_out > 0.5);

if length(idx) < 4096
    error('Simulation incomplete');
end

R = double(real_out(idx(end-4095:end)));
I = double(img_out(idx(end-4095:end)));

% Reconstruct matrix
recon = reshape(complex(R, I), [64, 64]);

% Shift for display
recon = fftshift(recon);

%% Display
figure;
imagesc(log(1 + abs(recon)));
colormap(hot);
axis image;
colorbar;
title('On-Axis Reconstruction (Simulink)');
xlabel('Spatial X'); ylabel('Spatial Y');