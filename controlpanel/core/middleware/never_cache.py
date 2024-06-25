from django.utils.cache import add_never_cache_headers


# TODO this was copied from Control Panel do we still want/need it?
class DisableClientSideCachingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        response["Pragma"] = "no-cache"
        return response
