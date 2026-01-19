`timescale 1ns/1ps

module snake_logic #(
    parameter BOARD_WIDTH = 20,
    parameter BOARD_HEIGHT = 20,
    parameter ADDR_WIDTH = 5 
) (
    input wire clk,
    input wire reset,

    input wire [1:0] direction,
    input wire [ADDR_WIDTH-1:0] head_x,
    input wire [ADDR_WIDTH-1:0] head_y,

    output reg [ADDR_WIDTH-1:0] next_head_x,
    output reg [ADDR_WIDTH-1:0] next_head_y
);

    reg [ADDR_WIDTH:0] new_x, new_y; 
    
    localparam DIR_NORTH = 2'b00;
    localparam DIR_EAST  = 2'b01;
    localparam DIR_SOUTH = 2'b10;
    localparam DIR_WEST  = 2'b11;

    always @(*) begin
        case (direction)
            DIR_NORTH: begin
                new_x = {1'b0, head_x};
                new_y = {1'b0, head_y} - 6'd1;
            end
            DIR_EAST: begin
                new_x = {1'b0, head_x} + 6'd1;
                new_y = {1'b0, head_y};
            end
            DIR_SOUTH: begin
                new_x = {1'b0, head_x};
                new_y = {1'b0, head_y} + 6'd1;
            end
            DIR_WEST: begin
                new_x = {1'b0, head_x} - 6'd1;
                new_y = {1'b0, head_y};
            end
            default: begin
                new_x = {1'b0, head_x};
                new_y = {1'b0, head_y};
            end
        endcase
    end

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            next_head_x <= BOARD_WIDTH / 2;
            next_head_y <= BOARD_HEIGHT / 2;
        end else begin
            if (new_x == BOARD_WIDTH) begin
                next_head_x <= 0;
            end else if (new_x == {ADDR_WIDTH+1{1'b1}}) begin 
                next_head_x <= BOARD_WIDTH - 1; // 19
            end else begin
                next_head_x <= new_x[ADDR_WIDTH-1:0]; 
            end

            if (new_y == BOARD_HEIGHT) begin
                next_head_y <= 0;
            end else if (new_y == {ADDR_WIDTH+1{1'b1}}) begin 
                next_head_y <= BOARD_HEIGHT - 1; // 19
            end else begin
                next_head_y <= new_y[ADDR_WIDTH-1:0];
            end
        end
    end

endmodule