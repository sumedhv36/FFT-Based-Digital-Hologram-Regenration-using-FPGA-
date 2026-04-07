clc; clear; close all;

%% Grid
N = 64;
[x, y] = meshgrid(1:N, 1:N);

%% Create "T"
obj = zeros(N,N);
obj(15:50, 32) = 1;
obj(15:20, 20:45) = 1;

%% ON-AXIS (NO SHIFT)
shifted_obj = obj;

%% FFT (input to Simulink)
hologram_data = fft2(shifted_obj);

%% Convert to stream
data_stream = hologram_data(:);
t = (0:N^2-1)';

% Real & Imag as time series
sim_in_re = [t, real(data_stream)];
sim_in_im = [t, imag(data_stream)];

% Control signals
tvalid_signal = [t, ones(N^2,1)];
tlast_signal  = [t, [zeros(N^2-1,1); 1]];

disp('👉 Run Simulink model now');