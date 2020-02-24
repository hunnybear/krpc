"""
telemetry.py

Class and functions for reading data from the server
"""

import functools

from ozzybear_krpc import const


def convert_atmosphere_to_pascal(atmospheres):
    """
    Convert pressure in atmospheres to pascals.
    """

    return atmospheres * 101325


def convert_pascal_to_atmosphere(pascals):
    """
    Convert pressure in pascals to atmospheres.

    """
    return pascals / 101325.0


class ManagerMeta(type):
    _instances = {}

    def __call__(cls, conn):
        if (cls, conn) not in cls._instances:
            cls._instances[(cls, conn)] = super(ManagerMeta, cls).__call__(conn)
        return cls._instances[(cls, conn)]


class StreamManager(metaclass=ManagerMeta):
    """
    Central management point for streams. Allows proximal location for caching
    of streams and access based on connection and arguments passed to stream
    """

    def __init__(self, conn):
        self._conn = conn
        self._streams = {}

    @staticmethod
    def _get_dict_key_val(item):
        if hasattr(item, '_object_id'):
            return "{0}::{1}".format(str(item.__class__), item._object_id)

        return str(item)

    @classmethod
    def add_managed_method(cls, function):

        @functools.wraps(function)
        def method(self, *args, **kwargs):
            key_args = tuple(cls._get_dict_key_val(item) for item in args)
            key_kwargs = tuple('{0}=>{1}'.format(k, cls._get_dict_key_val(v)) for k, v in kwargs.items())
            stream_key = key_args + key_kwargs
            print(stream_key)
            if stream_key not in self._streams.setdefault(function.__name__, {}):
                stream = function(self._conn, *args, **kwargs)
                self._streams[function.__name__][stream_key] = stream
            return self._streams[function.__name__][stream_key]

        setattr(cls, function.__name__, method)

        return function


@StreamManager.add_managed_method
def get_pressure_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.flight(), 'static_pressure')


@StreamManager.add_managed_method
def get_vertical_speed_stream(conn, vessel):
    """
    Get a stream for the vertical speed fof a vessel

    Arguments:
        *conn* <krpc.client.Client> : your client connection
        *vessel* <SpaceCenter.Vessel> : the vehicle you want the stream for
    """
    # not gonna lie, only half understand the explanation they gave for this
    # (probably a good explanation, just my lack of understanding), but I
    # stole this chunk from: https://krpc.github.io/krpc/tutorials/reference-frames.html
    ref_frame = vessel.orbit.body.reference_frame
    stream = conn.add_stream(getattr, vessel.flight(ref_frame), 'vertical_speed')
    return stream


@StreamManager.add_managed_method
def get_surface_altitude_stream(conn, vessel, reference_frame=None):
    if reference_frame is None:
        reference_frame = vessel.orbit.body.reference_frame
    return conn.add_stream(getattr, vessel.flight(reference_frame), const.SURFACE_ALTITUDE)


@StreamManager.add_managed_method
def get_apoapsis_altitude_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.orbit, const.APOAPSIS_ALTITUDE)


@StreamManager.add_managed_method
def get_periapsis_altitde_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.orbit, const.PERIAPSIS_ALTITUDE)


@StreamManager.add_managed_method
def get_time_to_apoapsis_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.orbit, const.TIME_TO_APOAPSIS)


@StreamManager.add_managed_method
def get_time_to_periapsis_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.orbit, const.TIME_TO_PERIAPSIS)


@StreamManager.add_managed_method
def get_landspeed(conn, vessel):
    ref_frame = conn.space_center.ReferenceFrame.create_hybrid(
        position=vessel.orbit.body.reference_frame,
        rotation=vessel.surface_reference_frame
    )
    raise NotImplementedError()


@StreamManager.add_managed_method
def get_accelleration_stream(conn, vessel, reference_frame):
    raise NotImplementedError()
    stream = conn.add_stream(getattr, vessel.flight())
    return stream


@StreamManager.add_managed_method
def get_mean_altitude_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.flight(), const.MEAN_ALTITUDE)


@StreamManager.add_managed_method
def get_stage_resource_stream(conn, vessel, stage, resource, cumulative=False):
    """
    Get a stream of the amount of a given resource in a stage.
    """

    resource_obj = vessel.resources_in_decouple_stage(stage=stage, cumulative=cumulative)
    return conn.add_stream(resource_obj.amount, resource)


@StreamManager.add_managed_method
def get_target_pitch_stream(conn, vessel):
    return conn.add_stream(getattr, vessel.auto_pilot, 'target_pitch')
