"""Remove command for deleting links."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from dubco_cli.api.client import DubAPIError, DubClient
from dubco_cli.api.links import bulk_delete_links, delete_link, get_link
from dubco_cli.utils.output import print_error, print_success, print_warning

console = Console()


def rm(
    keys: Annotated[
        list[str] | None,
        typer.Argument(help="Link key(s) or ID(s) to delete"),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option("--domain", "-d", help="Domain for key lookup"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
    file: Annotated[
        Path | None,
        typer.Option("--file", help="File with link IDs/keys to delete (one per line)"),
    ] = None,
):
    """Delete short links.

    You can delete links by:
    - Key (requires --domain): dub rm my-link -d dub.sh
    - Link ID: dub rm clx1234567890
    - Multiple: dub rm link1 link2 link3 -d dub.sh
    - From file: dub rm --file links-to-delete.txt

    Examples:

        dub rm my-link -d dub.sh

        dub rm clx1234567890 clx0987654321

        dub rm --file to-delete.txt --force
    """
    # Collect all identifiers to delete
    identifiers: list[str] = []

    if keys:
        identifiers.extend(keys)

    if file:
        if not file.exists():
            print_error(f"File not found: {file}")
            raise typer.Exit(2)
        lines = file.read_text().strip().split("\n")
        identifiers.extend(line.strip() for line in lines if line.strip())

    if not identifiers:
        print_error("No links specified. Provide keys/IDs or use --file.")
        raise typer.Exit(2)

    try:
        with DubClient() as client:
            # Resolve identifiers to link IDs and get click counts
            links_to_delete = []
            not_found = []

            with console.status("Looking up links..."):
                for identifier in identifiers:
                    # Try to find the link
                    link = None

                    # Check if it looks like a link ID (starts with common prefixes)
                    if identifier.startswith(("clx", "link_", "ext_")):
                        link = get_link(client, link_id=identifier)

                    # If not found by ID, try by key+domain
                    if not link and domain:
                        link = get_link(client, domain=domain, key=identifier)

                    # If still not found, try as external ID
                    if not link:
                        link = get_link(client, external_id=identifier)

                    if link:
                        links_to_delete.append(link)
                    else:
                        not_found.append(identifier)

            # Report not found
            if not_found:
                for identifier in not_found:
                    print_warning(f"Link not found: {identifier}")

            if not links_to_delete:
                print_error("No links found to delete")
                raise typer.Exit(4)

            # Calculate total clicks
            total_clicks = sum(link.clicks for link in links_to_delete)

            # Show confirmation
            if not force:
                console.print(f"\nAbout to delete {len(links_to_delete)} link(s):")
                for link in links_to_delete[:10]:
                    click_str = f" ({link.clicks} clicks)" if link.clicks else ""
                    console.print(f"  {link.shortLink}{click_str}")
                if len(links_to_delete) > 10:
                    console.print(f"  ... and {len(links_to_delete) - 10} more")

                if total_clicks > 0:
                    console.print(
                        f"\n[yellow]Warning: These links have {total_clicks} total clicks.[/yellow]"
                    )

                if not typer.confirm("\nContinue with deletion?"):
                    console.print("Aborted.")
                    raise typer.Exit(0)

            # Delete links
            link_ids = [link.id for link in links_to_delete]

            if len(link_ids) == 1:
                # Single delete
                success = delete_link(client, link_ids[0])
                if success:
                    print_success(f"Deleted: {links_to_delete[0].shortLink}")
                else:
                    print_error(f"Failed to delete: {links_to_delete[0].shortLink}")
                    raise typer.Exit(1)
            else:
                # Bulk delete
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        f"Deleting {len(link_ids)} links...",
                        total=len(link_ids),
                    )

                    deleted_count, errors = bulk_delete_links(client, link_ids)
                    progress.update(task, completed=len(link_ids))

                # Report results
                if deleted_count > 0:
                    print_success(f"Deleted {deleted_count} links")

                if errors:
                    console.print(f"\n[red]Failed to delete {len(errors)} links:[/red]")
                    for err in errors[:10]:
                        console.print(f"  {err['linkId']}: {err['error']}")
                    if len(errors) > 10:
                        console.print(f"  ... and {len(errors) - 10} more errors")
                    raise typer.Exit(5)

    except DubAPIError as e:
        print_error(str(e))
        if e.status_code == 401:
            raise typer.Exit(3)
        if e.status_code == 404:
            raise typer.Exit(4)
        raise typer.Exit(1)
