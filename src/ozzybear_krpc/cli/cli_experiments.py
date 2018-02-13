"""
This should go away soon, but just making sure I have this working correctly.
"""
import sys

import ozzybear_krpc.vessel.control
import ozzybear_krpc.vessel.util

from ozzybear_krpc import const
from ozzybear_krpc import util


def hello_world():

    conn = util.get_conn('hello world!')
    vessel = ozzybear_krpc.vessel.util.get_active_vessel(conn)
    print(vessel.name)


def orbit_test():
    if len(sys.argv) > 1:
        ip_addr = sys.argv[1]
    else:
        ip_addr = None

    conn = util.get_conn(name="orbit tests", address=ip_addr)
    vessel = ozzybear_krpc.vessel.util.get_active_vessel(conn)
    ozzybear_krpc.vessel.control.prep_rocket_launch(vessel)

    gravity_turn_interrupt = ozzybear_krpc.vessel.control.GravityTurnInterrupt(conn, vessel, 90)
    chute_intterupt = ozzybear_krpc.vessel.control.DeployChuteInterrupt(conn, vessel)
    reach_apoapsis_interrupt = ozzybear_krpc.vessel.control.TargetApoapsisInterrupt(conn, vessel, 100000)

    reach_apoapsis_interrupt.add_prerequisite(lambda: gravity_turn_interrupt.finished)

    vessel.control.activate_next_stage()

    # paint some happy little interrupts

    interrupts = [gravity_turn_interrupt, reach_apoapsis_interrupt, chute_intterupt]

    ozzybear_krpc.vessel.control.autostage(vessel, interrupts=interrupts, stop_non_engine=False)





def launch_tests():
    ip_addr = sys.argv[1]
    conn = util.get_conn(name="launch tests", address=ip_addr)
    vessel = ozzybear_krpc.vessel.util.get_active_vessel(conn)
    ozzybear_krpc.vessel.control.prep_rocket_launch(vessel)

    gravity_turn_interrupt = ozzybear_krpc.vessel.control.GravityTurnInterrupt(conn, vessel, 90)
    chute_intterupt = ozzybear_krpc.vessel.control.DeployChuteInterrupt(conn, vessel)

    vessel.control.activate_next_stage()

    # paint some happy little interrupts

    interrupts = [gravity_turn_interrupt, chute_intterupt]

    ozzybear_krpc.vessel.control.autostage(vessel, noisy=True, interrupts=interrupts, stop_non_engine=False)


