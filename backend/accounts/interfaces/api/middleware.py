from django.http import JsonResponse

PENDING_PASSWORD_PATHS = ("/api/v1/accounts/change-password/",)


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
            and not request.path.startswith(PENDING_PASSWORD_PATHS)
        ):
            return JsonResponse(
                {
                    "detail": "Change your temporary password before using StockTill.",
                    "code": "password_change_required",
                },
                status=403,
            )
        return self.get_response(request)
