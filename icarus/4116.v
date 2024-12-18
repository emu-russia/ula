// Model for the classic MOSTEK 4116 16384 x 1 Bit Dynamic Ram

module MK4116 (Din, Dout, nWRITE, nRAS, nCAS, A);

	input wire Din;
	output reg Dout;
	input wire nWRITE;
	input wire nRAS;
	input wire nCAS;
	input wire [6:0] A;

	reg memory [16383:0];
	reg [6:0] row_latch;
	reg [6:0] col_latch;
	wire [13:0] mem_addr;

	// Latch Row and Column

	always @ (negedge nRAS) begin
		row_latch <= A;
	end

	always @ (negedge nCAS) begin
		col_latch <= A;
	end

	assign mem_addr = {row_latch, col_latch};

	// READ CYCLE

	always @ (posedge nCAS) begin
		if (nWRITE) begin
			Dout <= memory[mem_addr];
		end
	end

	// WRITE CYCLE (EARLY WRITE)

	always @ (negedge nCAS) begin
		if (! nWRITE) begin
			memory[mem_addr] <= Din;
		end
	end

	// TBD: READ-WRITE/READ-MODIFY-WRITE CYCLE
	// TBD: RAS-ONLY REFRESH CYCLE
	// TBD: PAGE MODE READ CYCLE
	// TBD: PAGE MODE WRITE CYCLE

	integer j;
	initial begin
		// Pre-fill the memory with some value so we don't run into `xx`
		for(j = 0; j < 16384; j = j+1) 
			memory[j] = 0;
	end

endmodule // MK4116