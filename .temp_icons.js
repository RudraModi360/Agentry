// Helper: Get file icon based on extension
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const base = 'width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"';

    const icons = {
        // Python - Two circles representing Python logo
        'py': `<svg viewBox="0 0 24 24" ${base}><circle cx="9" cy="8" r="3"></circle><circle cx="15" cy="16" r="3"></circle><path d="M9 11v5c0 2 1 3 3 3M15 13V8c0-2-1-3-3-3"></path></svg>`,

        // JavaScript - Distinctive JS 
        'js': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M8 15c0 1.5 1 2 2 2s2-.5 2-2V9M14 15c0 1.5 1 2 2 2s2-.5 2-2 0-2-2-2-2-.5-2-2 1-2 2-2"></path></svg>`,
        'jsx': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M8 15c0 1.5 1 2 2 2s2-.5 2-2V9M14 15c0 1.5 1 2 2 2s2-.5 2-2 0-2-2-2-2-.5-2-2 1-2 2-2"></path></svg>`,

        // TypeScript - TS with distinctive style
        'ts': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M8 9h4M10 9v6M14 12h2c1 0 2 .5 2 1.5s-1 1.5-2 1.5h-2V12z"></path></svg>`,
        'tsx': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M8 9h4M10 9v6M14 12h2c1 0 2 .5 2 1.5s-1 1.5-2 1.5h-2V12z"></path></svg>`,

        // HTML - Clear angle brackets
        'html': `<svg viewBox="0 0 24 24" ${base}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,
        'htm': `<svg viewBox="0 0 24 24" ${base}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,

        // CSS - Paint/style brush
        'css': `<svg viewBox="0 0 24 24" ${base}><path d="M12 2l9.5 5.5v11L12 24l-9.5-6.5v-11L12 2z"></path><path d="M12 8v8M8 12h8"></path></svg>`,
        'scss': `<svg viewBox="0 0 24 24" ${base}><path d="M12 2l9.5 5.5v11L12 24l-9.5-6.5v-11L12 2z"></path><path d="M12 8v8M8 12h8"></path></svg>`,

        // JSON - Curly braces
        'json': `<svg viewBox="0 0 24 24" ${base}><path d="M6 4h3a2 2 0 0 1 2 2v3a2 2 0 0 0 2 2 2 2 0 0 0-2 2v3a2 2 0 0 1-2 2H6"></path><path d="M18 4h-3a2 2 0 0 0-2 2v3a2 2 0 0 1-2 2 2 2 0 0 1 2 2v3a2 2 0 0 0 2 2h3"></path></svg>`,

        // Markdown - M with document
        'md': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z"></path><path d="M14 2v6h6M8 13l2 2 2-2M10 15v-4"></path></svg>`,
        'markdown': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z"></path><path d="M14 2v6h6M8 13l2 2 2-2M10 15v-4"></path></svg>`,

        // Docker - Container/box
        'dockerfile': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="8" width="18" height="12" rx="1"></rect><path d="M7 8V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2M7 12h2M11 12h2M15 12h2M7 16h2M11 16h2M15 16h2"></path></svg>`,

        // Config files - Gear/cog
        'yaml': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="3"></circle><path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"></path></svg>`,
        'yml': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="3"></circle><path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"></path></svg>`,
        'toml': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="3"></circle><path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"></path></svg>`,
        'ini': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="3"></circle><path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"></path></svg>`,
        'env': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="3"></circle><path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"></path></svg>`,

        // Database - Cylinder
        'sql': `<svg viewBox="0 0 24 24" ${base}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path></svg>`,
        'db': `<svg viewBox="0 0 24 24" ${base}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path></svg>`,

        // Images - Picture frame
        'png': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'jpg': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'jpeg': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'gif': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'svg': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'webp': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,

        // Spreadsheet - Table grid
        'xlsx': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,
        'xls': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,
        'csv': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,

        // Text - Document with lines
        'txt': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z"></path><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"></path></svg>`,
        'log': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z"></path><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"></path></svg>`,
    };

    // Return specific icon or default file icon
    return icons[ext] || icons[filename.toLowerCase()] || `<svg viewBox="0 0 24 24" ${base}><path d="M13 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V9l-6-6z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>`;
}
