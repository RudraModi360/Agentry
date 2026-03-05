# Deploying Logicore Documentation to GitHub Pages

This guide explains how to deploy your Docsify documentation to GitHub Pages.

---

## Prerequisites

- GitHub repository
- Git installed locally
- Documentation files in `/docs` folder

---

## Step 1: Verify Files Are in Place

Your `/docs` folder should contain:

```
docs/
├── index.html              ✅ Docsify config (Provided)
├── _sidebar.md             ✅ Navigation structure (Provided)
├── README.md               ✅ Homepage (Provided)
├── .nojekyll               ✅ GitHub Pages bypass (Provided)
├── 01-birds-eye-view.md    ✅ Documentation
├── 02-quickstart.md        ✅ Documentation
├── 03-how-to-guides.md     ✅ Documentation
├── 04-core-architecture.md ✅ Documentation
└── 05-api-reference.md     ✅ Documentation
```

All files have been created for you. ✅

---

## Step 2: Push to GitHub

```bash
# Navigate to your repo
cd your-logicore-repo

# Add docs folder
git add docs/

# Commit
git commit -m "docs: add comprehensive Docsify documentation with sidebar navigation"

# Push
git push origin main
```

---

## Step 3: Enable GitHub Pages

### Option A: Automatic (Recommended)

1. Go to your GitHub repository
2. Click **Settings** → **Pages**
3. Under "Source", select:
   - **Branch**: `main`
   - **Folder**: `/docs`
4. Click **Save**

GitHub will automatically build and deploy your site.

### Option B: Custom Domain

If you have a custom domain:

1. Add a `CNAME` file to `/docs`:
```bash
echo "your-domain.com" > docs/CNAME
git add docs/CNAME
git commit -m "docs: add CNAME for custom domain"
git push
```

2. Follow Option A steps in Settings → Pages

---

## Step 4: View Your Documentation

After GitHub Pages deploys (takes ~1-2 minutes):

- **Default URL**: `https://yourusername.github.io/logicore`
- **Check status**: Go to Settings → Pages to see deployment status

---

## What You Get

Your deployed documentation will have:

### ✅ Sidebar Navigation
Like the image you showed:
```
📚 Overview

📖 Getting Started
  └ Bird's-Eye View
  └ Quickstart

🛠️ Guides
  └ How-To Guides

🏗️ Architecture & Reference
  └ Core Architecture
  └ API Reference

⚙️ Components
  └ Agents
  └ Memory
  └ Providers
  └ Tools
  └ Skills
  └ Sessions

⚙️ Configuration
  └ Settings
  └ Callbacks
  └ Exceptions
```

### ✅ Features
- 🔍 **Full-text search** (search for any class, method, parameter)
- 📋 **Table of contents** (auto-generated per page)
- 🎨 **Dark theme** (purple/violet accent color)
- 💻 **Code syntax highlighting** (Python, JSON, YAML, Bash)
- 📊 **Mermaid diagrams** (flowcharts, architecture)
- 📱 **Mobile responsive**
- 🔗 **Cross-file linking**

---

## Customization

### Change Theme Color

Edit `docs/index.html`, find this line:

```javascript
themeColor: "#673ab7",
```

Replace with any hex color:
```javascript
themeColor: "#2196F3",  // Blue
themeColor: "#FF5722",  // Orange
themeColor: "#4CAF50",  // Green
```

### Change Logo

Replace this line in `docs/index.html`:

```javascript
logo: "https://via.placeholder.com/40x40/673ab7/ffffff?text=LC",
```

With your image URL:
```javascript
logo: "https://your-domain.com/logo.png",
```

### Change Repository Link

```javascript
repo: "https://github.com/yourusername/logicore",
```

---

## Updating Documentation

To update docs:

1. Edit markdown files in `/docs`
2. Commit and push:
   ```bash
   git add docs/*.md
   git commit -m "docs: update API reference"
   git push
   ```
3. Changes auto-deploy (usually within 30 seconds)

---

## Troubleshooting

### Site not loading?

1. Check GitHub Pages is enabled: **Settings → Pages**
2. Verify files are in `/docs` folder
3. Ensure `.nojekyll` file exists
4. Check deployment status (green checkmark on Pages tab)

### Sidebar not showing?

Verify `_sidebar.md` exists in `/docs` folder.

### Search not working?

Search builds automatically. Give it 1-2 minutes after first deploy.

### Custom domain not working?

1. Verify `CNAME` file exists in `/docs`
2. Check DNS settings in your domain provider
3. Wait 24 hours for DNS propagation

---

## Advanced: Local Testing

Before deploying, test locally:

### With Python:
```bash
cd docs
python -m http.server 8080
```

Visit: `http://localhost:8080`

### With Node.js:
```bash
npm install -g http-server
cd docs
http-server
```

Visit: `http://localhost:8080`

---

## File Reference

| File | Purpose |
|------|---------|
| `index.html` | Docsify configuration & styling |
| `_sidebar.md` | Navigation panel structure |
| `README.md` | Homepage content |
| `.nojekyll` | Tells GitHub to skip Jekyll processing |
| `CNAME` | Custom domain (optional) |
| `*.md` | Documentation content |

---

## Next Steps

✅ **Documentation created**  
✅ **GitHub Pages configured**  
Now:

1. Push to GitHub
2. Enable Pages in Settings
3. Share your documentation!

---

**Questions?** Check [README.md](README.md) for links to full documentation.
