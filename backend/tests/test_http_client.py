import httpx
import pytest

from app.services.http_client import ExternalApiError, get_json


def test_get_json_returns_parsed_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hello": "world"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = get_json("https://example.test/word", client=client)

    assert result == {"hello": "world"}


def test_get_json_raises_on_non_2xx():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalApiError):
        get_json("https://example.test/missing", client=client)


def test_get_json_raises_on_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalApiError):
        get_json("https://example.test/slow", client=client)


def test_get_json_raises_on_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalApiError):
        get_json("https://example.test/unreachable", client=client)


def test_get_json_raises_on_non_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalApiError):
        get_json("https://example.test/word", client=client)


def test_get_json_returns_list_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"word": "hello"}])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = get_json("https://example.test/word", client=client)

    assert result == [{"word": "hello"}]
