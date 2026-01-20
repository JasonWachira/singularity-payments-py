# adapters/Django/mpesa/wrap_view.py
from functools import wraps


def wrap_view(view_func, client_factory=None, handler_factory=None):
    """
    Wraps a Django async view to inject a fresh client or handler per request.
    """

    @wraps(view_func)
    async def _wrapped(request, *args, **kwargs):
        client = client_factory() if client_factory else None
        handler = handler_factory() if handler_factory else None
        return await view_func(request, client=client, handler=handler, *args, **kwargs)

    return _wrapped
