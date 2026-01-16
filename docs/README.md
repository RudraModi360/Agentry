# Documentation Build

This directory contains the Jekyll-based documentation for Agentry, configured for GitHub Pages deployment.

## Structure

```
docs/
├── _config.yml           # Jekyll configuration
├── index.md              # Home page
├── getting-started.md    # Installation and quick start
├── core-concepts.md      # Architecture and concepts
├── api-reference.md      # Complete API documentation
├── custom-tools.md       # Creating custom tools
├── mcp-integration.md    # MCP server integration
├── session-management.md # Session handling
├── examples.md           # Code examples
├── troubleshooting.md    # Common issues
├── CONTRIBUTING.md       # Contribution guidelines
├── DEPLOYMENT_GUIDE.md   # Production deployment
├── Gemfile               # Ruby dependencies
└── assets/
    └── images/           # Documentation images
```

## Local Development

### Prerequisites

- Ruby 3.0+
- Bundler

### Setup

```bash
cd docs
bundle install
```

### Run Locally

```bash
bundle exec jekyll serve
```

Open http://localhost:4000/Agentry/ in your browser.

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` or `Azure_Provider` branch.

### Manual Deployment

1. Go to repository Settings > Pages
2. Set Source to "GitHub Actions"
3. The workflow will run on push to main branch

### Live URL

https://rudramodi360.github.io/Agentry/

## Adding New Pages

1. Create a new `.md` file in the `docs/` directory
2. Add the Jekyll front matter:

```yaml
---
layout: page
title: Your Page Title
nav_order: 12
description: "Brief description of the page"
---
```

3. Write your content using Markdown
4. Commit and push to trigger deployment

## Style Guidelines

- Use tables for structured information
- Use code blocks with language hints
- Include images from `assets/images/` for complex concepts
- Avoid emojis in technical documentation
- Use proper headings hierarchy (h1, h2, h3)
