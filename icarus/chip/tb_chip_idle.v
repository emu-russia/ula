// tb_chip_idle.v — full-chip ULA 6C001 testbench for Icarus Verilog.
//
// Scenario: "ULA in the vacuum" with a populated DRAM (deterministic checker
// pattern, same formula as the python reference model) and no CPU bus
// activity. The chip free-runs: OSC = 20 MHz, the h/v counters count rows and
// frames, the video pipeline fetches pixel/attribute bytes from the DRAM and
// the whole timing/sync/DAC front end runs. This reproduces, gate-for-gate in
// Icarus Verilog, the scenario the python model used for the typical waves.
//
// Output: ula_run_idle.vcd (full hierarchical dump of ULA_Run).
// Run:    iverilog -g2012 -o chip_idle.run tb_chip_idle.v dram_ula.v ../../hdl/*.v
//         vvp chip_idle.run
//
// Use +run_ns=<ns> to shorten/lengthen the run (default: 19 ms ~ one full
// frame plus margin).

`timescale 1ns/1ns

module ULA_Run;

    parameter longint RUN_NS = 19_000_000;

    // ------------------------------------------------------------------ pins
    reg         OSC     = 1'b0;      // 20 MHz master clock (period 50 ns)
    reg         n_RD    = 1'b1;
    reg         n_WR    = 1'b1;
    reg         n_MREQ  = 1'b1;
    reg         n_IOREQ = 1'b1;
    reg         A15     = 1'b0;
    reg         A14     = 1'b0;
    reg         KB0_drv = 1'b0;      // keyboard matrix, idle
    wire        KB0     = KB0_drv;
    reg         KB1 = 1'b1, KB2 = 1'b1, KB3 = 1'b1, KB4 = 1'b1;

    wire        n_INT;
    wire        n_WE;
    wire        n_RAS;
    wire        n_CAS;
    wire        n_ROMCS;
    wire        n_PHICPU;
    wire        SOUND;
    wire        n_Yout, Vout, Uout;
    wire [6:0]  busA;
    wire [7:0]  busD;

    // pull-ups on the shared/real board buses (dram data + chip outputs)
    genvar g;
    generate
        for (g = 0; g < 7; g = g + 1) begin : pa
            pullup (busA[g]);
        end
        for (g = 0; g < 8; g = g + 1) begin : pd
            pullup (busD[g]);
        end
    endgenerate
    pullup (n_INT);
    pullup (n_PHICPU);
    pullup (n_WE);
    pullup (n_CAS);
    pullup (n_RAS);
    pullup (n_ROMCS);
    pullup (SOUND);

    // ------------------------------------------------------------------ DUT
    ula ula_inst (
        .n_INT    (n_INT),
        .A6       (busA[6]),
        .A5       (busA[5]),
        .A4       (busA[4]),
        .A3       (busA[3]),
        .A2       (busA[2]),
        .A1       (busA[1]),
        .A0       (busA[0]),
        .n_WE     (n_WE),
        .n_RD     (n_RD),
        .n_WR     (n_WR),
        .n_CAS    (n_CAS),
        .OSC      (OSC),
        .n_MREQ   (n_MREQ),
        .A15      (A15),
        .A14      (A14),
        .n_RAS    (n_RAS),
        .n_ROMCS  (n_ROMCS),
        .n_IOREQ  (n_IOREQ),
        .n_PHICPU (n_PHICPU),
        .D7       (busD[7]),
        .D6       (busD[6]),
        .D5       (busD[5]),
        .D4       (busD[4]),
        .SOUND    (SOUND),
        .KB4      (KB4),
        .D3       (busD[3]),
        .D2       (busD[2]),
        .D1       (busD[1]),
        .D0       (busD[0]),
        .KB0      (KB0),
        .KB1      (KB1),
        .KB2      (KB2),
        .KB3      (KB3),
        .n_Yout   (n_Yout),
        .Vout     (Vout),
        .Uout     (Uout)
    );

    // ------------------------------------------------------------------ DRAM
    dram_ula dram (
        .D      (busD),
        .A      (busA),
        .nWRITE (n_WE),
        .nRAS   (n_RAS),
        .nCAS   (n_CAS)
    );

    // ------------------------------------------------------------------ osc
    always #25 OSC = ~OSC;

    // ------------------------------------------------------------------ self-check scaffolding
    reg [8:0] V_prev = 9'bxxxxxxxxx;
    wire [8:0] V_now = ula_inst.V;
    integer   line_count   = 0;   // HCrst rising edges
    integer   v_ok_count   = 0;   // lines where V advanced by exactly 1 (mod 312)
    integer   v_bad_count  = 0;   // lines where V did not
    longint   last_hcrst   = 0;
    integer   bad_line_len = 0;
    longint   nclk_edges   = 0;   // nCLK7 edges (negedge counted)
    integer   nint_count   = 0;   // n_INT pulses

    always @(posedge ula_inst.HCrst) begin
        if (line_count > 0) begin
            if (last_hcrst != 0 && $time - last_hcrst != 44800)
                bad_line_len = bad_line_len + 1;
            if (V_prev !== 9'bx) begin
                if (V_now == ((V_prev + 1) % 312))
                    v_ok_count = v_ok_count + 1;
                else
                    v_bad_count = v_bad_count + 1;
            end
        end
        V_prev = V_now;
        last_hcrst = $time;
        line_count = line_count + 1;
    end

    always @(negedge ula_inst.nCLK7) begin
        nclk_edges = nclk_edges + 1;
    end

    always @(negedge n_INT) begin
        nint_count = nint_count + 1;
    end

    // ------------------------------------------------------------------ run
    longint t_end;

    initial begin
        t_end = RUN_NS;
        if (!$value$plusargs("run_ns=%0d", t_end))
            t_end = RUN_NS;

        $dumpfile("ula_run_idle.vcd");
        $dumpvars(0, ULA_Run);

        $display("=== ULA 6C001 idle+DRAM run, %0d ns ===", t_end);
        #(t_end);
        $display("lines (HCrst rises)      : %0d", line_count);
        $display("nCLK7 rising edges       : %0d", nclk_edges);
        $display("lines with V+1 (mod 312) : %0d", v_ok_count);
        $display("lines with bad V step    : %0d", v_bad_count);
        $display("bad line lengths (44800) : %0d", bad_line_len);
        $display("n_INT pulses             : %0d", nint_count);
        if (v_bad_count > 0)
            $error("vcounter: %0d bad V steps", v_bad_count);
        if (bad_line_len > 0)
            $error("hcounter: %0d lines with wrong length", bad_line_len);
        $finish;
    end

endmodule // ULA_Run
