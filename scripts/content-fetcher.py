#!/usr/bin/env python3
"""
Content Fetcher for Personal Website
Automatically fetches content from various sources and updates JSON files.
"""

import re
import os
import sys
import time
import json
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup

load_dotenv(override=True)
ssl_verify = True
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


class ContentFetcher:
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.data_path = os.path.join(base_path, "data")
        self.sources_config = self.load_sources_config()
        
    def load_sources_config(self) -> dict:
        """Load content sources configuration from content.json"""
        try:
            with open(os.path.join(self.base_path, "content.json"), 'r') as f:
                content = json.load(f)
                sources_config = content.get("content_sources", {})
                
                # Convert new structure to old format for compatibility
                sources = []
                
                # Medium source
                if sources_config.get("medium", {}).get("enabled"):
                    sources.append({
                        "id": "medium",
                        "name": "Medium",
                        "type": "rss",
                        "url": f"https://medium.com/feed/@" + sources_config["medium"]["username"],
                        "username": sources_config["medium"]["username"],
                        "icon": "fab fa-medium",
                        "platform": "Medium",
                        "enabled": True,
                        "language": sources_config["medium"].get("language", "en")
                    })
                
                # YouTube source
                if sources_config.get("youtube", {}).get("enabled"):
                    sources.append({
                        "id": "youtube",
                        "name": "YouTube", 
                        "type": "youtube_api",
                        "url": f"https://www.youtube.com/{content['personal']['youtube_channel']}",
                        "channel_id": "",
                        "icon": "fab fa-youtube",
                        "platform": "YouTube",
                        "enabled": True,
                        "playlists": sources_config["youtube"]["playlists"]
                    })
                
                # Spotify source
                if sources_config.get("spotify", {}).get("enabled"):
                    sources.append({
                        "id": "spotify",
                        "name": "Spotify",
                        "type": "spotify_api",
                        "icon": "fab fa-spotify",
                        "platform": "Spotify", 
                        "enabled": True,
                        "podcasts": sources_config["spotify"]["podcasts"]
                    })
                
                # Blog sources are processed separately, not added to main sources list
                
                return {"sources": sources}
                
        except FileNotFoundError:
            print("❌ content.json not found")
            return {"sources": []}
        except KeyError as e:
            print(f"❌ Missing key in content.json: {e}")
            return {"sources": []}
    
    def load_talks_data(self) -> dict:
        """Load existing talks data"""
        try:
            with open(os.path.join(self.data_path, "talks.json"), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"manual_items": [], "auto_fetched": []}
    
    def save_talks_data(self, data: dict):
        """Save updated talks data"""
        with open(os.path.join(self.data_path, "talks.json"), 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved talks data with {len(data.get('auto_fetched', []))} auto-fetched items")
    
    def fetch_medium_rss(self, username: str) -> list[dict]:
        """Fetch articles from Medium RSS feed"""
        rss_url = f"https://medium.com/feed/@{username}"
        api_url = "https://api.rss2json.com/v1/api.json"
        print(f"📡 Fetching Medium RSS: {rss_url}")
        
        try:
            resp = requests.get(api_url, params={"rss_url": rss_url})
            resp.raise_for_status()
            data = resp.json()

            articles = []
            items = data.get("items", [])
            for i, item in enumerate(items):
                title = item.get("title", "")
                content = item.get("content", "")
                snippet = (BeautifulSoup(content, "html.parser")
                        .get_text()[:100] + "…")
                date = item.get("pubDate", "")
                link = item.get("link", "")

                articles.append({
                    "id": f"medium_{i}",
                    "title": title,
                    "platform": "Medium",
                    "type": "Article",
                    "link": link,
                    "icon": "fab fa-medium",
                    "date": datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y"),
                    "claps": None,
                    "source": "medium",
                    "description": snippet,
                    "language": "en"  
                    })
            
            print(f"Found {len(items)} entries in feed")
            return articles
            
        except Exception as e:
            print(f"❌ Error fetching Medium RSS: {e}")
            return []
    
    def get_medium_claps(self, article_url: str) -> str | None:
        """Get claps count from Medium article page"""
        try:
            headers = {
                'User-Agent': user_agent
            }
            response = requests.get(article_url, headers=headers, timeout=10, verify=ssl_verify)
            response.raise_for_status()
            
            # Look for claps data in the page
            content = response.text
            
            # Try to find claps in JSON-LD data
            json_ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
            if json_ld_match:
                try:
                    json_data = json.loads(json_ld_match.group(1))
                    if isinstance(json_data, dict) and 'interactionStatistic' in json_data:
                        for stat in json_data['interactionStatistic']:
                            if stat.get('interactionType') == 'https://schema.org/LikeAction':
                                claps = stat.get('userInteractionCount', 0)
                                if claps > 0:
                                    return self.format_claps(claps)
                except:
                    pass
            
            # Fallback: look for claps in HTML
            claps_match = re.search(r'"clapCount":(\d+)', content)
            if claps_match:
                claps = int(claps_match.group(1))
                return self.format_claps(claps)
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch claps for {article_url}: {e}")
            return None
    
    def format_claps(self, claps: int) -> str:
        """Format claps count nicely"""
        if claps >= 1000000:
            return f"{claps/1000000:.1f}M"
        elif claps >= 1000:
            return f"{claps/1000:.1f}K"
        else:
            return str(claps)
    
    def fetch_jfrog_blog(self, url: str, xpath: str = None) -> list[dict]:
        """Fetch articles from JFrog blog author page"""
        print(f"📡 Fetching JFrog blog: {url}")
        
        try:
            headers = {
                'User-Agent': user_agent
            }
            response = requests.get(url, headers=headers, timeout=10, verify=ssl_verify)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            
            # If XPath is provided, use it to find the specific section
            if xpath:
                print(f"   🎯 Using XPath selector: {xpath}")
                target_section = None
                
                # Convert XPath to CSS selector approximation for BeautifulSoup
                if "latest-posts-from-blog-author" in xpath:
                    target_section = soup.find('div', class_='latest-posts-from-blog-author')
                    print(f"   🔍 Looking for div with class 'latest-posts-from-blog-author'")
                    if target_section:
                        print(f"   ✅ Found latest-posts-from-blog-author div")
                    else:
                        print(f"   ❌ latest-posts-from-blog-author div not found")
                elif "site-content" in xpath:
                    # For Taboola: //*[@id='site-content']/section[2]/div/div/div/div
                    site_content = soup.find('div', id='site-content')
                    if site_content:
                        print(f"   🔍 Found site-content div, looking for section[2]")
                        sections = site_content.find_all('section')
                        if len(sections) >= 2:
                            target_section = sections[1]  # section[2] is index 1
                            print(f"   ✅ Found section[2], now looking for div/div/div/div")
                            # Navigate through the div hierarchy more carefully
                            current = target_section
                            for i in range(4):  # div/div/div/div
                                divs = current.find_all('div', recursive=False)
                                if divs:
                                    # Try to find the right div - look for one with content
                                    best_div = divs[0]  # Default to first
                                    for div in divs:
                                        # Check if this div has meaningful content
                                        if div.find_all('a', href=True):
                                            best_div = div
                                            break
                                    current = best_div
                                    print(f"      Level {i+1}: Found {len(divs)} divs, selected one with {len(current.find_all('a', href=True))} links")
                                else:
                                    print(f"      Level {i+1}: No divs found")
                                    break
                            target_section = current
                        else:
                            print(f"   ⚠️  Only found {len(sections)} sections, need at least 2")
                            # Fallback: try to find any section with content
                            print(f"   🔄 Fallback: looking for any section with content")
                            for section in sections:
                                if section.find_all('a', href=True):
                                    target_section = section
                                    print(f"   ✅ Found section with {len(target_section.find_all('a', href=True))} links")
                                    break
                    else:
                        print(f"   ❌ site-content div not found")
                        # Fallback: try to find any div with id containing 'content'
                        print(f"   🔄 Fallback: looking for any content div")
                        content_divs = soup.find_all('div', id=re.compile(r'content'))
                        if content_divs:
                            target_section = content_divs[0]
                            print(f"   ✅ Found content div with {len(target_section.find_all('a', href=True))} links")
                else:
                    print(f"   ⚠️  Unknown XPath pattern: {xpath}")
                
                if target_section:
                    print(f"   🎯 Target section found, extracting links...")
                    blog_links = target_section.find_all('a', href=True)
                    print(f"   🔍 Found {len(blog_links)} links in target section")
                    
                    # If no links found in target section, allow fallback for Taboola
                    if len(blog_links) == 0 and "site-content" in xpath:
                        print(f"   🔄 Target section is empty, allowing fallback to entire page for Taboola")
                        blog_links = soup.find_all('a', href=True)
                        print(f"   🔍 Fallback found {len(blog_links)} links in entire page")
                else:
                    print(f"   ❌ Target section not found, XPath targeting failed")
                    # For Taboola, allow fallback to entire page to get content back
                    if "site-content" in xpath:
                        print(f"   🔄 Allowing fallback to entire page for Taboola")
                        blog_links = soup.find_all('a', href=True)
                    else:
                        print(f"   📝 Will NOT search entire page - respecting XPath boundaries")
                        blog_links = []  # Empty list to force no results
            else:
                # Look for ONLY actual blog post links - be very selective
                blog_links = soup.find_all('a', href=True)
            
            found_articles = set()  # Track found articles to avoid duplicates
            
            # Process ONLY blog post links with very strict filtering
            for link in blog_links[:50]:  # Check more links to find actual posts
                href = str(link.get('href', ''))
                title = link.get_text().strip()
                
                # VERY STRICT filtering - only actual blog posts
                if (href and 
                    title and 
                    len(title) > 20 and  # Longer titles are more likely to be articles
                    len(title) < 200 and  # But not too long
                    '/blog/' in href and  # Must contain /blog/ in URL
                    not title.lower().startswith('http') and
                    not title.lower().startswith('www') and
                    title.lower() not in ['read more', 'continue reading', 'blog', 'home', 'about', 'back to blog', 'engineering blog', 'community', 'documentation', 'integrations', 'applications'] and
                    not href.startswith('#') and
                    not href.startswith('mailto:') and
                    not href.startswith('tel:') and
                    not any(nav in title.lower() for nav in ['menu', 'navigation', 'footer', 'header', 'sidebar', 'breadcrumb', 'pagination'])):
                    
                    # Get full URL
                    if href.startswith('/'):
                        full_url = f"https://jfrog.com{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://jfrog.com/{href}"
                    
                    # Skip if we already found this article
                    if full_url in found_articles:
                        continue
                    
                    # Additional validation - check if the URL looks like a blog post
                    if not any(post_indicator in full_url.lower() for post_indicator in ['/blog/', '/post/', '/article/', '/news/', '/insights/']):
                        continue
                    
                    found_articles.add(full_url)
                    
                    # Try to get article metadata
                    article_data = self.get_jfrog_article_metadata(full_url)
                    
                    article = {
                        "id": f"jfrog_{abs(hash(full_url)) % 10000}",
                        "title": title,
                        "platform": "JFrog",
                        "type": "Technical Article",
                        "link": full_url,
                        "icon": "fas fa-blog",
                        "date": article_data.get('date', 'Unknown'),
                        "views": article_data.get('views'),
                        "source": "jfrog",
                        "description": article_data.get('description', ''),
                        "language": "en"
                    }
                    articles.append(article)
                    print(f"   📄 {title}")
            
            # If XPath was provided, ONLY use content from the target section - no fallback to entire page
            if xpath and len(articles) < 3:
                print(f"   ⚠️  Only found {len(articles)} articles in XPath section '{xpath}' - respecting boundaries")
                print(f"   📝 XPath targeting is working - only extracting from specified section")
            elif not xpath and len(articles) < 3:
                print(f"   🔍 Only found {len(articles)} articles, looking for more blog-like content...")
                for link in blog_links[:100]:
                    href = str(link.get('href', ''))
                    title = link.get_text().strip()
                    
                    # Look for any remaining content that might be blog posts
                    if (href and 
                        title and 
                        len(title) > 25 and  # Even longer titles
                        len(title) < 150 and
                        not title.lower().startswith('http') and
                        not any(nav in title.lower() for nav in ['menu', 'navigation', 'footer', 'header', 'sidebar', 'breadcrumb', 'pagination', 'community', 'documentation', 'integrations', 'applications', 'resources', 'partners', 'about', 'contact', 'privacy', 'terms', 'cookies', 'sitemap']) and
                        not href.startswith('#') and
                        not href.startswith('mailto:') and
                        not href.startswith('tel:')):
                        
                        # Get full URL
                        if href.startswith('/'):
                            full_url = f"https://jfrog.com{href}"
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            full_url = f"https://jfrog.com/{href}"
                        
                        # Skip if we already found this article
                        if full_url in found_articles:
                            continue
                        
                        found_articles.add(full_url)
                        
                        # Try to get article metadata
                        article_data = self.get_jfrog_article_metadata(full_url)
                        
                        article = {
                            "id": f"jfrog_{abs(hash(full_url)) % 10000}",
                            "title": title,
                            "platform": "JFrog",
                            "type": "Technical Article",
                            "link": full_url,
                            "icon": "fas fa-blog",
                            "date": article_data.get('date', 'Unknown'),
                            "views": article_data.get('views'),
                            "source": "jfrog",
                            "description": article_data.get('description', ''),
                            "language": "en"
                        }
                        articles.append(article)
                        print(f"   📄 {title}")
                        
                        if len(articles) >= 5:  # Limit to 5 articles max
                            break
            
            print(f"✅ Fetched {len(articles)} JFrog articles")
            return articles
            
        except Exception as e:
            print(f"❌ Error fetching JFrog blog: {e}")
            return []
    
    def get_jfrog_article_metadata(self, article_url: str) -> dict:
        """Get metadata from JFrog article page"""
        try:
            headers = {
                'User-Agent': user_agent
            }
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = str(meta_desc.get('content', ''))
                if len(content) > 120:
                    description = content[:120] + "..."
                else:
                    description = content
            
            # Extract date
            date = "Unknown"
            date_elem = soup.find('time') or soup.find(class_=re.compile(r'date|published|time'))
            if date_elem:
                date_text = date_elem.get_text().strip()
                if date_text:
                    date = date_text
            
            return {
                'description': description,
                'date': date,
                'views': None  # JFrog doesn't typically show view counts
            }
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch metadata for {article_url}: {e}")
            return {'description': '', 'date': 'Unknown', 'views': None}
    
    def fetch_taboola_blog(self, url: str, xpath: str = None) -> list[dict]:
        """Fetch articles from Taboola blog author page"""
        print(f"📡 Fetching Taboola blog: {url}")
        
        try:
            headers = {
                'User-Agent': user_agent
            }
            response = requests.get(url, headers=headers, timeout=10, verify=ssl_verify)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            
            # If XPath is provided, use it to find the specific section
            if xpath:
                print(f"   🎯 Using XPath selector: {xpath}")
                # Convert XPath to CSS selector approximation for BeautifulSoup
                if "site-content" in xpath:
                    target_section = soup.find('div', id='site-content')
                    if target_section:
                        # Navigate to section[2]/div/div/div/div
                        sections = target_section.find_all('section')
                        if len(sections) >= 2:
                            target_section = sections[1]  # section[2] is index 1
                        else:
                            target_section = soup
                else:
                    # Fallback to searching the entire page
                    target_section = soup
                
                if target_section:
                    blog_links = target_section.find_all('a', href=True)
                    print(f"   🔍 Found {len(blog_links)} links in target section")
                else:
                    print(f"   ⚠️  Target section not found, searching entire page")
                    blog_links = soup.find_all('a', href=True)
            else:
                # Look for blog post links - adjust selectors based on Taboola's actual HTML structure
                blog_links = soup.find_all('a', href=True)
            
            # Also look for article/post elements
            post_elements = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|entry|blog'))
            
            found_articles = set()  # Track found articles to avoid duplicates
            
            # Process ONLY actual blog post links with very strict filtering
            for link in blog_links[:50]:  # Check more links to find actual posts
                href = str(link.get('href', ''))
                title = link.get_text().strip()
                
                # VERY STRICT filtering - only actual blog posts
                if (href and 
                    title and 
                    len(title) > 20 and  # Longer titles are more likely to be articles
                    len(title) < 200 and  # But not too long
                    any(path in href for path in ['/blog/', '/post/', '/article/', '/engineering/']) and  # Must contain blog-related paths
                    not title.lower().startswith('http') and
                    not title.lower().startswith('www') and
                    title.lower() not in ['read more', 'continue reading', 'blog', 'home', 'about', 'engineering blog', 'community', 'documentation', 'integrations', 'applications', 'resources', 'partners', 'social responsibility', 'glossary', 'quickstart', 'webinars', 'trends', 'marketing'] and
                    not href.startswith('#') and
                    not href.startswith('mailto:') and
                    not href.startswith('tel:') and
                    not any(nav in title.lower() for nav in ['menu', 'navigation', 'footer', 'header', 'sidebar', 'breadcrumb', 'pagination'])):
                    
                    # Get full URL
                    if href.startswith('/'):
                        full_url = f"https://www.taboola.com{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://www.taboola.com/{href}"
                    
                    # Skip if we already found this article
                    if full_url in found_articles:
                        continue
                    
                    # Additional validation - check if the URL looks like a blog post
                    if not any(post_indicator in full_url.lower() for post_indicator in ['/blog/', '/post/', '/article/', '/news/', '/insights/', '/engineering/']):
                        continue
                    
                    found_articles.add(full_url)
                    
                    # Try to get article metadata
                    article_data = self.get_taboola_article_metadata(full_url)
                    
                    article = {
                        "id": f"taboola_{abs(hash(full_url)) % 10000}",
                        "title": title,
                        "platform": "Taboola",
                        "type": "Engineering Article",
                        "link": full_url,
                        "icon": "fas fa-code",
                        "date": article_data.get('date', 'Unknown'),
                        "views": article_data.get('views'),
                        "source": "taboola",
                        "description": article_data.get('description', ''),
                        "language": "en"
                    }
                    articles.append(article)
                    print(f"   📄 {title}")
            
            # If XPath was provided, ONLY use content from the target section - no fallback to entire page
            if xpath and len(articles) < 3:
                print(f"   ⚠️  Only found {len(articles)} articles in XPath section '{xpath}' - respecting boundaries")
                print(f"   📝 XPath targeting is working - only extracting from specified section")
            elif not xpath and len(articles) < 3:
                print(f"   🔍 Only found {len(articles)} articles, looking for more blog-like content...")
                for link in blog_links[:100]:
                    href = str(link.get('href', ''))
                    title = link.get_text().strip()
                    
                    # Look for any remaining content that might be blog posts
                    if (href and 
                        title and 
                        len(title) > 25 and  # Even longer titles
                        len(title) < 150 and
                        not title.lower().startswith('http') and
                        not any(nav in title.lower() for nav in ['menu', 'navigation', 'footer', 'header', 'sidebar', 'breadcrumb', 'pagination', 'community', 'documentation', 'integrations', 'applications', 'resources', 'partners', 'about', 'contact', 'privacy', 'terms', 'cookies', 'sitemap', 'social responsibility', 'glossary', 'quickstart', 'webinars', 'trends', 'marketing']) and
                        not href.startswith('#') and
                        not href.startswith('mailto:') and
                        not href.startswith('tel:')):
                        
                        # Get full URL
                        if href.startswith('/'):
                            full_url = f"https://www.taboola.com{href}"
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            full_url = f"https://www.taboola.com/{href}"
                        
                        found_articles.add(full_url)
                        
                        # Try to get article metadata
                        article_data = self.get_taboola_article_metadata(full_url)
                        
                        article = {
                            "id": f"taboola_{abs(hash(full_url)) % 10000}",
                            "title": title,
                            "platform": "Taboola",
                            "type": "Engineering Article",
                            "link": full_url,
                            "icon": "fas fa-code",
                            "date": article_data.get('date', 'Unknown'),
                            "views": article_data.get('views'),
                            "source": "taboola",
                            "description": article_data.get('description', ''),
                            "language": "en"
                        }
                        articles.append(article)
                        print(f"   📄 {title}")
                        
                        if len(articles) >= 5:  # Limit to 5 articles max
                            break
            
            print(f"✅ Fetched {len(articles)} Taboola articles")
            return articles
            
        except Exception as e:
            print(f"❌ Error fetching Taboola blog: {e}")
            return []
    
    def get_taboola_article_metadata(self, article_url: str) -> dict:
        """Get metadata from Taboola article page"""
        try:
            headers = {
                'User-Agent': user_agent
            }
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = str(meta_desc.get('content', ''))
                if len(content) > 120:
                    description = content[:120] + "..."
                else:
                    description = content
            
            # Extract date
            date = "Unknown"
            date_elem = soup.find('time') or soup.find(class_=re.compile(r'date|published|time'))
            if date_elem:
                date_text = date_elem.get_text().strip()
                if date_text:
                    date = date_text
            
            return {
                'description': description,
                'date': date,
                'views': None  # Taboola doesn't typically show view counts
            }
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch metadata for {article_url}: {e}")
            return {'description': '', 'date': 'Unknown', 'views': None}
    
    def fetch_spotify_episodes(self, source_config: dict) -> list[dict]:
        """Fetch episodes from Spotify podcasts"""
        print("📡 Fetching Spotify podcast episodes")
        
        try:
            spotify_app_id = os.environ['SPOTIFY_APP_ID']
            spotify_app_secret = os.environ['SPOTIFY_APP_SECRET']

            auth_response = requests.post(
                "https://accounts.spotify.com/api/token", 
                data={
                    "grant_type": "client_credentials"
                }, auth=(spotify_app_id, spotify_app_secret))
            token = auth_response.json()["access_token"]

            all_episodes = []
            podcasts = source_config.get('podcasts', [])
            
            for podcast in podcasts:
                podcast_name = podcast.get('name', '')
                print(f"   🎧 Processing podcast: {podcast_name}")
                podcast_language = podcast.get('language', 'en')
                podcast_episodes = requests.get(
                    "https://api.spotify.com/v1/shows/6tdxOe9J5qjykTLRvB6blL/episodes?limit=50",
                    headers={"Authorization": f"Bearer {token}"}
                ).json().get("items", [])
                for i, episode in enumerate(podcast_episodes):
                    all_episodes.append({
                        "id": f"spotify_{podcast_name}_{i}",
                        "title": episode["name"],
                        "link": episode["external_urls"]["spotify"],
                        "date": datetime.strptime(episode["release_date"], "%Y-%m-%d").strftime("%b %d, %Y"),
                        "description": episode["description"],
                        "platform": "Spotify",
                        "type": "Podcast",
                        "icon": "fab fa-spotify",
                        "views": None,
                        "source": "spotify",
                        "show_name": podcast_name,
                        "language": podcast_language,
                    })
                
            
            print(f"✅ Successfully fetched {len(all_episodes)} Spotify episodes")
            return all_episodes
            
        except Exception as e:
            print(f"❌ Error fetching Spotify episodes: {e}")
            return []
    
    def fetch_youtube_videos(self, channel_info: dict) -> list[dict]:
        """Fetch videos from specific YouTube playlists"""
        print(f"📡 Fetching YouTube videos from playlists")
        
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            print("⚠️  YOUTUBE_API_KEY environment variable not set")
            return []
        
        try:
            # Extract channel username/handle from URL
            channel_url = channel_info.get('url', '')
            channel_username = None
            channel_id = channel_info.get('channel_id')
            
            if 'youtube.com/shakedzy' in channel_url or 'youtube.com/c/shakedzy' in channel_url:
                channel_username = 'shakedzy'
            elif 'youtube.com/@' in channel_url:
                channel_username = channel_url.split('@')[-1]
            
            print(f"   Channel username: {channel_username}")
            print(f"   Channel ID: {channel_id}")
            
            # If we don't have channel_id, try to get it from username
            if not channel_id and channel_username:
                channel_id = self.get_youtube_channel_id(api_key, channel_username)
                print(f"   Retrieved channel ID: {channel_id}")
            
            if not channel_id:
                print("❌ Could not determine YouTube channel ID")
                return []
            
            # Get videos from configured playlists
            playlists_config = channel_info.get('playlists', {})
            all_videos = []
            
            for playlist_name, language in playlists_config.items():
                print(f"   🔍 Searching for playlist: {playlist_name}")
                playlist_id = self.find_playlist_by_name(api_key, channel_id, playlist_name)
                
                if playlist_id:
                    print(f"   📋 Found playlist ID: {playlist_id}")
                    videos = self.get_playlist_videos(api_key, playlist_id, max_results=20, playlist_name=playlist_name, language=language)
                    all_videos.extend(videos)
                    print(f"   ✅ Fetched {len(videos)} videos from '{playlist_name}'")
                else:
                    print(f"   ❌ Playlist '{playlist_name}' not found")
            
            print(f"✅ Successfully fetched {len(all_videos)} YouTube videos from playlists")
            return all_videos
            
        except Exception as e:
            print(f"❌ Error fetching YouTube videos: {e}")
            return []
    
    def fetch_github_repositories(self, username: str = "shakedzy") -> list[dict]:
        """Fetch repositories from GitHub API"""
        print(f"📡 Fetching GitHub repositories for {username}")
        
        try:
            # Get user repositories
            url = f"https://api.github.com/users/{username}/repos"
            headers = {
                'User-Agent': 'Personal-Website-Content-Fetcher/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Add GitHub token if available for higher rate limits
            GH_TOKEN = os.getenv('GH_TOKEN')
            if GH_TOKEN:
                headers['Authorization'] = f'token {GH_TOKEN}'
                print("   🔑 Using GitHub token for authentication")
            
            # Fetch all repositories (GitHub paginates at 30 per page)
            all_repos = []
            page = 1
            per_page = 100
            
            while True:
                params = {
                    'per_page': per_page,
                    'page': page,
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                repos = response.json()
                
                if not repos:  # No more repositories
                    break
                    
                all_repos.extend(repos)
                page += 1
                
                print(f"   📄 Fetched page {page-1} ({len(repos)} repos)")
                
                if len(repos) < per_page:  # Last page
                    break
                    
                time.sleep(0.5)  # Rate limiting
            
            print(f"   📊 Total repositories found: {len(all_repos)}")
            
            # Filter and format repositories
            formatted_repos = []
            for repo in all_repos:
                # Skip forks, archived, or private repos unless they're significant
                if repo.get('fork') and repo.get('stargazers_count', 0) < 5:
                    continue
                if repo.get('archived'):
                    continue
                if repo.get('private'):
                    continue
                
                # Skip repos with no description
                if not repo.get('description'):
                    continue
                    
                # Format repository data
                formatted_repo = {
                    "id": f"github_{repo['id']}",
                    "name": repo['name'],
                    "description": repo['description'][:120] + "..." if len(repo.get('description', '')) > 120 else repo.get('description', ''),
                    "github": f"{username}/{repo['name']}",
                    "link": repo['html_url'],
                    "language": repo.get('language') or 'Unknown',
                    "stars": repo.get('stargazers_count', 0),
                    "forks": repo.get('forks_count', 0),
                    "updated_at": repo.get('updated_at', ''),
                    "created_at": repo.get('created_at', ''),
                    "is_fork": repo.get('fork', False),
                    "topics": repo.get('topics', [])
                }
                
                formatted_repos.append(formatted_repo)
                print(f"   ⭐ {repo['name']} ({repo.get('stargazers_count', 0)} stars, {repo.get('language', 'Unknown')})")
            
            # Sort by stars (descending), then by update date
            formatted_repos.sort(key=lambda x: (x['stars'], x['updated_at']), reverse=True)
            
            # Take top repositories (limit to reasonable number)
            top_repos = formatted_repos[:20]
            
            print(f"✅ Successfully formatted {len(top_repos)} GitHub repositories")
            return top_repos
            
        except Exception as e:
            print(f"❌ Error fetching GitHub repositories: {e}")
            return []
    
    def get_youtube_channel_id(self, api_key: str, username: str) -> str:
        """Get YouTube channel ID from username/handle"""
        try:
            # Try forUsername first
            url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'id',
                'forUsername': username,
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                return data['items'][0]['id']
            
            # If forUsername doesn't work, try search API
            search_url = f"https://www.googleapis.com/youtube/v3/search"
            search_params = {
                'part': 'snippet',
                'q': username,
                'type': 'channel',
                'key': api_key,
                'maxResults': 1
            }
            
            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                return data['items'][0]['snippet']['channelId']
            
            return None
            
        except Exception as e:
            print(f"Error getting channel ID: {e}")
            return None
    
    def find_playlist_by_name(self, api_key: str, channel_id: str, playlist_name: str) -> str:
        """Find a playlist ID by its name within a channel"""
        try:
            url = f"https://www.googleapis.com/youtube/v3/playlists"
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'key': api_key,
                'maxResults': 50
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                if item['snippet']['title'] == playlist_name:
                    return item['id']
            
            # If not found in first page, check if there are more pages
            next_page_token = data.get('nextPageToken')
            while next_page_token:
                params['pageToken'] = next_page_token
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    if item['snippet']['title'] == playlist_name:
                        return item['id']
                
                next_page_token = data.get('nextPageToken')
            
            return None
            
        except Exception as e:
            print(f"Error finding playlist '{playlist_name}': {e}")
            return None
    
    def get_uploads_playlist_id(self, api_key: str, channel_id: str) -> str:
        """Get the uploads playlist ID for a channel"""
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'contentDetails',
                'id': channel_id,
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            return None
            
        except Exception as e:
            print(f"Error getting uploads playlist: {e}")
            return None
    
    def get_playlist_videos(self, api_key: str, playlist_id: str, max_results: int = 10, playlist_name: str = "", language: str = "en") -> list[dict]:
        """Get videos from a playlist"""
        try:
            url = f"https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'key': api_key,
                'maxResults': max_results,
                'order': 'date'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            videos = []
            for item in data.get('items', []):
                snippet = item['snippet']
                
                # Skip deleted/private videos
                if snippet['title'] == 'Deleted video' or snippet['title'] == 'Private video':
                    continue
                
                # Get video statistics for view count
                video_id = snippet['resourceId']['videoId']
                stats = self.get_video_statistics(api_key, video_id)
                
                video = {
                    "id": f"youtube_{video_id}",
                    "title": snippet['title'],
                    "platform": "YouTube",
                    "type": "Talk",
                    "link": f"https://www.youtube.com/watch?v={video_id}",
                    "icon": "fab fa-youtube",
                    "date": datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')).strftime("%Y-%m-%d"),
                    "views": stats.get('viewCount', 'N/A'),
                    "source": "youtube",
                    "description": snippet.get('description', '')[:120] + "..." if len(snippet.get('description', '')) > 120 else snippet.get('description', ''),
                    "playlist": playlist_name,
                    "language": language
                }
                videos.append(video)
                print(f"   🎥 {snippet['title']} (Talk {language})")
            
            return videos
            
        except Exception as e:
            print(f"Error getting playlist videos: {e}")
            return []
    
    def get_video_statistics(self, api_key: str, video_id: str) -> dict:
        """Get video statistics including view count"""
        try:
            url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'statistics',
                'id': video_id,
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                stats = data['items'][0]['statistics']
                # Format view count nicely
                view_count = int(stats.get('viewCount', 0))
                if view_count >= 1000000:
                    formatted_views = f"{view_count/1000000:.1f}M"
                elif view_count >= 1000:
                    formatted_views = f"{view_count/1000:.1f}K"
                else:
                    formatted_views = str(view_count)
                
                return {"viewCount": formatted_views}
            
            return {}
            
        except Exception as e:
            print(f"Error getting video statistics: {e}")
            return {}
    
    def fetch_all_content(self) -> list[dict]:
        """Fetch content from all enabled sources"""
        all_content = []
        
        # Process main sources (Medium, YouTube, Spotify)
        for source in self.sources_config.get("sources", []):
            if not source.get("enabled", False):
                continue
                
            print(f"\n🔄 Processing {source['name']}...")
            
            try:
                if source["type"] == "rss" and source["id"] == "medium":
                    content = self.fetch_medium_rss(source["username"])
                elif source["id"] == "youtube":
                    content = self.fetch_youtube_videos(source)
                elif source["id"] == "spotify":
                    content = self.fetch_spotify_episodes(source)
                else:
                    print(f"⚠️  Unsupported source type: {source['type']}")
                    continue
                
                # Add language tag to each content item (except YouTube which handles it internally)
                if source["id"] != "youtube" and source.get("language"):
                    for item in content:
                        item["language"] = source["language"]
                
                all_content.extend(content)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error processing {source['name']}: {e}")
        
        # Process blog sources separately
        # Load blogs directly from content.json since they're not in sources_config
        try:
            with open(os.path.join(self.base_path, "content.json"), 'r') as f:
                content = json.load(f)
                blog_sources = content.get("content_sources", {}).get("blogs", [])
        except Exception as e:
            print(f"   ❌ Error loading blog sources: {e}")
            blog_sources = []
        
        for blog_source in blog_sources:
            if not blog_source.get("enabled", False):
                continue
                
            print(f"\n🔄 Processing {blog_source['name']}...")
            
            try:
                if "jfrog" in blog_source["name"].lower():
                    xpath = blog_source.get("xpath")
                    print(f"   🔍 JFrog XPath: {xpath}")
                    content = self.fetch_jfrog_blog(blog_source["url"], xpath)
                else:
                    print(f"⚠️  Unknown blog source: {blog_source['name']}")
                    continue
                
                # Add language tag to each content item
                if blog_source.get("language"):
                    for item in content:
                        item["language"] = blog_source["language"]
                
                all_content.extend(content)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error processing {blog_source['name']}: {e}")
        
        return all_content
    
    def update_talks_json(self):
        """Update talks.json with fresh content from all sources"""
        print("\n🚀 Starting content fetch...")
        
        # Load existing data
        talks_data = self.load_talks_data()
        
        # Fetch new content
        fetched_content = self.fetch_all_content()
        
        # Update auto-fetched content
        talks_data["auto_fetched"] = fetched_content
        
        # Save updated data
        self.save_talks_data(talks_data)
        
        print(f"\n🎉 Content update complete!")
        print(f"   Manual items: {len(talks_data.get('manual_items', []))}")
        print(f"   Auto-fetched: {len(talks_data.get('auto_fetched', []))}")
        
        return talks_data
    
    def update_opensource_json(self):
        """Update opensource.json with fresh GitHub repository data"""
        print("\n🔄 Updating Open Source repositories...")
        
        # Fetch repositories from GitHub API
        repos = self.fetch_github_repositories()
        
        if repos:
            # Save to opensource.json
            opensource_path = os.path.join(self.data_path, "opensource.json")
            with open(opensource_path, 'w') as f:
                json.dump(repos, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated opensource.json with {len(repos)} repositories")
        else:
            print("❌ No repositories fetched, keeping existing file")
        
        return repos
    
    def update_sitemap_lastmod(self):
        """Update the lastmod field in sitemap.xml with current date"""
        print("\n🗺️  Updating sitemap.xml lastmod fields...")
        
        sitemap_path = os.path.join(self.base_path, "sitemap.xml")
        
        if not os.path.exists(sitemap_path):
            print("❌ sitemap.xml not found, skipping sitemap update")
            return
        
        try:
            # Parse the XML file
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            # Get current date in YYYY-MM-DD format
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Define namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Find all lastmod elements and update them
            updated_count = 0
            for lastmod in root.findall('.//ns:lastmod', namespace):
                old_date = lastmod.text
                lastmod.text = current_date
                updated_count += 1
                print(f"   📅 Updated {old_date} → {current_date}")
            
            # Write the updated XML back to file
            # Ensure proper XML declaration and formatting
            ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
            tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ Updated {updated_count} lastmod entries in sitemap.xml")
            
        except ET.ParseError as e:
            print(f"❌ Error parsing sitemap.xml: {e}")
        except Exception as e:
            print(f"❌ Error updating sitemap.xml: {e}")
    
    def update_all_content(self):
        """Update all content including talks and open source repositories"""
        print("\n🚀 Starting full content update...")
        
        # Update talks and articles
        talks_result = self.update_talks_json()
        
        # Update open source repositories  
        opensource_result = self.update_opensource_json()
        
        # Update sitemap with current date
        self.update_sitemap_lastmod()
        
        print(f"\n🎉 Full content update complete!")
        print(f"   Talks & Articles: {len(talks_result.get('auto_fetched', []))} items")
        print(f"   GitHub Repositories: {len(opensource_result)} repos")
        print(f"   Sitemap updated with current date")
        
        return {
            'talks': talks_result,
            'opensource': opensource_result
        }

def main():
    """Main function"""
    print("🌐 Personal Website Content Fetcher")
    print("=" * 40)
    
    # Determine base path
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        # Assume we're in scripts/ directory
        base_path = os.path.join(os.path.dirname(__file__), "..")
    
    fetcher = ContentFetcher(base_path)
    fetcher.update_all_content()

if __name__ == "__main__":
    main()
