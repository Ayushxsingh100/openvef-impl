// TEST-ONLY: the toy design written in a different style (stand-in for a null netlist).
module toy(input clk, input rst, input [1:0] a, input b, output [1:0] q, output flag);
  reg [2:0] r;
  always @(posedge clk) r <= rst ? 3'b000 : {b, a};
  assign q = r[1:0];
  assign flag = r[2];
endmodule
