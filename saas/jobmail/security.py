class SaaSSecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        checkout = (
            request.resolver_match is not None
            and request.resolver_match.url_name == "pilot_checkout"
            and response.status_code == 200
        )
        scripts = " https://checkout.razorpay.com" if checkout else ""
        connections = (
            " https://api.razorpay.com https://checkout.razorpay.com"
            if checkout
            else ""
        )
        frames = (
            "frame-src https://api.razorpay.com https://checkout.razorpay.com; "
            if checkout
            else ""
        )
        response["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'; img-src 'self' data:; object-src 'none'; "
            f"script-src 'self'{scripts}; style-src 'self'; font-src 'self'; "
            f"connect-src 'self'{connections}; {frames}"
            "upgrade-insecure-requests"
        )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["X-Content-Type-Options"] = "nosniff"
        return response
