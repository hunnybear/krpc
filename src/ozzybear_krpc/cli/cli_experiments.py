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



def launch_tests():
    ip_addr = sys.argv[1]
    conn = util.get_conn(name="launch tests", address=ip_addr)
    vessel = ozzybear_krpc.vessel.util.get_active_vessel(conn)
    ozzybear_krpc.vessel.control.prep_rocket_launch(vessel)

    gravity_turn_interrupt = ozzybear_krpc.vessel.control.get_gravity_turn_interrupt(conn, 90)
    chute_intterupt = ozzybear_krpc.vessel.control.DeployChuteInterrupt(conn, vessel)

    vessel.control.activate_next_stage()

    # paint some happy little interrupts

    interrupts = [gravity_turn_interrupt, chute_intterupt]

    ozzybear_krpc.vessel.control.autostage(vessel, noisy=True, interrupts=interrupts, stop_non_engine=False)


