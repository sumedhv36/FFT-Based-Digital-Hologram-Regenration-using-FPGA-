clc; clear; close all;

%% Grid
N = 64;
[x, y] = meshgrid(1:N, 1:N);

%% Create "T"
obj = zeros(N,N);
obj(15:50, 32) = 1;
obj(15:20, 20:45) = 1;

%% Off-axis shift
kx = 2*pi/8;
ky = 2*pi/8;
shifted_obj = obj .* exp(1j * (kx*x + ky*y));

%% FFT (this is your "golden reference")
hologram_data = fft2(shifted_obj);

%% Convert to stream (IMPORTANT)
data_stream = hologram_data(:);

t = (0:N^2-1)';

sim_in_re = [t, real(data_stream)];
sim_in_im = [t, imag(data_stream)];

%% Control signals
tvalid_signal = [t, ones(N^2,1)];
tlast_signal = [t, [zeros(N^2-1,1); 1]];

disp('Run Simulink now');