from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from shared.domain.errors import DomainError, InvalidQuantityError
from shared.interfaces.api.errors import domain_errors_to_bad_request

factory = APIRequestFactory()


class _PublicView(APIView):
    permission_classes: list = []


class _DomainErrorView(_PublicView):
    @domain_errors_to_bad_request
    def get(self, request):
        raise DomainError("nope")


class _ValueErrorView(_PublicView):
    @domain_errors_to_bad_request
    def get(self, request):
        raise ValueError("bad input")


class _NestedDomainErrorView(_PublicView):
    @domain_errors_to_bad_request
    def get(self, request):
        raise InvalidQuantityError("quantity must be positive")


class _WorkingView(_PublicView):
    @domain_errors_to_bad_request
    def get(self, request):
        return Response({"ok": True})


def test_maps_domain_errors_to_bad_request():
    response = _DomainErrorView.as_view()(factory.get("/"))

    assert response.status_code == 400
    assert response.data == {"detail": "nope"}


def test_maps_value_errors_to_bad_request():
    response = _ValueErrorView.as_view()(factory.get("/"))

    assert response.status_code == 400
    assert response.data == {"detail": "bad input"}


def test_maps_domain_subclasses_to_bad_request():
    response = _NestedDomainErrorView.as_view()(factory.get("/"))

    assert response.status_code == 400
    assert response.data == {"detail": "quantity must be positive"}


def test_leaves_successful_responses_alone():
    response = _WorkingView.as_view()(factory.get("/"))

    assert response.status_code == 200
    assert response.data == {"ok": True}
