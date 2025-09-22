import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer


def set_ui(dut, en=0, dir=1, load=0, oe=0):
    """Pack EN, DIR, LOAD, OE into ui_in[3:0]."""
    dut.ui_in.value = (oe << 3) | (load << 2) | (dir << 1) | en


async def step(dut, cycles=1):
    """Advance 'cycles' rising edges and then sample after HDL settles."""
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    # NOTE: After this returns we are in ReadOnly phase.
    await ReadOnly()


@cocotb.test()
async def test_load_count_tristate(dut):
    # 10 MHz clock (100 ns period)
    cocotb.start_soon(Clock(dut.clk, 100, units="ns").start())

    # ----- Reset -----
    dut.rst_n.value  = 0
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    await Timer(1, units="us")
    dut.rst_n.value = 1
    await step(dut)  # ends in ReadOnly

    # Leave ReadOnly before driving new values
    await Timer(1, units="ns")

    # ----- Sync LOAD 0xA5 from uio_in -----
    dut.uio_in.value = 0xA5
    set_ui(dut, en=0, dir=1, load=1, oe=0)   # assert LOAD
    await step(dut, 1)                       # load on this edge

    # Leave ReadOnly before deasserting LOAD
    await Timer(1, units="ns")
    set_ui(dut, en=0, dir=1, load=0, oe=0)   # deassert LOAD
    await step(dut, 1)

    assert int(dut.uo_out.value) == 0xA5, f"After LOAD expected 0xA5, got 0x{int(dut.uo_out.value):02X}"

    # ----- Count UP: check each edge to avoid off-by-one -----
    await Timer(1, units="ns")               # exit ReadOnly before writing
    set_ui(dut, en=1, dir=1, load=0, oe=0)
    expected = 0xA5
    for i in range(1, 4):                    # 3 cycles
        await step(dut, 1)
        expected = (expected + 1) & 0xFF
        got = int(dut.uo_out.value)
        assert got == expected, f"UP step {i}: expected 0x{expected:02X}, got 0x{got:02X}"
    # Final spot check (should be 0xA8)
    assert int(dut.uo_out.value) == 0xA8

    # ----- Tri-state drive -----
    await Timer(1, units="ns")
    set_ui(dut, en=1, dir=1, load=0, oe=1)
    await step(dut, 1)
    assert int(dut.uio_out.value) == int(dut.uo_out.value), "uio_out should mirror count when OE=1"
    assert int(dut.uio_oe.value)  == 0xFF, "uio_oe should be 0xFF when OE=1"

    # ----- Count DOWN 5 edges, verify per step -----
    await Timer(1, units="ns")
    set_ui(dut, en=1, dir=0, load=0, oe=1)
    for i in range(1, 6):                    # 5 cycles
        await step(dut, 1)
        expected = (expected - 1) & 0xFF
        got = int(dut.uo_out.value)
        assert got == expected, f"DOWN step {i}: expected 0x{expected:02X}, got 0x{got:02X}"
    # Final spot check (should be 0xA3)
    assert int(dut.uo_out.value) == 0xA3
