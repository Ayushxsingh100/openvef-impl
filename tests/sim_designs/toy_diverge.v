// TEST-ONLY: differs from toy.v on `flag` after reset (masked-divergence test).
module toy(input clk, input rst, input [1:0] a, input b, output reg [1:0] q, output reg flag);
  always @(posedge clk) begin
    if (rst) begin q <= 2'b00; flag <= 1'b0; end
    else begin q <= a; flag <= ~b; end
  end
endmodule
