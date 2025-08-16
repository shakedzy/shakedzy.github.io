# Content Fetcher Scripts

This directory contains scripts for automatically fetching content from external sources to keep your personal website updated.

## Files

- `content-fetcher.py` - Main script that fetches content from various sources
- `../data/content-sources.json` - Configuration for content sources
- `../requirements.txt` - Python dependencies

## Usage

### Manual Update

```bash
# Install dependencies
pip install -r requirements.txt

# Run the content fetcher
cd scripts
python content-fetcher.py

# Or specify a custom base path
python content-fetcher.py /path/to/your/website
```

### Automatic Updates

The GitHub Actions workflow in `.github/workflows/update-content.yml` automatically runs daily at 6 AM UTC to fetch new content.

You can also trigger it manually:
1. Go to your GitHub repository
2. Click on "Actions" tab
3. Select "Update Content from External Sources"
4. Click "Run workflow"

## Supported Sources

### Medium
- **Type**: RSS Feed
- **URL**: `https://shakedzy.medium.com/feed`
- **Features**: Automatic title, description, date, and link extraction

### JFrog Blog
- **Type**: Web Scraping
- **URL**: `https://jfrog.com/blog-author/shaked-zychlinski/`
- **Status**: Mock data (implement scraping logic)

### Taboola Blog  
- **Type**: Web Scraping
- **URL**: `https://www.taboola.com/author/shakedzy/`
- **Status**: Mock data (implement scraping logic)

### YouTube
- **Type**: YouTube Data API
- **Status**: Requires API key (not implemented)

## Configuration

Edit `data/content-sources.json` to:
- Enable/disable sources
- Add new sources
- Configure update frequency
- Set API keys

## Manual Items

You can still add manual items to `data/talks.json` under the `manual_items` array. These will be merged with auto-fetched content and sorted chronologically.

## Data Structure

The fetched content is stored in `data/talks.json`:

```json
{
  "manual_items": [
    {
      "id": "manual_1",
      "title": "Custom Talk",
      "platform": "Conference",
      "type": "Keynote",
      "link": "https://...",
      "icon": "fas fa-microphone",
      "date": "2024-03-15",
      "views": "1.2K",
      "source": "manual"
    }
  ],
  "auto_fetched": [
    {
      "id": "medium_123",
      "title": "Article Title",
      "platform": "Medium",
      "type": "Article",
      "link": "https://...",
      "icon": "fab fa-medium",
      "date": "2024-01-15",
      "views": "2.1K",
      "source": "medium",
      "description": "Article description..."
    }
  ]
}
```

## Extending

To add new content sources:

1. Add the source configuration to `content-sources.json`
2. Implement the fetching logic in `content-fetcher.py`
3. Add appropriate icon mappings in the frontend JavaScript

## Rate Limiting

The script includes built-in rate limiting (1 second between requests) to be respectful to source websites.
