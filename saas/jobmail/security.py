class SaaSSecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'; img-src 'self' data:; object-src 'none'; "
            "script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; "
            "upgrade-insecure-requests"
        )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["X-Content-Type-Options"] = "nosniff"
        return response
