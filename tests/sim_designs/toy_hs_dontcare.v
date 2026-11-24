// TEST-ONLY variant of toy_hs (see toy_hs.v): q differs only while v = 0.
module toy_hs(input clk, input rst, input en, input [1:0] d, output reg v, output reg [1:0] q);
  always @(posedge clk) begin
    if (rst) begin v <= 1'b0; q <= 2'b00; end
    else begin v <= en; q <= en ? d : 2'b11; end
  end
endmodule
