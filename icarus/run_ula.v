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

	// Cadence
	wire nCLK7;
	wire [8:0] C;
	wire [8:0] V;
	// Video Signal Features
	wire nBorder;
	wire nHSyncPulses;
	wire C5delay;
	wire HSync;
	wire nSync;
	wire nHBlank;
	wire Burst;
	wire nINT;
	wire Timing;
	wire VSync;
	// Latch Control
	wire nVidC3;
	wire nDataLatch;
	wire SLoad;
	wire nVidEn;
	wire nAttrLatch;
	wire nAOLatch;
	// Video address generator
	wire nAE;
	// RAS/CAS
	wire RAM16;
	wire VidRAS;
	wire VidCASAC;
	wire VidCASBD;
	wire nCAS;
	wire MUXSEL;
	wire nWE;
	wire nRAS;
	wire nROMCS;
	// Latches + Pixel Shift Register
	wire [7:0] DataLatch;
	wire [7:0] AttrLatch;
	wire [7:0] AOLatch;
	wire [7:0] Pixel;
	// Flash Clock + XNOR + Mux
	wire FlashClock;
	wire nDataSelect;
	wire PB0_B;
	wire PB1_R;
	wire PB2_G;
	wire AL6_HL;
	wire AL7_FL;
	// VideoDAC Setup
	wire RedS;
	wire RedD;
	wire nRedDD;
	wire nGreenS;
	wire GreenD;
	wire nGreenDD;
	wire nBlueS;
	wire BlueD;
	wire BlueDD;
	wire BurstS;
	wire nBurstDD;
	wire nBurstS;	
	wire nBLACKS;
	wire nHL;
	// I/O
	wire nPortRD;
	wire nPortWR;
	wire Ear;
	wire Tape;
	wire Speaker;
	wire B0_B;
	wire B1_R;
	wire B2_G;

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

	assign nBorder = ula_inst.g614.x;
	assign nHSyncPulses = ula_inst.g84.x;
	assign C5delay = ula_inst.g172.x;
	assign HSync = ula_inst.g105.x;
	assign nSync = ula_inst.g106.x;
	assign nHBlank = ula_inst.g131.x;
	assign Burst = ula_inst.g520.x;
	assign nINT = ula_inst.g4.x;
	assign Timing = ula_inst.g151.x;
	assign VSync = ula_inst.g621.x;

	assign nVidC3 = ula_inst.g50.x;
	assign nDataLatch = ula_inst.g51.x;
	assign SLoad = ula_inst.g443.x;
	assign nVidEn = ula_inst.g467.x;
	assign nAttrLatch = ula_inst.g47.x;
	assign nAOLatch = ula_inst.g46.x;

	assign nAE = ula_inst.g615.x;

	assign RAM16 = ula_inst.g389.x;
	assign VidRAS = ula_inst.g451.x;
	assign VidCASAC = ula_inst.g477.x;
	assign VidCASBD = ula_inst.g475.x;
	assign nCAS = ula_inst.g74.x;
	assign MUXSEL = ula_inst.g503.x;
	assign nWE = ula_inst.g87.x;
	assign nRAS = ula_inst.g390.x;
	assign nROMCS = ula_inst.g39.x;

	assign DataLatch[0] = ula_inst.g247.x;
	assign DataLatch[1] = ula_inst.g282.x;
	assign DataLatch[2] = ula_inst.g315.x;
	assign DataLatch[3] = ula_inst.g345.x;
	assign DataLatch[4] = ula_inst.g378.x;
	assign DataLatch[5] = ula_inst.g348.x;
	assign DataLatch[6] = ula_inst.g352.x;
	assign DataLatch[7] = ula_inst.g356.x;

	assign AttrLatch[0] = ula_inst.g222.x;
	assign AttrLatch[1] = ula_inst.g254.x;
	assign AttrLatch[2] = ula_inst.g288.x;
	assign AttrLatch[3] = ula_inst.g321.x;
	assign AttrLatch[4] = ula_inst.g373.x;
	assign AttrLatch[5] = ula_inst.g349.x;
	assign AttrLatch[6] = ula_inst.g353.x;
	assign AttrLatch[7] = ula_inst.g357.x;

	assign AOLatch[0] = ula_inst.g228.x;
	assign AOLatch[1] = ula_inst.g273.x;
	assign AOLatch[2] = ula_inst.g240.x;
	assign AOLatch[3] = ula_inst.g296.x;
	assign AOLatch[4] = ula_inst.g262.x;
	assign AOLatch[5] = ula_inst.g305.x;
	assign AOLatch[6] = ula_inst.g330.x;
	assign AOLatch[7] = ula_inst.g304.x;

	assign Pixel[0] = ula_inst.g482.x;
	assign Pixel[1] = ula_inst.g465.x;
	assign Pixel[2] = ula_inst.g456.x;
	assign Pixel[3] = ula_inst.g442.x;
	assign Pixel[4] = ula_inst.g433.x;
	assign Pixel[5] = ula_inst.g421.x;
	assign Pixel[6] = ula_inst.g412.x;
	assign Pixel[7] = ula_inst.g400.x;

	assign FlashClock = ula_inst.g192.x;
	assign nDataSelect = ula_inst.g190.x;
	assign PB0_B = ula_inst.g291.x;
	assign PB1_R = ula_inst.g325.x;
	assign PB2_G = ula_inst.g292.x;
	assign AL6_HL = ula_inst.g309.x;
	assign AL7_FL = ula_inst.g326.x;

	assign RedS = ula_inst.g1.x;
	assign RedD = ula_inst.g15.x;
	assign nRedDD = ula_inst.g173.x;
	assign nGreenS = ula_inst.g153.x; 
	assign GreenD = ula_inst.g16.x; 
	assign nGreenDD = ula_inst.g179.x;
	assign nBlueS = ula_inst.g625.x;
	assign BlueD = ula_inst.g20.x; 
	assign BlueDD = ula_inst.g21.x;
	assign BurstS = ula_inst.g117.x;
	assign nBurstDD = ula_inst.g10.x;
	assign nBurstS = ula_inst.g6.x;	
	assign nBLACKS = ula_inst.g19.x;
	assign nHL = ula_inst.g23.x;

	assign nPortRD = ula_inst.g80.x;
	assign nPortWR = ula_inst.g77.x;
	assign Ear = ula_inst.g317.a;
	assign Tape = ula_inst.g323.x;
	assign Speaker = ula_inst.g371.x;
	assign B0_B = ula_inst.g224.x;
	assign B1_R = ula_inst.g256.x;
	assign B2_G = ula_inst.g290.x;

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
