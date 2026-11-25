import os

from django.http import HttpRequest


def demo(request: HttpRequest) -> dict[str, bool]:
    return {"demo_mode": os.environ.get("DEMO_MODE") == "1"}
