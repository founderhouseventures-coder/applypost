import hashlib
from collections.abc import Callable
from time import time

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

WINDOW_SECONDS = 60
# Route name: (requests per minute, limit only POST).
LIMITS = {
    "login": (10, True),
    "signup": (5, True),
    "password_reset": (5, True),
    "password_reset_confirm": (10, True),
    "subscribe_updates": (5, True),
    "checkout": (5, True),
    "pilot_checkout": (5, True),
    "cancel_subscription": (5, True),
    "import_applications": (10, True),
    "export_data": (10, False),
}
PUBLIC_IP_LIMITS = {
    "login",
    "signup",
    "password_reset",
    "password_reset_confirm",
    "subscribe_updates",
}

View = Callable[..., HttpResponse]


class RequestThrottle:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view: View,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> HttpResponse | None:
        route = request.resolver_match.url_name if request.resolver_match else None
        if route is None or route not in LIMITS:
            return None
        limit, post_only = LIMITS[route]
        if request.method not in ({"POST"} if post_only else {"GET", "HEAD", "POST"}):
            return None

        if route not in PUBLIC_IP_LIMITS and request.user.is_authenticated:
            identity = f"user:{request.user.pk}"
        else:
            identity = f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"
        window, elapsed = divmod(int(time()), WINDOW_SECONDS)
        digest = hashlib.sha256(identity.encode()).hexdigest()
        key = f"portal:rate:{route}:{window}:{digest}"
        retry_after = WINDOW_SECONDS - elapsed
        cache.add(key, 0, timeout=retry_after + 1)
        try:
            count = cache.incr(key)
        except ValueError:
            # A key may expire or be evicted between add and increment.
            count = 1 if cache.add(key, 1, timeout=retry_after + 1) else cache.incr(key)
        if count <= limit:
            return None

        detail = "Too many requests. Wait a minute and try again."
        response = render(
            request,
            "tracker/problem.html",
            {"title": "Too many requests", "detail": detail},
            status=429,
        )
        response["Retry-After"] = str(retry_after)
        return response
