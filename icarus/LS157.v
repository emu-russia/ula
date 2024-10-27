// LS157 QUAD 2-INPUT MULTIPLEXER

module LS157 (S, nE, A1, A2, A3, A4, B1, B2, B3, B4, Y1, Y2, Y3, Y4 );

	input S;
	input nE;
	input A1;
	input A2;
	input A3;
	input A4;
	input B1;
	input B2;
	input B3;
	input B4;
	input Y1;
	input Y2;
	input Y3;
	input Y4;

	assign Y1 = nE == 1'b0 ? : (S ? B1 : A1) : 1'b0;
	assign Y2 = nE == 1'b0 ? : (S ? B2 : A2) : 1'b0;
	assign Y3 = nE == 1'b0 ? : (S ? B3 : A3) : 1'b0;
	assign Y4 = nE == 1'b0 ? : (S ? B4 : A4) : 1'b0;

endmodule // LS157