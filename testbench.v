`timescale 1ns/1ps

module tb_fft;

reg clk;
reg rst;

reg [15:0] data_re_in;
reg [15:0] data_im_in;
reg tvalid_in;
reg tlast_in;

wire [15:0] data_re_out;
wire [15:0] data_im_out;
wire tvalid_out;
wire tlast_out;

integer i;

// DUT
fft_top uut (
    .clk(clk),
    .rst(rst),
    .data_re_in(data_re_in),
    .data_im_in(data_im_in),
    .tvalid_in(tvalid_in),
    .tlast_in(tlast_in),
    .data_re_out(data_re_out),
    .data_im_out(data_im_out),
    .tvalid_out(tvalid_out),
    .tlast_out(tlast_out)
);

// Clock
always #5 clk = ~clk;

initial begin
    clk = 0;
    rst = 1;
    tvalid_in = 0;
    tlast_in = 0;

    #20 rst = 0;

    // Send 4096 samples
    for (i = 0; i < 4096; i = i + 1) begin
        @(posedge clk);
        data_re_in = i;   // replace with real data
        data_im_in = 0;
        tvalid_in = 1;

        if (i == 4095)
            tlast_in = 1;
        else
            tlast_in = 0;
    end

    @(posedge clk);
    tvalid_in = 0;

    #1000 $finish;
end

endmodule