import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock


def set_ui(dut, en=0, dir=1, load=0, oe=0):
    """Pack EN, DIR, LOAD, OE into ui_in[3:0]."""
    dut.ui_in.value = (oe << 3) | (load << 2) | (dir << 1) | en


async def tick(dut, n=1):
    """Advance n rising clock edges, then wait a tiny time for signals to settle."""
    for _ in range(n):
        await RisingEdge(dut.clk)
    # Small delay so registered outputs are visible to cocotb after the edge
    await Timer(1, units="ns")


@cocotb.test()
async def test_load_count_tristate(dut):
    # 10 MHz clock (100 ns period)
    cocotb.start_soon(Clock(dut.clk, 100, units="ns").start())

    # Reset
    dut.rst_n.value  = 0
    dut.ena.value    = 1
    dut.uio_in.value = 0
    dut.ui_in.value  = 0
    await Timer(1, units="us")
    dut.rst_n.value = 1
    await tick(dut)

    # 1) Synchronous load 0xA5 from uio_in
    dut.uio_in.value = 0xA5
    set_ui(dut, en=0, dir=1, load=1, oe=0)   # assert LOAD
    await tick(dut)                          # load occurs on this edge
    set_ui(dut, en=0, dir=1, load=0, oe=0)   # deassert LOAD
    await tick(dut)
    assert int(dut.uo_out.value) == 0xA5, f"After LOAD expected 0xA5, got 0x{int(dut.uo_out.value):02X}"

    # 2) Count up 3 cycles → 0xA8
    set_ui(dut, en=1, dir=1, load=0, oe=0)
    await tick(dut, 3)
    assert int(dut.uo_out.value) == 0xA8, f"After count-up expected 0xA8, got 0x{int(dut.uo_out.value):02X}"

    # 3) Drive tri-state bus with current count
    set_ui(dut, en=1, dir=1, load=0, oe=1)
    await tick(dut)
    assert int(dut.uio_out.value) == int(dut.uo_out.value), "uio_out should mirror count when OE=1"
    assert int(dut.uio_oe.value)  == 0xFF, "uio_oe should be 0xFF when OE=1"

    # 4) Count down 5 cycles → 0xA3
    set_ui(dut, en=1, dir=0, load=0, oe=1)
    await tick(dut, 5)
    assert int(dut.uo_out.value) == 0xA3, f"After count-down expected 0xA3, got 0x{int(dut.uo_out.value):02X}"
