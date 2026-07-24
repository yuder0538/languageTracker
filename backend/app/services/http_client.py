from typing import Any

import httpx


class ExternalApiError(Exception):
    pass


def get_json(
    url: str,
    params: dict | None = None,
    timeout: float = 5.0,
    client: httpx.Client | None = None,
) -> Any:
    try:
        if client is not None:
            response = client.get(
                url, params=params, timeout=timeout, follow_redirects=False
            )
        else:
            response = httpx.get(
                url, params=params, timeout=timeout, follow_redirects=False
            )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ExternalApiError(f"Request to {url} timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise ExternalApiError(
            f"Request to {url} failed with status {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ExternalApiError(f"Request to {url} failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ExternalApiError(f"Request to {url} returned a non-JSON response") from exc
