`timescale 1ns/1ns

module ULA_Run ();

	reg OSC;
	wire KB0;
	wire n_INT;
	wire n_PHICPU;
	wire [6:0] addr;

	always #25 OSC = ~OSC;

	// Not all ports are connected, those that are Output can be viewed in the VCD

	assign KB0 = 1'b0;

	ula ula_inst (
		.n_RD(1'b1),
		.n_WR(1'b1),
		.OSC(OSC),
		.n_MREQ(1'b1),
		.A15(1'b0),
		.A14(1'b0),
		.n_IOREQ(1'b1),
		.KB4(1'b0),
		.KB0(KB0),
		.KB1(1'b0),
		.KB2(1'b0),
		.KB3(1'b0),
		.n_INT(n_INT),
		.n_PHICPU(n_PHICPU),
		.A0(addr[0]),
		.A1(addr[1]),
		.A2(addr[2]),
		.A3(addr[3]),
		.A4(addr[4]),
		.A5(addr[5]),
		.A6(addr[6]) );

	pullup p1 (n_INT);
	pullup p2 (n_PHICPU);

	// Signals for debugging (by Chris Smith)

	// Cadence
	wire nCLK7;
	wire [8:0] C;
	wire [8:0] V;
	// Video Signal Features
	// Latch Control
	// Video address generator
	// RAS/CAS
	// Latches
	// Pixel Shift Register
	// Flash Clock + XNOR
	// Mux
	// VideoDAC Setup
	// I/O
	// Contention Handler	

	assign nCLK7 = ula_inst.g54.x;

	assign C[0] = ula_inst.g454.x;
	assign C[1] = ula_inst.g472.x;
	assign C[2] = ula_inst.g524.x;
	assign C[3] = ula_inst.g509.x;
	assign C[4] = ula_inst.g521.x;
	assign C[5] = ula_inst.g519.x;
	assign C[6] = ula_inst.g103.x;
	assign C[7] = ula_inst.g112.x;
	assign C[8] = ula_inst.g129.x;

	assign V[0] = ula_inst.g141.x;
	assign V[1] = ula_inst.g161.x;
	assign V[2] = ula_inst.g132.x;
	assign V[3] = ula_inst.g537.x;
	assign V[4] = ula_inst.g549.x;
	assign V[5] = ula_inst.g575.x;
	assign V[6] = ula_inst.g599.x;
	assign V[7] = ula_inst.g595.x;
	assign V[8] = ula_inst.g565.x;

	// ------------ END Signals for debugging

	initial begin

		$display("Check that the ULA is moving.");

		OSC <= 1'b0;

		$dumpfile("ula_waves.vcd");
		$dumpvars(0, ULA_Run);

		repeat (1000) @ (posedge OSC);
		$finish;
	end

endmodule // ULA_Run
