"""arm_se.py - gem5 ARM, modo SE, 1 nucleo O3 parametrizable.
Uso: gem5.opt -d <outdir> configs/arm_se.py --bin bin/gemm_sve --args 64 --width 8 --rob 192 --vl 4
--vl en cuadruples de 128 bits: 1=128, 2=256, 4=512, 8=1024
"""
import argparse
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import PrivateL1PrivateL2CacheHierarchy
from gem5.components.memory import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("--bin", required=True)
p.add_argument("--args", nargs="*", default=[])
p.add_argument("--width", type=int, default=8)
p.add_argument("--rob", type=int, default=192)
p.add_argument("--vl", type=int, default=4)
p.add_argument("--l1", default="32KiB")
p.add_argument("--l2", default="512KiB")
a = p.parse_args()

proc = SimpleProcessor(cpu_type=CPUTypes.O3, isa=ISA.ARM, num_cores=1, clk_freq="2GHz")
for c in proc.get_cores():
    cpu = c.core
    for attr in ("fetchWidth", "decodeWidth", "renameWidth", "dispatchWidth",
                 "issueWidth", "wbWidth", "commitWidth", "squashWidth"):
        if hasattr(cpu, attr):
            setattr(cpu, attr, a.width)
    cpu.numROBEntries = a.rob
    cpu.isa[0].sve_vl_se = a.vl

board = SimpleBoard(
    clk_freq="2GHz",
    processor=proc,
    memory=SingleChannelDDR4_2400("2GiB"),
    cache_hierarchy=PrivateL1PrivateL2CacheHierarchy(
        l1d_size=a.l1, l1i_size=a.l1, l2_size=a.l2),
)
board.set_se_binary_workload(BinaryResource(a.bin), arguments=a.args)

sim = Simulator(board=board)
sim.run()
print("exit:", sim.get_last_exit_event_cause())