// File Type Icons - Properly Designed Based on Industry Standards
// All icons designed for 14x14px at 2px stroke width

const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const name = filename.toLowerCase();
    const base = 'width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"';

    const icons = {
        // === PROGRAMMING LANGUAGES ===

        // Python - Two circles (Python logo style)
        'py': `<svg viewBox="0 0 24 24" ${base}><circle cx="9" cy="8" r="3"></circle><circle cx="15" cy="16" r="3"></circle><path d="M9 11v5c0 2 1 3 3 3M15 13V8c0-2-1-3-3-3"></path></svg>`,

        // JavaScript - JS in square
        'js': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M7 14c0 2 1 3 2.5 3s2.5-1 2.5-2.5V9M13 14c0 2 1 3 2.5 3s2.5-1 2.5-3-1-2-2.5-2-2.5-.5-2.5-2 1-2 2.5-2"></path></svg>`,
        'jsx': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M7 14c0 2 1 3 2.5 3s2.5-1 2.5-2.5V9M13 14c0 2 1 3 2.5 3s2.5-1 2.5-3-1-2-2.5-2-2.5-.5-2.5-2 1-2 2.5-2"></path></svg>`,

        // TypeScript - TS in square  
        'ts': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M8 8h4M10 8v9M14 12h2c1.5 0 2 1 2 2.5S17.5 17 16 17h-2z"></path></svg>`,
        'tsx': `<svg viewBox="0 0 24 24" ${base}><rect x="2" y="2" width="20" height="20" rx="2"></rect><path d="M8 8h4M10 8v9M14 12h2c1.5 0 2 1 2 2.5S17.5 17 16 17h-2z"></path></svg>`,

        // HTML - Angle brackets <>
        'html': `<svg viewBox="0 0 24 24" ${base}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,
        'htm': `<svg viewBox="0 0 24 24" ${base}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,

        // CSS - Hash symbol #
        'css': `<svg viewBox="0 0 24 24" ${base}><path d="M9 3v18M15 3v18M4 9h16M4 15h16"></path></svg>`,
        'scss': `<svg viewBox="0 0 24 24" ${base}><path d="M9 3v18M15 3v18M4 9h16M4 15h16"></path></svg>`,
        'sass': `<svg viewBox="0 0 24 24" ${base}><path d="M9 3v18M15 3v18M4 9h16M4 15h16"></path></svg>`,

        // Java - Coffee cup
        'java': `<svg viewBox="0 0 24 24" ${base}><path d="M17 8h3a2 2 0 0 1 2 2c0 2-1 3-2 3h-3M6 8v8c0 2 2 4 5 4h2c3 0 5-2 5-4V8H6z"></path><path d="M8 5c0-1 1-2 2-2h4c1 0 2 1 2 2"></path></svg>`,

        // PHP - Elephant head
        'php': `<svg viewBox="0 0 24 24" ${base}><path d="M12 6c-4 0-8 2-8 6s4 6 8 6 8-2 8-6-4-6-8-6z"></path><circle cx="9" cy="11" r="1"></circle><path d="M16 10v4"></path></svg>`,

        // Ruby - Diamond gem
        'rb': `<svg viewBox="0 0 24 24" ${base}><path d="M6 9l6-6 6 6-6 12-6-12z"></path><path d="M6 9h12M12 3v18"></path></svg>`,

        // Go - Gopher
        'go': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="8"></circle><circle cx="9" cy="10" r="1"></circle><circle cx="15" cy="10" r="1"></circle><path d="M8 14c1 2 3 3 4 3s3-1 4-3"></path></svg>`,

        // Rust - Gear
        'rs': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="3"></circle><path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"></path></svg>`,

        // C/C++ - Blocky C
        'c': `<svg viewBox="0 0 24 24" ${base}><path d="M18 8c-2-2-4-2-6-2s-4 0-6 2-2 4-2 6 0 4 2 6 4 2 6 2 4 0 6-2"></path></svg>`,
        'cpp': `<svg viewBox="0 0 24 24" ${base}><path d="M16 8c-1.5-1.5-3-2-5-2s-3.5.5-5 2S4 12 4 14s.5 3.5 2 5 3 2 5 2 3.5-.5 5-2"></path><path d="M16 10v4M18 12h-4M20 10v4M22 12h-4"></path></svg>`,
        'h': `<svg viewBox="0 0 24 24" ${base}><path d="M18 8c-2-2-4-2-6-2s-4 0-6 2-2 4-2 6 0 4 2 6 4 2 6 2 4 0 6-2"></path></svg>`,
        'hpp': `<svg viewBox="0 0 24 24" ${base}><path d="M16 8c-1.5-1.5-3-2-5-2s-3.5.5-5 2S4 12 4 14s.5 3.5 2 5 3 2 5 2 3.5-.5 5-2"></path><path d="M16 10v4M18 12h-4M20 10v4M22 12h-4"></path></svg>`,

        // C# - C with #
        'cs': `<svg viewBox="0 0 24 24" ${base}><path d="M11 8c-2-2-4-2-6-2s-2 0-2 2 0 4 0 6 0 4 2 6 4 2 6 2 4 0 6-2"></path><path d="M15 9v6M18 9v6M13 11h7M13 14h7"></path></svg>`,

        // === MARKUP & DATA ===

        // JSON - Curly braces
        'json': `<svg viewBox="0 0 24 24" ${base}><path d="M6 4h3a2 2 0 0 1 2 2v3a2 2 0 0 0 2 2 2 2 0 0 0-2 2v3a2 2 0 0 1-2 2H6M18 4h-3a2 2 0 0 0-2 2v3a2 2 0 0 1-2 2 2 2 0 0 1 2 2v3a2 2 0 0 0 2 2h3"></path></svg>`,

        // XML - Angle brackets with slash
        'xml': `<svg viewBox="0 0 24 24" ${base}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline><line x1="13" y1="6" x2="11" y2="18"></line></svg>`,

        // YAML - Three lines with bullets
        'yaml': `<svg viewBox="0 0 24 24" ${base}><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><circle cx="4" cy="6" r="1.5"></circle><circle cx="4" cy="12" r="1.5"></circle><circle cx="4" cy="18" r="1.5"></circle></svg>`,
        'yml': `<svg viewBox="0 0 24 24" ${base}><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><circle cx="4" cy="6" r="1.5"></circle><circle cx="4" cy="12" r="1.5"></circle><circle cx="4" cy="18" r="1.5"></circle></svg>`,

        // TOML - Square brackets
        'toml': `<svg viewBox="0 0 24 24" ${base}><path d="M8 6v12M16 6v12M6 6h4M6 18h4M14 6h4M14 18h4"></path></svg>`,

        // Markdown - M with #
        'md': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 13l1.5 2 1.5-2M10.5 15v-3"></path></svg>`,
        'markdown': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 13l1.5 2 1.5-2M10.5 15v-3"></path></svg>`,

        // === CONFIGURATION ===

        // ENV - Key
        'env': `<svg viewBox="0 0 24 24" ${base}><circle cx="8" cy="8" r="4"></circle><path d="M12 8h8M16 6v4M20 6v4"></path></svg>`,

        // INI - List with equals
        'ini': `<svg viewBox="0 0 24 24" ${base}><line x1="4" y1="7" x2="10" y2="7"></line><line x1="14" y1="7" x2="20" y2="7"></line><line x1="12" y1="7" x2="12" y2="7.01"></line><line x1="4" y1="12" x2="10" y2="12"></line><line x1="14" y1="12" x2="20" y2="12"></line><line x1="12" y1="12" x2="12" y2="12.01"></line><line x1="4" y1="17" x2="10" y2="17"></line><line x1="14" y1="17" x2="20" y2="17"></line><line x1="12" y1="17" x2="12" y2="17.01"></line></svg>`,

        // Docker - Container boxes
        'dockerfile': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="8" width="18" height="11" rx="1"></rect><path d="M7 8V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2M7 12h2M11 12h2M15 12h2M7 15h2M11 15h2M15 15h2"></path></svg>`,

        // Git - Branch
        'gitignore': `<svg viewBox="0 0 24 24" ${base}><circle cx="6" cy="6" r="3"></circle><circle cx="18" cy="18" r="3"></circle><circle cx="18" cy="6" r="3"></circle><path d="M18 9v6M6 9c0 6 6 6 12 6"></path></svg>`,
        'gitattributes': `<svg viewBox="0 0 24 24" ${base}><circle cx="6" cy="6" r="3"></circle><circle cx="18" cy="18" r="3"></circle><circle cx="18" cy="6" r="3"></circle><path d="M18 9v6M6 9c0 6 6 6 12 6"></path></svg>`,

        // === DATABASES ===

        // SQL - Database cylinder
        'sql': `<svg viewBox="0 0 24 24" ${base}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path></svg>`,
        'db': `<svg viewBox="0 0 24 24" ${base}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path></svg>`,
        'sqlite': `<svg viewBox="0 0 24 24" ${base}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path></svg>`,

        // === MEDIA ===

        // Images - Picture frame
        'png': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'jpg': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'jpeg': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'gif': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'svg': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'webp': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,
        'ico': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`,

        // === DOCUMENTS ===

        // Text - Document with lines
        'txt': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>`,
        'log': `<svg viewBox="0 0 24 24" ${base}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>`,

        // Excel/Spreadsheet - Grid
        'xlsx': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,
        'xls': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,
        'csv': `<svg viewBox="0 0 24 24" ${base}><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,

        // === SHELL SCRIPTS ===

        // Bash - Terminal prompt
        'sh': `<svg viewBox="0 0 24 24" ${base}><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>`,
        'bash': `<svg viewBox="0 0 24 24" ${base}><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>`,

        // PowerShell
        'ps1': `<svg viewBox="0 0 24 24" ${base}><polyline points="4 17 10 11 4 5"></polyline><polyline points="13 17 20 17"></polyline></svg>`,

        // === SPECIAL FILES ===

        // License - Balance scales
        'license': `<svg viewBox="0 0 24 24" ${base}><path d="M12 3v18"></path><path d="M5 9h6M13 9h6M5 9v3c0 3 3 3 3 3s3 0 3-3V9M13 9v3c0 3 3 3 3 3s3 0 3-3V9M5 21h14"></path></svg>`,

        // README - Info
        'readme': `<svg viewBox="0 0 24 24" ${base}><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,

        // Lock - Padlock
        'lock': `<svg viewBox="0 0 24 24" ${base}><rect x="5" y="11" width="14" height="10" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`,

        // Default - Generic file
        'default': `<svg viewBox="0 0 24 24" ${base}><path d="M13 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>`
    };

    // Check extension first, then full filename (for Dockerfile, LICENSE, etc.)
    return icons[ext] || icons[name] || icons.default;
};

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getFileIcon };
}
