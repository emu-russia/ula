`timescale 1ns/1ns

module ULA_Run ();

	reg OSC;
	wire KB0;
	wire n_INT;
	wire n_PHICPU;
	wire [6:0] A;
	wire [7:0] D;
	wire n_WRITE;
	wire n_RAS;
	wire n_CAS;

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
		.A0(A[0]),
		.A1(A[1]),
		.A2(A[2]),
		.A3(A[3]),
		.A4(A[4]),
		.A5(A[5]),
		.A6(A[6]),
		.D0(D[0]), 
		.D1(D[1]),
		.D2(D[2]),
		.D3(D[3]),
		.D4(D[4]),
		.D5(D[5]),
		.D6(D[6]),
		.D7(D[7]),
		.n_WE(n_WRITE),
		.n_RAS(n_RAS),
		.n_CAS(n_CAS) );

	pullup p1 (n_INT);
	pullup p2 (n_PHICPU);

	// Signals for debugging (by Chris Smith)

	// TBD.
	
	// ------------ END Signals for debugging

	// DRAM

	pullup (D[0]);
	pullup (D[1]);
	pullup (D[2]);
	pullup (D[3]);
	pullup (D[4]);
	pullup (D[5]);
	pullup (D[6]);
	pullup (D[7]);

	MK4116 d0_lane (.Din(D[0]), .Dout(D[0]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d1_lane (.Din(D[1]), .Dout(D[1]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d2_lane (.Din(D[2]), .Dout(D[2]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d3_lane (.Din(D[3]), .Dout(D[3]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d4_lane (.Din(D[4]), .Dout(D[4]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d5_lane (.Din(D[5]), .Dout(D[5]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d6_lane (.Din(D[6]), .Dout(D[6]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );
	MK4116 d7_lane (.Din(D[7]), .Dout(D[7]), .nWRITE(n_WRITE), .nRAS(n_RAS), .nCAS(n_CAS), .A(A) );

	initial begin

		$display("Check that the ULA is moving.");

		OSC <= 1'b0;

		$dumpfile("ula_waves.vcd");
		$dumpvars(0, ULA_Run);

		repeat (1000) @ (posedge OSC);
		$finish;
	end

endmodule // ULA_Run
