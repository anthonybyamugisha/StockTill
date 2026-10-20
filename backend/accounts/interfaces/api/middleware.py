from django.http import JsonResponse

PENDING_PASSWORD_PATHS = (
    "/api/v1/accounts/login/",
    "/api/v1/accounts/logout/",
    "/api/v1/accounts/me/",
    "/api/v1/accounts/change-password/",
    "/api/v1/health/",
    "/api/schema/",
    "/api/docs/",
)


def is_password_change_path(path: str) -> bool:
    return path in PENDING_PASSWORD_PATHS


class RequirePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        pending = (
            user is not None
            and user.is_authenticated
            and getattr(user, "must_change_password", False)
        )
        if (
            pending
            and request.path.startswith("/api/")
            and not is_password_change_path(request.path)
        ):
            return JsonResponse(
                {
                    "detail": "Change your temporary password before using StockTill.",
                    "code": "password_change_required",
                },
                status=403,
            )
        return self.get_response(request)
