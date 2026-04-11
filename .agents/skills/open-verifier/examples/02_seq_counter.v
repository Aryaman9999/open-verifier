// Sequential Example: 8-bit Counter with synchronous reset
module counter (
    input  wire clk,
    input  wire rst,
    input  wire enable,
    output reg  [7:0] count
);
    // Use <= for sequential logic
    always @(posedge clk) begin
        if (rst) begin
            count <= 8'd0;
        end else if (enable) begin
            count <= count + 1'b1;
        end
    end
endmodule
