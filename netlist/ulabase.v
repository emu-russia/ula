// Module Definitions [It is possible to wrap here on your primitives]

module ula_not (  a, x);

	input wire a;
	output wire x;

	not (x, a);

endmodule // ula_not

module ula_nor (  a, b, x);

	input wire a;
	input wire b;
	output reg x;

	// To simulate RS flip flops we use behavioral model

	always @ (a or b) begin
	    if (a == 1'b0 && b == 1'b0) begin
	        x = 1'b1;
	    end
	    else 
	        x = 1'b0; 
	end	

	// nor (x, a, b);

endmodule // ula_nor

module ula_nor3 (  b, a, c, x);

	input wire b;
	input wire a;
	input wire c;
	output wire x;

	nor (x, a, b, c);

endmodule // ula_nor3

module ula_nor4 (  a, b, c, d, x);

	input wire a;
	input wire b;
	input wire c;
	input wire d;
	output wire x;

	nor (x, a, b, c, d);

endmodule // ula_nor4

module ula_nor5 (  a, b, c, d, e, x);

	input wire a;
	input wire b;
	input wire c;
	input wire d;
	input wire e;
	output wire x;

	nor (x, a, b, c, d, e);

endmodule // ula_nor5

module ula_nor7 (  a, b, c, d, e, f, g, x);

	input wire a;
	input wire b;
	input wire c;
	input wire d;
	input wire e;
	input wire f;
	input wire g;
	output wire x;

	nor (x, a, b, c, d, e, f, g);

endmodule // ula_nor7

module ula_nor6 (  a, b, c, d, e, f, x);

	input wire a;
	input wire b;
	input wire c;
	input wire d;
	input wire e;
	input wire f;
	output wire x;

	nor (x, a, b, c, d, e, f);

endmodule // ula_nor6

module ula_pad_we_output (  pad, to_pad);

	output wire pad;
	input wire to_pad;

	assign pad = to_pad == 1'b0 ? to_pad : 1'bz;

endmodule // ula_pad_we_output

module ula_pad_rd_input (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_rd_input

module ula_pad_wr_input (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_wr_input

module ula_pad_cas_output (  pad, to_pad);

	output wire pad;
	input wire to_pad;

	assign pad = to_pad == 1'b0 ? to_pad : 1'bz;

endmodule // ula_pad_cas_output

module ula_pad_osc (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_osc

module ula_pad_mreq_input (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_mreq_input

module ula_pad_addr_input (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_addr_input

module ula_pad_ras_output (  pad, n_oe, to_pad);

	output wire pad;
	input wire n_oe;
	input wire to_pad;

	assign pad = n_oe == 1'b0 ? to_pad : 1'bz;

endmodule // ula_pad_ras_output

module ula_pad_romcs_output (  pad, to_pad);

	output wire pad;
	input wire to_pad;

	assign pad = to_pad == 1'b0 ? to_pad : 1'bz;

endmodule // ula_pad_romcs_output

module ula_pad_ioreq_input (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_ioreq_input

module ula_pad_phi_output (  pad, to_pad);

	output wire pad;
	input wire to_pad;

	// Inverting open-collector
	wire temp;
	assign temp = ~to_pad;
	assign pad = temp == 1'b0 ? temp : 1'bz;

endmodule // ula_pad_phi_output

module ula_pad_data_bidir (  pad, to_pad, from_pad);

	inout wire pad;
	input wire to_pad;
	output wire from_pad;

	assign pad = to_pad == 1'b0 ? to_pad : 1'bz;
	assign from_pad = pad;

endmodule // ula_pad_data_bidir

module ula_pad_data_input (  from_pad, pad);

	output wire from_pad;
	input wire pad;

	assign from_pad = pad;

endmodule // ula_pad_data_input

module ula_SoundDAC (  pad, from_pad, to_pad1, to_pad2);

	inout wire pad;
	output wire from_pad;
	input wire to_pad1;
	input wire to_pad2;

endmodule // ula_SoundDAC

module ula_pad_kb_input (  pad, from_pad);

	input wire pad;
	output wire from_pad;

	assign from_pad = pad;

endmodule // ula_pad_kb_input

module ula_pad_kb_bidir (  pad, from_pad, to_pad);

	inout wire pad;
	output wire from_pad;
	input wire to_pad;

	assign from_pad = pad;
	assign pad = to_pad == 1'b0 ? 1'b0 : 1'bz;

endmodule // ula_pad_kb_bidir

module ula_VideoDAC (  u, v, ny, i14, i13, i12, i11, i10, i9, i8, i7, i6, i5, i4, i3, i2, i1, i0);

	output wire u;
	output wire v;
	output wire ny;
	input wire i14;
	input wire i13;
	input wire i12;
	input wire i11;
	input wire i10;
	input wire i9;
	input wire i8;
	input wire i7;
	input wire i6;
	input wire i5;
	input wire i4;
	input wire i3;
	input wire i2;
	input wire i1;
	input wire i0;

endmodule // ula_VideoDAC

module ula_pad_addr_bidir (  pad, n_oe, from_pad, to_pad);

	inout wire pad;
	input wire n_oe;
	output wire from_pad;
	input wire to_pad;

	assign pad = n_oe == 1'b0 ? to_pad : 1'bz;
	assign from_pad = pad;

endmodule // ula_pad_addr_bidir

module ula_pad_addr_output (  pad, n_oe, to_pad);

	output wire pad;
	input wire n_oe;
	input wire to_pad;

	assign pad = n_oe == 1'b0 ? to_pad : 1'bz;

endmodule // ula_pad_addr_output

module ula_pad_int_output (  pad, to_pad);

	output wire pad;
	input wire to_pad;

	assign pad = to_pad == 1'b0 ? to_pad : 1'bz;

endmodule // ula_pad_int_output
