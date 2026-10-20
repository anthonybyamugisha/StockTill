from collections.abc import Callable
from functools import wraps
from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.errors import DomainError


def domain_errors_to_bad_request(
    view_method: Callable[[Any, Request], Response],
) -> Callable[[Any, Request], Response]:
    @wraps(view_method)
    def wrapper(view: APIView, request: Request, *args, **kwargs) -> Response:
        try:
            return view_method(view, request, *args, **kwargs)
        except (ValueError, DomainError) as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    return wrapper
