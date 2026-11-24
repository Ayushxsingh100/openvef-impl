// TEST-ONLY toy design for the miter/pair-runner unit tests. Not a FIFO, not an OpenVEF
// design, not a control mutant, not derived from any owner material. A registered
// valid/data output: q is a don't-care while v = 0 (in the toy mask used by the tests).
module toy_hs(input clk, input rst, input en, input [1:0] d, output reg v, output reg [1:0] q);
  always @(posedge clk) begin
    if (rst) begin v <= 1'b0; q <= 2'b00; end
    else begin v <= en; q <= en ? d : 2'b00; end
  end
endmodule
