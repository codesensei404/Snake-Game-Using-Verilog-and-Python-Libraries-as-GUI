`timescale 1ns/1ps

module snake_tb;

    parameter BOARD_WIDTH = 20;
    parameter BOARD_HEIGHT = 20;
    parameter ADDR_WIDTH = 5; 

    reg clk;
    reg reset;
    reg test_enable; 
    reg [1:0] direction;
    reg [ADDR_WIDTH-1:0] head_x;
    reg [ADDR_WIDTH-1:0] head_y;

    wire [ADDR_WIDTH-1:0] next_head_x;
    wire [ADDR_WIDTH-1:0] next_head_y;

    snake_logic #(
        .BOARD_WIDTH(BOARD_WIDTH),
        .BOARD_HEIGHT(BOARD_HEIGHT),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) UUT (
        .clk(clk),
        .reset(reset),
        .direction(direction),
        .head_x(head_x),
        .head_y(head_y),
        .next_head_x(next_head_x),
        .next_head_y(next_head_y)
    );

    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end


    initial begin
        $dumpfile("snake_waves.vcd");
        $dumpvars(0, snake_tb);
        $display("VCD file snake_waves.vcd generated.");
    end

    always @(posedge clk) begin
        if (!reset && test_enable) begin

            head_x <= next_head_x;
            head_y <= next_head_y;
        end
    end

    initial begin

        reset = 1;
        test_enable = 0;
        direction = 2'b00; 
        head_x = 10;
        head_y = 10;
        
        #20 reset = 0; 

        @(posedge clk);
        
        $display("--- Test 1: Moving East (No wrap, 20 cycles) ---");
        test_enable = 1; 
        direction = 2'b01; 
        #400; 

        $display("--- Test 2: Wrap-around East (X=19 -> 0) ---");
        test_enable = 0; 
        @(posedge clk); 
        
        head_x = 19;
        head_y = 10;
        
        test_enable = 1; 
        direction = 2'b01; 
        #40;

        $display("--- Test 3: Wrap-around North (Y=0 -> 19) ---");
        test_enable = 0; 
        @(posedge clk); 

        head_x = 10;
        head_y = 0;
        
        test_enable = 1; 
        direction = 2'b00; 
        #40; 

        $display("Test sequence complete.");
        test_enable = 0;
        #10 $finish;
    end

endmodule