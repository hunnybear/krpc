
import krpc

def get_conn(name, address=None):
    """
    Get a connection [client]

    Arguments:
        *name* <str> : name of the connection

    Keyword Arguments:
        *address* <str> : IP address of the server

    Returns:
        *conn* <krpc.client.Client> : A new krpc Client
    """

    return krpc.connect(name=name, address=address)


