# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Pre-Commit Checklist (MANDATORY)

**NEVER commit without running these commands first:**

```bash
ruff format src tests          # Format code
ruff check src tests --fix     # Lint and auto-fix
uv run pytest                  # Run all tests
```

All three must pass before any commit.

## Development Commands

```bash
# Setup
uv sync --extra dev --extra tui    # Install all dependencies

# Testing
uv run pytest                              # Run all tests
uv run pytest tests/test_add.py            # Run specific test file
uv run pytest tests/test_add.py::TestUTMHandling::test_extract_utm_from_url_with_params  # Single test

# Linting
ruff check src tests           # Check for errors
ruff check src tests --fix     # Auto-fix errors
ruff format src tests          # Format code
ruff format --check src tests  # Check formatting without changing
```

## Architecture

**CLI Framework**: Typer with Rich for output formatting

**Entry Point**: `src/dubco_cli/main.py` → `dub` command

**Key Modules**:
- `api/client.py` - HTTP client with automatic token refresh and retry logic
- `api/oauth.py` - OAuth PKCE flow (port 8484 callback, credentials at `~/.config/dubco/`)
- `api/links.py` - Link CRUD operations (batch size: 100)
- `commands/` - CLI commands (add, list, rm, stats, auth, tui)
- `models/link.py` - Pydantic models matching Dub.co API (uses camelCase field names)

**Authentication Flow**: OAuth PKCE with local callback server. Tokens auto-refresh when expired.

**Output Formats**: table (default), json, csv, plain

## Code Conventions

- Line length: 100 characters
- Python 3.10+ required
- Pydantic models in `models/link.py` use camelCase to match API (N815 ignored)
- Use `DubAPIError` for API errors with status codes
- Exit codes: 0=success, 1=error, 2=invalid args, 3=auth error, 4=not found, 5=partial failure
