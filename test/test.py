import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

def set_ui(dut, en=0, dir=1, load=0, oe=0):
    dut.ui_in.value = (oe << 3) | (load << 2) | (dir << 1) | en

@cocotb.test()
async def test_load_count_tristate(dut):
    # 10 MHz clock (100 ns period)
    cocotb.start_soon(Clock(dut.clk, 100, units="ns").start())

    # Reset
    dut.rst_n.value = 0
    dut.ena.value   = 1
    dut.uio_in.value = 0
    dut.ui_in.value  = 0
    await Timer(1, units="us")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # 1) Sync load 0xA5 from uio_in
    dut.uio_in.value = 0xA5
    set_ui(dut, en=0, dir=1, load=1, oe=0)
    await RisingEdge(dut.clk)   # load happens here
    set_ui(dut, en=0, dir=1, load=0, oe=0)
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0xA5

    # 2) Count up 3 cycles → 0xA8
    set_ui(dut, en=1, dir=1, load=0, oe=0)
    for _ in range(3):
        await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0xA8

    # 3) Drive tri-state bus
    set_ui(dut, en=1, dir=1, load=0, oe=1)
    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) == int(dut.uo_out.value)
    assert int(dut.uio_oe.value)  == 0xFF

    # 4) Count down 5 → 0xA3
    set_ui(dut, en=1, dir=0, load=0, oe=1)
    for _ in range(5):
        await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0xA3
