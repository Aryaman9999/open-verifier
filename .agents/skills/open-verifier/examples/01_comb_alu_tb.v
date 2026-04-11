`timescale 1ns/1ps

module alu_tb;
    // Inputs are reg
    reg  [3:0] tb_a;
    reg  [3:0] tb_b;
    reg  [1:0] tb_sel;
    // Outputs are wire
    wire [3:0] tb_out;

    // Strict named port mapping
    alu dut (
        .a(tb_a),
        .b(tb_b),
        .sel(tb_sel),
        .out(tb_out)
    );

    initial begin
        $dumpfile("out/waves.vcd");
        $dumpvars(0, alu_tb);
        
        $monitor("Time=%0t | a=%b, b=%b, sel=%b | out=%b", $time, tb_a, tb_b, tb_sel, tb_out);

        // TODO: Apply test vectors here
        tb_a = 4'b0000; tb_b = 4'b0000; tb_sel = 2'b00;
        #10;
        
        $finish;
    end
endmodule
