// dram_ula.v — behavioral 8x4116-style DRAM array for the ULA chip testbench.
//
// Mirrors the semantics of the python reference model (ulasim.py -> Dram):
//   - row latched at negedge nRAS,
//   - column latched at negedge nCAS,
//   - EARLY WRITE (nWRITE low): data written at negedge nCAS,
//   - read completes at posedge nCAS: drives the (inout) D bus,
//   - tri-state output with pull-ups handled in the testbench (idle = 0xFF).
//
// Memory content is deterministic ("checker" pattern, same formula as
// ulasim.py) so video fetches produce a lively, realistic data stream.

`timescale 1ns/1ns

module dram_ula (
    inout  wire [7:0] D,
    input  wire [6:0] A,
    input  wire nWRITE,      // high = read (n_WE of the board, 4116 /WE style)
    input  wire nRAS,
    input  wire nCAS
);
    reg [7:0] mem [0:16383];
    reg [6:0] row_latch;
    reg [6:0] col_latch;
    reg [7:0] out;
    reg       driving;

    integer j;

    initial begin
        for (j = 0; j < 16384; j = j + 1)
            mem[j] = (j * 7 + (j >> 7) * 3) & 8'hFF;   // checker pattern
        out     = 8'hFF;
        driving = 1'b0;
    end

    always @(negedge nRAS) begin
        row_latch <= A;
    end

    always @(negedge nCAS) begin
        col_latch <= A;
        if (!nWRITE)                        // early write
            mem[{row_latch, col_latch}] <= D;
    end

    always @(posedge nCAS) begin
        if (nWRITE) begin                   // read cycle completes
            out     <= mem[{row_latch, col_latch}];
            driving <= 1'b1;
        end
    end

    assign D = driving ? out : 8'bz;

endmodule // dram_ula
