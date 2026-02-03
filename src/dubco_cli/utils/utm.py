"""UTM parameter handling utilities."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

UTM_PARAMS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]


def extract_utm_from_url(url: str) -> tuple[str, dict[str, str]]:
    """Extract UTM parameters from URL.

    Returns:
        Tuple of (clean_url, utm_params) where clean_url has UTM params removed.
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Extract UTM params
    utm_params = {}
    remaining_params = {}

    for key, values in query_params.items():
        if key in UTM_PARAMS:
            utm_params[key] = values[0]  # Take first value
        else:
            remaining_params[key] = values

    # Rebuild URL without UTM params
    new_query = urlencode(remaining_params, doseq=True)
    clean_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )

    return clean_url, utm_params


def merge_utm_params(
    url_params: dict[str, str],
    cli_params: dict[str, str | None],
) -> dict[str, str]:
    """Merge UTM params from URL with CLI overrides.

    CLI params take precedence over URL params.
    """
    result = url_params.copy()

    for key, value in cli_params.items():
        if value is not None:
            result[key] = value

    return result


def build_utm_dict(
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    utm_term: str | None = None,
    utm_content: str | None = None,
) -> dict[str, str | None]:
    """Build a UTM params dict from individual values."""
    return {
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
        "utm_term": utm_term,
        "utm_content": utm_content,
    }
