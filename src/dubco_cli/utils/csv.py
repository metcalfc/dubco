"""CSV parsing and validation for bulk operations."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from dubco_cli.models.link import CreateLinkRequest

# Required and optional CSV columns
REQUIRED_COLUMNS = ["url"]
OPTIONAL_COLUMNS = [
    "key",
    "domain",
    "tag",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "externalId",
    "comments",
]


@dataclass
class CSVRow:
    """A parsed CSV row."""

    row_number: int
    data: dict[str, str]
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


@dataclass
class CSVParseResult:
    """Result of parsing a CSV file."""

    rows: list[CSVRow]
    headers: list[str]

    @property
    def valid_rows(self) -> list[CSVRow]:
        return [r for r in self.rows if r.is_valid]

    @property
    def invalid_rows(self) -> list[CSVRow]:
        return [r for r in self.rows if not r.is_valid]

    @property
    def is_valid(self) -> bool:
        return len(self.invalid_rows) == 0


def validate_headers(headers: list[str]) -> list[str]:
    """Validate CSV headers and return any errors."""
    errors = []
    header_set = set(h.lower().strip() for h in headers)

    for required in REQUIRED_COLUMNS:
        if required not in header_set:
            errors.append(f"Missing required column: {required}")

    return errors


def validate_row(row: dict[str, str], row_number: int) -> CSVRow:
    """Validate a single CSV row."""
    errors = []

    # Check required fields
    url = row.get("url", "").strip()
    if not url:
        errors.append("Missing required field: url")
    elif not (url.startswith("http://") or url.startswith("https://")):
        errors.append(f"Invalid URL (must start with http:// or https://): {url}")

    return CSVRow(row_number=row_number, data=row, errors=errors)


def parse_csv(file_path: Path | str) -> CSVParseResult:
    """Parse a CSV file and validate its contents."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        return parse_csv_file(f)


def parse_csv_file(file: TextIO) -> CSVParseResult:
    """Parse a CSV file object."""
    reader = csv.DictReader(file)

    if reader.fieldnames is None:
        raise ValueError("CSV file is empty or has no headers")

    # Normalize headers
    headers = [h.lower().strip() for h in reader.fieldnames]
    header_errors = validate_headers(headers)

    if header_errors:
        raise ValueError(f"Invalid CSV headers: {', '.join(header_errors)}")

    rows = []
    for i, raw_row in enumerate(reader, start=2):  # Start at 2 (1 is header)
        # Normalize keys
        row = {k.lower().strip(): v.strip() for k, v in raw_row.items() if v}
        validated = validate_row(row, i)
        rows.append(validated)

    return CSVParseResult(rows=rows, headers=headers)


def row_to_create_request(row: CSVRow) -> CreateLinkRequest:
    """Convert a validated CSV row to a CreateLinkRequest."""
    data = row.data

    # Handle tag -> tagNames conversion
    tag_names = None
    if tag := data.get("tag"):
        tag_names = [t.strip() for t in tag.split(",")]

    return CreateLinkRequest(
        url=data["url"],
        key=data.get("key") or None,
        domain=data.get("domain") or None,
        tagNames=tag_names,
        externalId=data.get("externalid") or data.get("external_id") or None,
        comments=data.get("comments") or None,
        utm_source=data.get("utm_source") or None,
        utm_medium=data.get("utm_medium") or None,
        utm_campaign=data.get("utm_campaign") or None,
        utm_term=data.get("utm_term") or None,
        utm_content=data.get("utm_content") or None,
    )
