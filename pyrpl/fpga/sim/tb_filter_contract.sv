`timescale 1ns/1ps
// Integer, bit/cycle-accurate characterization of the existing recurrence.
// The DUT is the real RTL. No internal state is forced or read by this model.
module filter_contract_case #(
    parameter STAGES = 3,
    parameter SHIFTBITS = 5,
    parameter SIGNALBITS = 14,
    parameter MINBW = 10
)(output reg done = 0);
    function automatic integer floor_log2_plus_one(input integer value);
        integer width;
        begin
            width = 0;
            while (value > 0) begin value = value >> 1; width = width + 1; end
            floor_log2_plus_one = width;
        end
    endfunction
    localparam MAXSHIFT = floor_log2_plus_one(125000000 / MINBW);
    localparam STATEBITS = SIGNALBITS + MAXSHIFT;
    reg clk = 0, rstn = 0;
    always #4 clk = ~clk;
    reg [31:0] setting = 0;
    reg signed [SIGNALBITS-1:0] data_in = 0;
    wire signed [SIGNALBITS-1:0] data_out;
    longint signed state_y [0:STAGES-1];
    longint signed state_delta [0:STAGES-1];
    longint signed next_y [0:STAGES-1];
    longint signed next_delta [0:STAGES-1];
    longint signed stage_input, expected, old_output;
    reg [31:0] random_state = 32'h347ac591;
    integer cycle, stage, shift_value, mode, checks = 0;

    red_pitaya_filter_block #(
        .STAGES(STAGES), .SHIFTBITS(SHIFTBITS),
        .SIGNALBITS(SIGNALBITS), .MINBW(MINBW)
    ) dut (.clk_i(clk), .rstn_i(rstn), .set_filter(setting),
           .dat_i(data_in), .dat_o(data_out));

    function automatic longint signed wrap_signed(
        input longint signed value, input integer bits
    );
        longint signed modulus, truncated;
        begin
            modulus = 64'sd1 << bits;
            truncated = value & (modulus - 1);
            wrap_signed = (truncated >= (modulus >> 1)) ? truncated - modulus : truncated;
        end
    endfunction

    function automatic longint signed stage_output(
        input integer index, input longint signed sample
    );
        begin
            if (!setting[index*8+7]) stage_output = sample;
            else if (setting[index*8+6])
                stage_output = wrap_signed(state_delta[index], SIGNALBITS);
            else stage_output = state_y[index] >>> MAXSHIFT;
        end
    endfunction

    task compare_output(input string phase);
        begin
            expected = $signed(data_in);
            for (integer index = 0; index < STAGES; index = index + 1)
                expected = stage_output(index, expected);
            checks = checks + 1;
            if ($signed(data_out) !== expected)
                $fatal(1, "PID_CONTRACT_FAIL filter stages=%0d bits=%0d minbw=%0d cycle=%0d %s expected=%0d got=%0d config=%h",
                       STAGES, SIGNALBITS, MINBW, cycle, phase, expected, $signed(data_out), setting);
        end
    endtask

    initial begin
        // Initialize both implementations through their public reset input.
        repeat (2) @(posedge clk);
        #1;
        for (stage = 0; stage < STAGES; stage = stage + 1) begin
            state_y[stage] = 0; state_delta[stage] = 0;
        end
        for (cycle = 0; cycle < 2048; cycle = cycle + 1) begin
            @(negedge clk);
            rstn = (cycle % 257 != 0);
            // Deterministic full-range samples: zero, both rails, impulse,
            // alternating sign and pseudo-random. No host RNG dependency.
            random_state = {random_state[30:0],
                random_state[31] ^ random_state[21] ^ random_state[1] ^ random_state[0]};
            case (cycle % 8)
                0: data_in = 0;
                1: data_in = (64'sd1 << (SIGNALBITS-1)) - 1;
                2: data_in = -(64'sd1 << (SIGNALBITS-1));
                3: data_in = 1;
                4: data_in = -1;
                default: data_in = random_state;
            endcase
            // Every register-encoded shift, each mode and mixed cascades.
            // Values above MAXSHIFT characterize the existing clamp.
            setting = 0;
            for (stage = 0; stage < STAGES; stage = stage + 1) begin
                shift_value = (cycle / 4 + stage * 3) % (1 << SHIFTBITS);
                mode = (cycle / (4 * (1 << SHIFTBITS)) + stage) % 4;
                setting[stage*8 +: 8] = (mode << 6) | shift_value;
            end
            #1; compare_output("before clock/control update");
            // Simultaneous state update: all stages consume OLD state.
            stage_input = $signed(data_in);
            for (stage = 0; stage < STAGES; stage = stage + 1) begin
                old_output = stage_output(stage, stage_input);
                shift_value = (setting >> (stage*8)) & ((1 << SHIFTBITS)-1);
                if (shift_value > MAXSHIFT) shift_value = MAXSHIFT;
                next_delta[stage] = rstn ? wrap_signed(
                    stage_input - (state_y[stage] >>> MAXSHIFT), STATEBITS) : 0;
                next_y[stage] = rstn ? wrap_signed(
                    state_y[stage] + (state_delta[stage] <<< shift_value), STATEBITS) : 0;
                stage_input = old_output;
            end
            @(posedge clk);
            for (stage = 0; stage < STAGES; stage = stage + 1) begin
                state_y[stage] = next_y[stage]; state_delta[stage] = next_delta[stage];
            end
            #1; compare_output("after clock");
        end
        done = 1;
        $display("FILTER_CONTRACT_PASS stages=%0d bits=%0d minbw=%0d checks=%0d",
                 STAGES, SIGNALBITS, MINBW, checks);
    end
endmodule
