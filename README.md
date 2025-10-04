# Personal Website

A modern, clean, and professional personal website with data-driven content management.

## 🎯 **WHAT YOU NEED TO UPDATE**

### **📝 ONE FILE TO EDIT:** `content.json`

This is the ONLY file you need to edit to update your website content. Everything else is automated.

```json
{
  "personal": {
    "name": "Your Name",
    "title": "Your Professional Title", 
    "bio": "Your bio description",
    "github_username": "yourusername",
    "medium_username": "yourusername",
    "youtube_channel": "yourusername"
  },

  "publications": [
    {
      "title": "Paper Title",
      "journal": "Journal Name", 
      "year": "2023",
      "link": "https://your-paper-url.com",
      "description": "Paper description"
    }
  ],

  "online_course": {
    "title": "Course Title",
    "platform": "Platform Name",
    "students": "10,000+",
    "rating": "4.9/5", 
    "description": "Course description",
    "link": "https://course-url.com",
    "logo_url": "https://logo-url.com/logo.png",
    "highlights": ["Feature 1", "Feature 2", "Feature 3"]
  },

  "showcase_repositories": {
    "selected": ["repo1", "repo2", "repo3"],
    "custom_descriptions": {
      "repo1": "Custom description for this repo"
    },
    "max_display": 7
  },

  "manual_talks": [
    {
      "title": "Talk Title", 
      "platform": "Event Name",
      "type": "Conference Talk",
      "date": "2024-03-15",
      "link": "https://youtube.com/watch?v=...",
      "description": "Talk description",
      "views": "2.5K",
      "icon": "fas fa-microphone-alt"
    }
  ]
}
```

## 🚀 **HOW TO UPDATE YOUR WEBSITE**

### **1. Edit Content**
```bash
# Edit the main content file
nano content.json
```

### **2. Update Auto-Fetched Content** (Optional)
```bash
# Fetch latest content from GitHub, Medium, YouTube, etc.
cd scripts
python3 content-fetcher.py ..
```

### **3. Test Locally**
```bash
# Start local server
python3 -m http.server 3000

# Visit: http://localhost:3000
```

## 📁 **FILE STRUCTURE**

### **Files You Edit:**
- ✅ `content.json` - **MAIN CONTENT FILE** (edit this!)

### **Files That Auto-Update:**
- 🤖 `data/opensource.json` - GitHub repositories (auto-generated)
- 🤖 `data/talks.json` - Articles and videos (auto-generated)

### **System Files (Don't Edit):**
- ❌ `index.html`, `script.js`, `styles.css` - Website code  
- ❌ `scripts/content-fetcher.py` - Content fetching logic
- ❌ `.github/workflows/` - Auto-update system

## 🔧 **COMMON TASKS**

### **Add/Remove Publications**  
Edit `content.json` → `publications` array

### **Change GitHub Repositories Shown**
Edit `content.json` → `showcase_repositories.selected` array
Available repos: Check `data/opensource.json` after running fetcher

### **Add Manual Talks/Videos**
Edit `content.json` → `manual_talks` array

### **Update Course Information**
Edit `content.json` → `online_course` object

## 🔑 **SETUP REQUIREMENTS**

### **GitHub Token** (for repository data)
1. Go to https://github.com/settings/tokens  
2. Create "Personal access token (classic)"
3. Select scope: `public_repo`
4. Add to `~/.zshrc`: `export GH_TOKEN="your_token_here"`
5. Run: `source ~/.zshrc`

### **YouTube API Key** (for video data)  
1. Go to https://console.cloud.google.com/apis/credentials
2. Create API Key  
3. Enable YouTube Data API v3
4. Add to `~/.zshrc`: `export YOUTUBE_API_KEY="your_key_here"`
5. Run: `source ~/.zshrc`

## 🤖 **AUTO-UPDATE SYSTEM**

The website automatically updates daily via GitHub Actions:
- ✅ Fetches new GitHub repository stats
- ✅ Pulls latest Medium articles
- ✅ Gets new YouTube videos
- ✅ Scrapes blog posts

**Manual update:** `cd scripts && python3 content-fetcher.py ..`

## 🎨 **CUSTOMIZATION GUIDE**

### **Repository Showcase**
In `content.json`:
```json
"showcase_repositories": {
  "selected": ["dython", "companion", "notebooks"],
  "custom_descriptions": {
    "dython": "Your custom description here"
  },
  "max_display": 7
}
```

### **Talk Icons**
Use Font Awesome icons:
- `fas fa-microphone-alt` - Conference talk
- `fab fa-youtube` - YouTube video  
- `fab fa-medium` - Medium article
- `fas fa-podcast` - Podcast

## 📊 **SECTIONS OVERVIEW**

1. **Publications** - Academic papers and articles  
2. **Open Source** - GitHub repositories (auto-updated)
3. **Online Course** - Course you teach/created
4. **Talks & Videos** - Speaking engagements and content

## 🐛 **TROUBLESHOOTING**

### **Data not showing?**
- Make sure you're accessing via `http://localhost:3000` (not `file://`)
- Check browser console for errors
- Verify `content.json` syntax is valid JSON

### **GitHub repos not updating?**
- Check `GH_TOKEN` is set: `echo $GH_TOKEN`
- Verify token has `public_repo` scope
- Run fetcher manually: `cd scripts && python3 content-fetcher.py ..`

### **YouTube videos not showing?**
- Check `YOUTUBE_API_KEY` is set: `echo $YOUTUBE_API_KEY`  
- Ensure YouTube Data API v3 is enabled
- Verify playlist names in your YouTube channel

## 🚀 **DEPLOYMENT**

This website is designed for **GitHub Pages**:

1. Push to GitHub repository
2. Enable GitHub Pages in repository settings  
3. Choose source: GitHub Actions
4. Website will be available at: `https://yourusername.github.io/repository-name`

The auto-update system will keep your content fresh automatically!

---

**Need help?** Check the browser console for error messages or verify your `content.json` syntax.