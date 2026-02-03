# dubco-cli

A CLI for managing [Dub.co](https://dub.co) short links with OAuth PKCE authentication.

## Installation

```bash
pip install dubco-cli
```

Or with uv:

```bash
uv pip install dubco-cli
```

## Quick Start

### 1. Login

```bash
dub login
```

On first run, you'll be guided to create an OAuth app in your Dub workspace:

1. Go to https://app.dub.co/settings/oauth-apps
2. Create an OAuth App with redirect URI: `http://localhost:8484/callback`
3. Copy and paste the Client ID when prompted

### 2. Create a short link

```bash
# Simple
dub add https://example.com

# With custom key and domain
dub add https://example.com -k my-link -d dub.sh

# With UTM parameters
dub add https://example.com --utm-source twitter --utm-campaign launch

# With tags
dub add https://example.com -t marketing -t launch
```

### 3. List your links

```bash
# Table format (default)
dub list

# JSON output
dub list --format json

# Filter by domain or tag
dub list -d dub.sh -t marketing

# Search
dub list -s "campaign"
```

### 4. Delete links

```bash
# By key (requires domain)
dub rm my-link -d dub.sh

# By link ID
dub rm clx1234567890

# Skip confirmation
dub rm my-link -d dub.sh --force
```

### 5. View link stats

```bash
dub stats my-link -d dub.sh
```

## Bulk Operations

### Create links from CSV

```bash
dub add -f links.csv
```

CSV format:
```csv
url,key,domain,tag,utm_source,utm_medium,utm_campaign
https://example.com/page1,page1,dub.sh,marketing,twitter,social,launch
https://example.com/page2,page2,dub.sh,sales,email,newsletter,promo
```

### Delete links from file

```bash
dub rm --file links-to-delete.txt --force
```

## Commands

| Command | Description |
|---------|-------------|
| `dub login` | Authenticate with Dub.co |
| `dub logout` | Clear stored credentials |
| `dub whoami` | Show current authentication status |
| `dub add` | Create a new short link |
| `dub list` | List your short links |
| `dub rm` | Delete short links |
| `dub stats` | View link statistics |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication error |
| 4 | Not found |
| 5 | Partial failure (bulk operations) |

## Development

```bash
# Clone the repo
git clone https://github.com/metcalfc/dubco.git
cd dubco

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .
ruff check --fix .
```

## License

MIT
