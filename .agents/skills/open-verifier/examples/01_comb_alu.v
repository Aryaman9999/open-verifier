// Combinational Example: Simple ALU
module alu (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire [1:0] sel,
    output reg  [3:0] out
);
    // Use = for combinational logic
    always @(*) begin
        case (sel)
            2'b00: out = a + b;
            2'b01: out = a - b;
            2'b10: out = a & b;
            2'b11: out = a | b;
            default: out = 4'b0000;
        endcase
    end
endmodule
