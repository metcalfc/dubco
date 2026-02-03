# dub-cli: Dub.co Link Management Tool

## Overview

A Python CLI for managing short links on Dub.co. Supports adding single or bulk links, listing existing links, and removing links.

## Installation & Configuration

```bash
pip install dub-cli
```

**Environment variables:**
- `DUB_API_KEY` — Required. Your Dub.co API token.
- `DUB_WORKSPACE_ID` — Required. Your workspace ID.
- `DUB_DOMAIN` — Optional. Default domain for new links (e.g., `go.continue.dev`). Can be overridden per-command.

## UTM Parameter Handling

Dub supports UTM parameters two ways. The CLI supports both:

### Option A: Baked into the URL (simple)

Just include UTMs in your destination URL. What you give is what you get.

```bash
dub add "https://continue.dev/signup?utm_source=snyk&utm_medium=blog&utm_campaign=partner-q1-2026" -k snyk-blog
```

**Result when clicked:**
```
https://continue.dev/signup?utm_source=snyk&utm_medium=blog&utm_campaign=partner-q1-2026
```

### Option B: Separate UTM flags (flexible)

Pass a clean base URL and specify UTMs as flags. Dub stores them separately and appends them on redirect.

```bash
dub add "https://continue.dev/signup" -k snyk-blog \
  --utm-source snyk --utm-medium blog --utm-campaign partner-q1-2026
```

**Result when clicked:**
```
https://continue.dev/signup?utm_source=snyk&utm_medium=blog&utm_campaign=partner-q1-2026
```

### Why use separate flags?

1. **Dashboard filtering** — Dub lets you filter/search links by UTM values in their UI
2. **Parameter passthrough** — You can override UTMs at click time by appending to the short link:
   ```
   go.continue.dev/snyk?utm_medium=video
   ```
   This overrides the stored `utm_medium` value for that click only.
3. **Cleaner CSV** — Your CSV can have a single base URL column and separate UTM columns

### Which should you use?

- **Baked-in URLs** — Simpler, what you see is what you get, works with your existing CSV
- **Separate flags** — More flexible, better Dub dashboard experience, enables click-time overrides

The CLI auto-detects: if your URL already has `?utm_` params, it uses them as-is. If you also pass `--utm-*` flags, the flags take precedence and replace any URL params.

---

## Commands

### `dub add`

Create a single link or bulk-create from a CSV file.

**Single link:**
```bash
dub add <url> [options]
```

| Option | Description |
|--------|-------------|
| `--key`, `-k` | Custom slug (e.g., `snyk-blog`). If omitted, Dub generates a random key. |
| `--domain`, `-d` | Domain to use. Defaults to `DUB_DOMAIN` env var. |
| `--tag`, `-t` | Tag name to apply. Can be repeated for multiple tags. |
| `--utm-source` | Set utm_source (overrides any in URL) |
| `--utm-medium` | Set utm_medium (overrides any in URL) |
| `--utm-campaign` | Set utm_campaign (overrides any in URL) |
| `--utm-term` | Set utm_term (overrides any in URL) |
| `--utm-content` | Set utm_content (overrides any in URL) |

**Examples:**
```bash
# Option A: Full URL with UTMs baked in
dub add "https://continue.dev/signup?utm_source=snyk&utm_medium=blog&utm_campaign=partner-q1-2026" -k snyk-blog

# Option B: Clean URL + separate UTM flags
dub add "https://continue.dev/signup" -k snyk-blog \
  --utm-source snyk --utm-medium blog --utm-campaign partner-q1-2026

# Both produce the same result. Option B stores UTMs separately in Dub.

# With tags
dub add "https://continue.dev/signup" -k snyk-blog -t partner -t snyk
```

**Bulk from CSV:**
```bash
dub add --file <path.csv> [options]
```

| Option | Description |
|--------|-------------|
| `--file`, `-f` | Path to CSV file |
| `--domain`, `-d` | Default domain (can be overridden per-row in CSV) |
| `--dry-run` | Validate and preview without creating |

**CSV format:**

Required columns: `url`

Optional columns: `key`, `domain`, `tag`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`

**Option A: Full URLs with UTMs baked in**
```csv
url,key
https://continue.dev/signup?utm_source=snyk&utm_medium=blog&utm_campaign=partner-q1-2026&utm_content=snyk-blog,snyk-blog
https://continue.dev/signup?utm_source=snyk&utm_medium=video&utm_campaign=partner-q1-2026&utm_content=snyk-video,snyk-video
```

**Option B: Clean URLs with separate UTM columns**
```csv
url,key,utm_source,utm_medium,utm_campaign,utm_content
https://continue.dev/signup,snyk-blog,snyk,blog,partner-q1-2026,snyk-blog
https://continue.dev/signup,snyk-video,snyk,video,partner-q1-2026,snyk-video
```

Both produce identical redirects. Option B stores UTMs as separate fields in Dub, enabling dashboard filtering and click-time overrides.

**Behavior:**
- If `url` contains `?utm_*` params AND UTM columns are present, columns take precedence
- If `url` contains `?utm_*` params and no UTM columns, params are extracted and stored separately in Dub
- Empty UTM columns are ignored

**Output:**
```
Created: go.continue.dev/snyk-blog → https://continue.dev/signup?utm_source=snyk...
Created: go.continue.dev/snyk-video → https://continue.dev/signup?utm_source=snyk...

2 links created.
```

On error, report which rows failed and continue processing remaining rows.

---

### `dub list`

List links in the workspace.

```bash
dub list [options]
```

| Option | Description |
|--------|-------------|
| `--domain`, `-d` | Filter by domain |
| `--tag`, `-t` | Filter by tag name |
| `--search`, `-s` | Search by URL or key |
| `--limit`, `-n` | Max results (default: 50, max: 100) |
| `--format` | Output format: `table` (default), `json`, `csv` |
| `--sort` | Sort by: `created` (default), `clicks`, `updated` |

**Examples:**
```bash
# List all
dub list

# Filter by domain
dub list -d go.continue.dev

# Filter by tag
dub list -t snyk

# Search
dub list -s "snyk"

# Export to CSV
dub list -d go.continue.dev --format csv > links.csv

# JSON for scripting
dub list --format json | jq '.[] | .shortLink'
```

**Table output:**
```
SHORT LINK                      DESTINATION                                      CLICKS  CREATED
go.continue.dev/snyk-blog       https://continue.dev/signup?utm_source=snyk...   142     2026-01-15
go.continue.dev/snyk-video      https://continue.dev/signup?utm_source=snyk...   89      2026-01-15
go.continue.dev/snyk-lab        https://continue.dev/signup?utm_source=snyk...   312     2026-01-16

3 links (showing 3)
```

**JSON output:**
```json
[
  {
    "id": "clv3o9p9q000au1h0mc7r6l63",
    "shortLink": "go.continue.dev/snyk-blog",
    "url": "https://continue.dev/signup?utm_source=snyk&utm_medium=blog...",
    "clicks": 142,
    "createdAt": "2026-01-15T10:30:00Z"
  }
]
```

---

### `dub rm`

Remove one or more links.

```bash
dub rm <key-or-id>... [options]
```

| Option | Description |
|--------|-------------|
| `--domain`, `-d` | Domain (required if using key, not ID) |
| `--force`, `-f` | Skip confirmation prompt |
| `--file` | Remove links listed in a file (one key/ID per line) |

**Examples:**
```bash
# Remove single link by key
dub rm snyk-blog -d go.continue.dev

# Remove by link ID
dub rm clv3o9p9q000au1h0mc7r6l63

# Remove multiple
dub rm snyk-blog snyk-video snyk-lab -d go.continue.dev

# Skip confirmation
dub rm snyk-blog -d go.continue.dev -f

# Bulk remove from file
dub rm --file links-to-delete.txt -d go.continue.dev
```

**Confirmation prompt (unless `--force`):**
```
Delete go.continue.dev/snyk-blog? (142 clicks) [y/N]: y
Deleted: go.continue.dev/snyk-blog
```

**Bulk confirmation:**
```
About to delete 3 links:
  - go.continue.dev/snyk-blog (142 clicks)
  - go.continue.dev/snyk-video (89 clicks)
  - go.continue.dev/snyk-lab (312 clicks)

Proceed? [y/N]: y
Deleted: 3 links
```

---

### `dub stats`

Get click stats for a link (nice-to-have, not core).

```bash
dub stats <key-or-id> [options]
```

| Option | Description |
|--------|-------------|
| `--domain`, `-d` | Domain (required if using key) |
| `--period` | Time period: `24h`, `7d`, `30d`, `90d`, `all` (default: `30d`) |

**Output:**
```
go.continue.dev/snyk-lab

Total clicks: 312 (last 30 days)

By day:
  2026-01-16: ████████████████████ 89
  2026-01-17: ████████████████████████████ 124
  2026-01-18: ██████████████████████ 99

Top referrers:
  twitter.com      45%
  linkedin.com     28%
  direct           18%
  other             9%

Top locations:
  United States    62%
  United Kingdom   12%
  Germany           8%
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API failure, network issue) |
| 2 | Invalid arguments or missing required options |
| 3 | Authentication error (bad API key) |
| 4 | Resource not found (link doesn't exist) |
| 5 | Partial failure (some bulk operations failed) |

---

## Error Handling

- **API errors:** Print error message from Dub API, exit with code 1.
- **Rate limits:** Retry with exponential backoff (max 3 retries), then fail.
- **Bulk partial failures:** Continue processing, report failures at end, exit with code 5.
- **Invalid CSV:** Validate all rows before processing. Report row numbers with errors.

---

## Dependencies

- `httpx` or `requests` — HTTP client
- `click` or `typer` — CLI framework
- `rich` — Pretty table output and progress bars
- `python-dotenv` — Load env vars from `.env` file

---

## Future Enhancements (Out of Scope for v1)

- `dub update` — Modify existing link destination or metadata
- `dub export` — Export all links to CSV
- `dub tags` — Manage tags (create, list, delete)
- Interactive mode / TUI
- Config file (~/.dub.toml) as alternative to env vars

