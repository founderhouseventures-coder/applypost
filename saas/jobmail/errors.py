from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(
        request,
        "tracker/problem.html",
        {
            "title": "Page unavailable",
            "detail": "The link may have expired or belong to another account.",
        },
        status=404,
    )


def server_error(request: HttpRequest) -> HttpResponse:
    if request.resolver_match and request.resolver_match.url_name in {
        "health",
        "razorpay_webhook",
    }:
        return JsonResponse(
            {"error": "The service could not complete the request."}, status=500
        )
    return render(
        None,
        "tracker/problem.html",
        {"title": "Something went wrong", "detail": "Try again in a moment."},
        status=500,
    )
