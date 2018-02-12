"""
control.py

Functions for controlling a vehicle, at this time probably mostly rockets.
This will probably get broken up in the future, so try to group things in what
ever way seems sensible to you, man.

TODO:
    *   determine whether a Resources object updates, or if it is static upon
        creation. This might impact how I handle things like
        get_stage_resources (if it's static, probably return a dict, but if it
        is dynamic, might want to return the object so that it can be used for
        updates).

"""

import ozzybear_krpc.telemetry
from ozzybear_krpc import const

import time

INTERRUPT_STOP = 'stop'
INTERRUPT_REMOVE = 'remove'
INTERRUPT_CONTINUE = 'continue'


def get_current_stage(vessel):

    return vessel.control.current_stage


def get_stage_resources_native(vessel, stage=None, cumulative=False):
    if stage is None:
        stage = get_current_stage(vessel)
        # TODO go to logging
        print("current stage: {0}".format(stage))

    resources = vessel.resources_in_decouple_stage(stage=stage, cumulative=cumulative)

    return resources


def get_stage_resource_amounts(
    vessel, stage=None,
    cumulative=False, res_filter=frozenset()):

    resources = get_stage_resources_native(vessel, stage=stage, cumulative=cumulative)
    # TODO cleanup on aisle too dense
    resource_dict = dict((name, resources.amount(name)) for name in resources.names if name not in res_filter)

    return resource_dict


def prep_rocket_launch(vessel):
    vessel.auto_pilot.target_pitch_and_heading(90, 90)
    vessel.auto_pilot.engage()
    vessel.control.throttle = 1


def launch_rocket(conn, vessel, heading, turn_altitude=10000):
    vessel.control.activate_next_stage()


def _stage_ready(resources_obj, autostage_resources, mode=const.AND):
    if mode not in [const.AND, const.OR]:
        valid_modes = ', '.join([const.AND, const.OR])
        msg = 'mode must be one of [{0}], {1} was provided'.format(valid_modes, mode)
        raise ValueError(msg)

    for resource in autostage_resources:
        current = resources_obj.amount(resource)
        if current <= 0:
            # TODO logging
            if mode == const.OR:
                return True
        elif mode == const.AND:
            return False

    if mode == const.AND:
        print("returning True since reached end with AND")
        return True
    else:
        print("implicit OR mode we didn't hit any empties")
        return False


def _get_autostage_stages(vessel, autostage_resources=const.RESOURCES_FUEL, skip_non_engine=True):
    # I /think/ this needs the +1, as the dox say it corresponds to the
    # in-game UI, but I haven't checked yet
    count_stages = get_current_stage(vessel)

    print("count stages: {0}".format(count_stages))

    stages = []

    for stage_i in reversed(range(count_stages)):
        stage_resources = vessel.resources_in_decouple_stage(stage=stage_i, cumulative=False)
        print(stage_i, set(stage_resources.names), autostage_resources)
        if set(stage_resources.names).intersection(autostage_resources):
            stages.append(stage_i)
        elif not skip_non_engine:
            stages.append(None)
    # TODO logging
    print('stages: {0}'.format(', '.join([str(i) for i in stages])))
    return stages


class InterruptHandler(object):

    def __init__(self, conn, vessel):
        self._vessel = vessel
        self._sm = ozzybear_krpc.telemetry.StreamManager(conn)

        super(InterruptHandler, self).__init__()

    def __call__(self, vessel):
        assert vessel._object_id == self._vessel
        self._handle()


class DeployChuteInterrupt(InterruptHandler):

    def __init__(self, conn, vessel):
        super(Deploy_Chute_Interrupt, self).__init__(conn, vessel)

        self._parachutes_stream = conn.add_stream(getattr, vessel.parts, 'parachutes')
        self._pressure_stream = self._sm.get_pressure_stream(vessel)
        self._vert_speed_stream = self._sm.get_vertical_speed_stream(vessel)

    def _handle(self):

        if self._vert_speed_stream() >= 0:
            return False

        parachutes = self._parachutes_stream()
        if not parachutes:
            print(parachutes)
            print("removing parachute interrupt")
            raise InterruptResponse(stop=True, remove=True)
        pressure = self._pressure_stream()
        pressure_atm = ozzybear_krpc.telemetry.convert_pascal_to_atmosphere(pressure)

        for parachute in parachutes:
            if pressure_atm >= parachute.deploy_min_pressure:
                parachute.deploy()


class GravityTurnInterrupt(InterruptHandler):
    def __init__(self, conn, vessel, hdg, turn_start=250, turn_end=12000):

        self._heading = hdg
        if turn_start >= turn_end:
            raise ValueError('turn_start must be smaller than turn_end')

        self.turn_start = turn_start
        self.turn_end = turn_end

        super(GravityTurnInterrupt, self).__init__(conn, vessel)

        self._vert_speed_stream = self._sm.get_vertical_speed_stream(vessel)
        self._target_pitch_stream = self._sm.get_target_pitch_stream(vessel)
        self._mean_altitude_stream = self._sm.get_mean_altitude_stream(vessel)

    def _handle(self):

        turn_height = self.turn_end - self.turn_start

        if self._vert_speed_stream() <= 0:
            return False
        mean_altitude = self._mean_altitude_stream()
        if self.turn_start <= mean_altitude <= self.turn_end:
            progress = (mean_altitude - self.turn_start) / turn_height
            new_pitch_angle = progress * 90
            if abs(new_pitch_angle - self._target_pitch_stream()) < 1:
                print('setting pitch to {0}, heading to {1}'.format(new_pitch_angle, self.heading))
                self._vessel.auto_pilot.target_pitch_and_heading(pitch=new_pitch_angle, heading=self.heading)

        elif mean_altitude > self.turn_end:
            raise InterruptResponse(remove=True)


def autostage(
        vessel, stages=None,
        skip_non_engine=False,
        stop_non_engine=True,
        interrupts=None, noisy=True,
        autostage_resources=const.RESOURCES_FUEL):

    if stages is None:
        stages = _get_autostage_stages(vessel, autostage_resources=autostage_resources, skip_non_engine=skip_non_engine)

    interrupts = list(interrupts or [])

    for stage in stages:
        if stage is None and stop_non_engine:
            raise NonEngineStage()
        while True:
            if stage is not None:
                resources = vessel.resources_in_decouple_stage(stage)
                if _stage_ready(resources, autostage_resources, mode=const.AND):
                    print("firing stage {0}".format(stage))
                    time.sleep(0.5)
                    vessel.control.activate_next_stage()
                    print("stage {0} fired.".format(stage))
                    break
            if interrupts is not None:
                for interrupt in set(interrupts):
                    try:
                        interrupt(vessel)
                    except InterruptResponse as exc:
                        if exc.remove:
                            interrupts.remove(interrupt)
                        if exc.stop:
                            raise exc
                        if exc.skip_stage:
                            break
            time.sleep(0.1)

    print('no more stages!')


class NonEngineStage(Exception):
    pass


class InterruptResponse(Exception):
    def __init__(self, msg=None, remove=False, skip_stage=False, stop=False):
        self.remove = remove
        self.skip_stage = skip_stage
        self.stop = stop

        if msg is None:
            msg = 'Interrupt'

        super(InterruptResponse, self).__init__(msg)




