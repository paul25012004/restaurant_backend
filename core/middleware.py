"""CORS headers for /media/ so Flutter Web (Chrome) can display uploaded images."""


class MediaCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS' and request.path.startswith('/media/'):
            from django.http import HttpResponse
            response = HttpResponse()
        else:
            response = self.get_response(request)

        if request.path.startswith('/media/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response['Access-Control-Allow-Headers'] = '*'
            response['Cross-Origin-Resource-Policy'] = 'cross-origin'
        return response
