`timescale 1ns/1ps

module counter_tb;
    // Inputs are reg
    reg clk;
    reg rst;
    reg enable;
    // Outputs are wire
    wire [7:0] count_out;

    counter dut (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count_out)
    );

    // Clock generation block
    always #5 clk = ~clk;

    initial begin
        $dumpfile("out/waves.vcd");
        $dumpvars(0, counter_tb);
        
        $monitor("Time=%0t | rst=%b, en=%b | count=%d", $time, rst, enable, count_out);

        // Initialize signals
        clk = 0;
        rst = 1;
        enable = 0;

        // TODO: Release reset and apply stimulus
        #15 rst = 0;
        
        // Let it run for a bit
        #100 $finish;
    end
endmodule
