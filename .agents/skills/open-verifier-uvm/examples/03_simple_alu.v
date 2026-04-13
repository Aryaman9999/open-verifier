// =============================================================================
// Module: simple_alu
// Description: 8-bit ALU with four operations (ADD, SUB, AND, OR).
//              Synchronous reset. 9-bit output to capture carry/overflow.
//              This is a teaching example for the open-verifier UVM tier.
// =============================================================================

module simple_alu (
    input  wire       clk,        // Clock signal
    input  wire       rst,        // Synchronous active-high reset
    input  wire [7:0] a,          // 8-bit operand A
    input  wire [7:0] b,          // 8-bit operand B
    input  wire [1:0] op,         // Operation selector:
                                  //   2'b00 = ADD
                                  //   2'b01 = SUB
                                  //   2'b10 = AND
                                  //   2'b11 = OR
    output reg  [8:0] result      // 9-bit result (extra bit for carry/overflow)
);

    // -------------------------------------------------------------------------
    // Synchronous always block:
    //   - On reset, result is cleared to zero.
    //   - Otherwise, the selected operation is performed on each rising clock
    //     edge and the result is registered.
    // -------------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            // Synchronous reset: clear output
            result <= 9'b0;
        end else begin
            case (op)
                2'b00: result <= {1'b0, a} + {1'b0, b};  // ADD — zero-extend to 9 bits for carry
                2'b01: result <= {1'b0, a} - {1'b0, b};  // SUB — zero-extend to 9 bits for borrow
                2'b10: result <= {1'b0, a & b};           // AND — bitwise, MSB is always 0
                2'b11: result <= {1'b0, a | b};           // OR  — bitwise, MSB is always 0
                default: result <= 9'b0;                  // Safety fallback
            endcase
        end
    end

endmodule
