// 8-bit programmable counter with synchronous load and tri-state bus
// Tiny Tapeout user module interface
// Top must be named exactly as info.yaml: tt_um_immrudul_counter

module tt_um_immrudul_counter (
    // TT standard ports
    input  wire [7:0] ui_in,     // dedicated inputs
    output wire [7:0] uo_out,    // dedicated outputs
    input  wire [7:0] uio_in,    // bidir in
    output wire [7:0] uio_out,   // bidir out
    output wire [7:0] uio_oe,    // bidir oe (1=drive)
    input  wire       ena,       // design enable (from harness)
    input  wire       clk,       // clock
    input  wire       rst_n      // async active-low reset
);

    // Control bits
    wire en    = ui_in[0];  // count enable
    wire dir   = ui_in[1];  // 1=up, 0=down
    wire load  = ui_in[2];  // synchronous load from uio_in
    wire oe    = ui_in[3];  // drive uio_out bus when 1

    // Counter register
    reg [7:0] count;

    // Next-state logic for increment/decrement
    wire [7:0] inc = count + 8'd1;
    wire [7:0] dec = count - 8'd1;

    // Synchronous state update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'h00;
        end else if (!ena) begin
            // When harness de-asserts ena, hold state
            count <= count;
        end else if (load) begin
            // Sync load from tri-state input bus
            count <= uio_in;
        end else if (en) begin
            count <= dir ? inc : dec;
        end
        // else hold
    end

    // Always mirror the count to the dedicated outputs for visibility
    assign uo_out = count;

    // Tri-state bus behavior:
    // - When OE=1, drive the counter value onto the bus.
    // - When OE=0, high-Z (by deasserting oe bits, uio_out value is ignored).
    assign uio_out = count;
    assign uio_oe  = {8{oe}};

endmodule
