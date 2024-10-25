`timescale 1ns/1ns

module ULA_Run ();

	reg OSC;
	wire KB0;
	wire n_INT;
	wire n_PHICPU;

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
		.n_PHICPU(n_PHICPU) );

	pullup p1 (n_INT);
	pullup p2 (n_PHICPU);

	initial begin

		$display("Check that the ULA is moving.");

		OSC <= 1'b0;

		$dumpfile("ula_waves.vcd");
		$dumpvars(0, ULA_Run);

		repeat (1000) @ (posedge OSC);
		$finish;
	end

endmodule // ULA_Run
