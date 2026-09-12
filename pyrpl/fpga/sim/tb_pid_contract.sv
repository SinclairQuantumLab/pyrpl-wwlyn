`timescale 1ns/1ps
// Real RTL, no forced internal nets or behavioral substitute for the DUT.
module tb_pid_contract;
    reg clk = 0;
    always #4 clk = ~clk;
    reg rstn = 0, paused = 0, trigger = 0;
    reg signed [13:0] data_in = 0, diff_in = 0;
    wire signed [13:0] data_out, diff_out;
    reg [15:0] addr = 0;
    reg wen = 0, ren = 0;
    reg [31:0] wdata = 0;
    wire ack;
    wire [31:0] rdata;
    integer failures = 0, checks = 0, i, value;
    reg signed [31:0] held_integral;

    red_pitaya_pid_block dut (
        .clk_i(clk), .rstn_i(rstn), .paused_i(paused),
        .dat_i(data_in), .dat_o(data_out),
        .diff_dat_i(diff_in), .diff_dat_o(diff_out),
        .setpoint_trig_i(trigger), .addr(addr), .wen(wen), .ren(ren),
        .ack(ack), .rdata(rdata), .wdata(wdata)
    );

    task tick(input integer count);
        repeat (count) @(posedge clk);
        #1;
    endtask

    task check(input logic condition, input string label_text);
        checks = checks + 1;
        if (condition !== 1'b1) begin
            failures = failures + 1;
            $display("PID_CONTRACT_FAIL %s at %0t", label_text, $time);
        end
    endtask

    task write_reg(input [15:0] address, input [31:0] value_in);
        @(negedge clk); addr = address; wdata = value_in; wen = 1; ren = 0;
        tick(1);
        check(ack === 1'b1, "write acknowledgement");
        @(negedge clk); wen = 0;
    endtask

    task read_reg(input [15:0] address);
        @(negedge clk); addr = address; ren = 1; wen = 0;
        tick(1);
        check(ack === 1'b1, "read acknowledgement");
        @(negedge clk); ren = 0;
    endtask

    task expect_reg(input [15:0] address, input [31:0] expected);
        read_reg(address);
        check(rdata === expected, $sformatf("register %h expected %h got %h", address, expected, rdata));
    endtask

    task expect_output(input integer expected);
        tick(8);
        check($signed(data_out) === expected,
              $sformatf("output expected %0d got %0d", expected, $signed(data_out)));
    endtask

    initial begin
        tick(5);
        @(negedge clk); rstn = 1;
        expect_reg('h200, 12);
        expect_reg('h204, 32);
        expect_reg('h20c, 30);
        expect_output(0);

        write_reg('h108, 4096); // P = 1, filter bypass, I = 0.
        @(negedge clk); data_in = 1024;
        expect_output(1024);
        @(negedge clk); data_in = 512;
        repeat (3) begin
            tick(1);
            check($signed(data_out) === 1024, "P path retains four-cycle latency");
        end
        tick(1);
        check($signed(data_out) === 512, "P path updates on fourth cycle");
        @(negedge clk); data_in = 1024;
        expect_output(1024);
        @(negedge clk); paused = 1; data_in = -2048;
        expect_output(1024); // P is held, not zeroed.
        @(negedge clk); paused = 0;
        expect_output(-2048);

        write_reg('h108, 32'h00100000);
        expect_reg('h108, 32'h00100000); // Wider than the original 14-bit gain.
        @(negedge clk); data_in = 64;
        expect_output(8191);
        @(negedge clk); data_in = -64;
        expect_output(-8192);
        write_reg('h108, 4096);
        write_reg('h124, -200);
        write_reg('h128, 300);
        @(negedge clk); data_in = 1024;
        expect_output(300);
        @(negedge clk); data_in = -1024;
        expect_output(-200);
        write_reg('h124, -8192);
        write_reg('h128, 8191);

        write_reg('h108, 0);
        write_reg('h100, 512);
        expect_output(512);
        expect_reg('h100, 512);
        @(negedge clk); data_in = 64;
        write_reg('h10c, 32'h10000000);
        tick(16);
        @(negedge clk); paused = 1;
        read_reg('h100);
        held_integral = $signed(rdata);
        check(held_integral > 512, "integrator accumulates positive error");
        @(negedge clk); data_in = -64;
        tick(20);
        expect_reg('h100, held_integral);
        @(negedge clk); paused = 0;
        tick(16);
        read_reg('h100);
        check($signed(rdata) < held_integral, "integrator resumes after hold");
        @(negedge clk); data_in = 64;
        tick(2200);
        expect_reg('h100, 8191);
        expect_output(8191);
        @(negedge clk); data_in = -64;
        tick(4200);
        expect_reg('h100, 32'hffffe000); // Signed -8192 integral readback.
        expect_output(-8192);
        write_reg('h10c, 0);
        write_reg('h100, 0);
        write_reg('h108, 4096);
        @(negedge clk); data_in = 0;

        for (i = 0; i < 16; i = i + 1) begin
            value = (i - 8) * 128;
            write_reg('h134, (i << 14) | (value & 'h3fff));
            expect_reg('h138, value & 'h3fff);
        end
        write_reg('h140, 1);
        write_reg('h130, 1);
        for (i = 0; i <= 16; i = i + 1) begin
            value = ((i % 16) - 8) * 128;
            expect_reg('h240, i % 16);
            expect_reg('h244, i == 16);
            expect_reg('h24c, value & 'h3fff);
            expect_output(-value);
            if (i < 16) begin
                @(negedge clk); trigger = 1;
                repeat (2) begin
                    tick(1);
                    check(dut.setpoint_index === (i % 16), "trigger synchronizer latency");
                end
                tick(1);
                check(dut.setpoint_index === ((i + 1) % 16), "advance on third sampled clock");
                tick(12); // A sustained high must advance only once.
                expect_reg('h240, (i + 1) % 16);
                @(negedge clk); trigger = 0;
                tick(4);
                expect_reg('h240, (i + 1) % 16); // No falling-edge advance.
            end
        end
        write_reg('h140, 1);
        expect_reg('h240, 0);
        expect_reg('h244, 0);
        write_reg('h240, 5);
        expect_reg('h240, 5);
        write_reg('h130, 0);
        write_reg('h12c, 15); // Differential input plus P/I/D pause mask.
        @(negedge clk); data_in = 256; diff_in = 128;
        expect_output(128);

        if (failures) $fatal(1, "PID_CONTRACT_FAIL %0d of %0d checks", failures, checks);
        $display("PID_CONTRACT_PASS %0d checks", checks);
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "PID_CONTRACT_FAIL watchdog");
    end
endmodule
