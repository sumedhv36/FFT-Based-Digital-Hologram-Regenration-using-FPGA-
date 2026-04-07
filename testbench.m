N = 64;

data_stream = hologram_data(:);

% Convert to fixed-point (16-bit)
real_fixed = fi(real(data_stream), 1, 16, 8);
imag_fixed = fi(imag(data_stream), 1, 16, 8);

% Convert to integer for FPGA
real_int = int16(real_fixed);
imag_int = int16(imag_fixed);

% Save to file (for testbench)
fid = fopen('input_data.txt','w');
for i = 1:length(real_int)
    fprintf(fid, '%d %d\n', real_int(i), imag_int(i));
end
fclose(fid);