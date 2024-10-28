// LS157 QUAD 2-INPUT MULTIPLEXER

module LS157 (S, nE, A, B, Y );

	input S;
	input nE;
	input [3:0] A;
	input [3:0] B;
	input [3:0] Y;

	assign Y[0] = nE == 1'b0 ? : (S ? B[0] : A[0]) : 1'b0;
	assign Y[1] = nE == 1'b0 ? : (S ? B[1] : A[1]) : 1'b0;
	assign Y[2] = nE == 1'b0 ? : (S ? B[2] : A[2]) : 1'b0;
	assign Y[3] = nE == 1'b0 ? : (S ? B[3] : A[3]) : 1'b0;

endmodule // LS157