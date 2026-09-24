`timescale 1ns/1ps
// Agent-only isolation of the inherited LPF input-width warning.
module probe_filter_port;
    reg clk = 0, rstn = 0;
    always #4 clk = ~clk;
    reg [4:0] setting = 3;
    reg signed [13:0] sample = 0;
    wire signed [13:0] narrow_out, padded_out;
    red_pitaya_lpf_block #(.SHIFTBITS(5)) narrow (
        .clk_i(clk), .rstn_i(rstn), .shift(setting),
        .filter_on(1'b1), .highpass(1'b0), .signal_i(sample), .signal_o(narrow_out));
    red_pitaya_lpf_block #(.SHIFTBITS(5)) padded (
        .clk_i(clk), .rstn_i(rstn), .shift({1'b0, setting}),
        .filter_on(1'b1), .highpass(1'b0), .signal_i(sample), .signal_o(padded_out));
    initial begin
        repeat (2) @(posedge clk);
        @(negedge clk); rstn = 1; sample = 8191;
        repeat (4) begin
            @(posedge clk); #1;
            $display("PORT_PROBE shift=%b/%b delta=%h/%h y=%h/%h out=%h/%h",
                     narrow.shift, padded.shift, narrow.delta, padded.delta,
                     narrow.y, padded.y, narrow_out, padded_out);
        end
        $finish;
    end
endmodule
