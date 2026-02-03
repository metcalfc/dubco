"""Link CRUD operations for Dub.co API."""

from typing import Any

from dubco_cli.api.client import DubClient, DubAPIError
from dubco_cli.models.link import CreateLinkRequest, Link


def create_link(client: DubClient, request: CreateLinkRequest) -> Link:
    """Create a single link."""
    response = client.post("/links", json=request.to_api_dict())
    return Link(**response)


def bulk_create_links(
    client: DubClient,
    requests: list[CreateLinkRequest],
) -> tuple[list[Link], list[dict[str, Any]]]:
    """Create multiple links in bulk.

    Returns:
        Tuple of (created_links, errors)
    """
    # API limit is 100 per request
    BATCH_SIZE = 100

    all_created = []
    all_errors = []

    for i in range(0, len(requests), BATCH_SIZE):
        batch = requests[i : i + BATCH_SIZE]
        batch_dicts = [r.to_api_dict() for r in batch]

        try:
            response = client.post("/links/bulk", json=batch_dicts)

            # Response is a list of created links
            if isinstance(response, list):
                for item in response:
                    try:
                        all_created.append(Link(**item))
                    except Exception as e:
                        all_errors.append({"data": item, "error": str(e)})
            elif isinstance(response, dict):
                # Some APIs return {links: [...], errors: [...]}
                if "links" in response:
                    for item in response["links"]:
                        try:
                            all_created.append(Link(**item))
                        except Exception as e:
                            all_errors.append({"data": item, "error": str(e)})
                if "errors" in response:
                    all_errors.extend(response["errors"])

        except DubAPIError as e:
            # Track which batch failed
            for j, req in enumerate(batch):
                all_errors.append({
                    "row": i + j + 1,
                    "url": req.url,
                    "error": str(e),
                })

    return all_created, all_errors


def list_links(
    client: DubClient,
    domain: str | None = None,
    tag_ids: list[str] | None = None,
    tag_names: list[str] | None = None,
    search: str | None = None,
    sort: str = "createdAt",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Link], bool]:
    """List links with optional filters.

    Returns:
        Tuple of (links, has_more)
    """
    params: dict[str, Any] = {
        "sort": sort,
        "page": page,
        "pageSize": min(page_size, 100),  # API max is 100
    }

    if domain:
        params["domain"] = domain
    if tag_ids:
        params["tagIds"] = ",".join(tag_ids)
    if tag_names:
        params["tagNames"] = ",".join(tag_names)
    if search:
        params["search"] = search

    response = client.get("/links", params=params)

    # Response is a list of links
    links = [Link(**item) for item in response]
    has_more = len(links) == params["pageSize"]

    return links, has_more


def list_all_links(
    client: DubClient,
    domain: str | None = None,
    tag_ids: list[str] | None = None,
    tag_names: list[str] | None = None,
    search: str | None = None,
    sort: str = "createdAt",
    limit: int | None = None,
) -> list[Link]:
    """List all links, handling pagination automatically."""
    all_links = []
    page = 1
    page_size = 100  # Use max page size for efficiency

    while True:
        links, has_more = list_links(
            client,
            domain=domain,
            tag_ids=tag_ids,
            tag_names=tag_names,
            search=search,
            sort=sort,
            page=page,
            page_size=page_size,
        )

        all_links.extend(links)

        if limit and len(all_links) >= limit:
            return all_links[:limit]

        if not has_more:
            break

        page += 1

    return all_links


def get_link(
    client: DubClient,
    link_id: str | None = None,
    domain: str | None = None,
    key: str | None = None,
    external_id: str | None = None,
) -> Link | None:
    """Get a single link by ID, domain+key, or external ID."""
    params = {}

    if link_id:
        # Direct ID lookup
        try:
            response = client.get(f"/links/{link_id}")
            return Link(**response)
        except DubAPIError as e:
            if e.status_code == 404:
                return None
            raise

    if external_id:
        params["externalId"] = external_id
    if domain:
        params["domain"] = domain
    if key:
        params["key"] = key

    try:
        response = client.get("/links/info", params=params)
        return Link(**response)
    except DubAPIError as e:
        if e.status_code == 404:
            return None
        raise


def delete_link(client: DubClient, link_id: str) -> bool:
    """Delete a single link by ID."""
    try:
        client.delete(f"/links/{link_id}")
        return True
    except DubAPIError as e:
        if e.status_code == 404:
            return False
        raise


def bulk_delete_links(
    client: DubClient,
    link_ids: list[str],
) -> tuple[int, list[dict[str, Any]]]:
    """Delete multiple links in bulk.

    Returns:
        Tuple of (deleted_count, errors)
    """
    BATCH_SIZE = 100

    deleted_count = 0
    all_errors = []

    for i in range(0, len(link_ids), BATCH_SIZE):
        batch = link_ids[i : i + BATCH_SIZE]

        try:
            response = client.delete("/links/bulk", params={"linkIds": ",".join(batch)})
            deleted_count += response.get("deletedCount", len(batch))
        except DubAPIError as e:
            for link_id in batch:
                all_errors.append({"linkId": link_id, "error": str(e)})

    return deleted_count, all_errors
