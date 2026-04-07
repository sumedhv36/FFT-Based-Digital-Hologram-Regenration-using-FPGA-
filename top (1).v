module fft_top (
    input wire clk,
    input wire rst,

    input wire [15:0] data_re_in,
    input wire [15:0] data_im_in,
    input wire tvalid_in,
    input wire tlast_in,

    output wire [15:0] data_re_out,
    output wire [15:0] data_im_out,
    output wire tvalid_out,
    output wire tlast_out
);

wire [31:0] s_axis_data;
assign s_axis_data = {data_re_in, data_im_in};

wire [31:0] m_axis_data;

// FFT IP instance
fft_ip fft_inst (
    .aclk(clk),

    .s_axis_data_tdata(s_axis_data),
    .s_axis_data_tvalid(tvalid_in),
    .s_axis_data_tlast(tlast_in),

    .m_axis_data_tdata(m_axis_data),
    .m_axis_data_tvalid(tvalid_out),
    .m_axis_data_tlast(tlast_out)
);

// Split output
assign data_re_out = m_axis_data[31:16];
assign data_im_out = m_axis_data[15:0];

endmodule