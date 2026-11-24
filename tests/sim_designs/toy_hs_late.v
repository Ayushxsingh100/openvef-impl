// TEST-ONLY variant of toy_hs (see toy_hs.v): q differs while v = 1, but only on the
// second consecutive enabled cycle, so the shortest counterexample needs two enables.
module toy_hs(input clk, input rst, input en, input [1:0] d, output reg v, output reg [1:0] q);
  reg seen;
  always @(posedge clk) begin
    if (rst) begin v <= 1'b0; q <= 2'b00; seen <= 1'b0; end
    else begin v <= en; seen <= en; q <= en ? (seen ? (d ^ 2'b01) : d) : 2'b00; end
  end
endmodule
