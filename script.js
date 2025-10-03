// Theme management
class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme();
        
        // If no stored theme, use system preference and store it
        if (!this.currentTheme) {
            this.currentTheme = this.getSystemTheme();
            this.storeTheme(this.currentTheme); // Store the initial preference
        }
        
        this.init();
    }

    init() {
        this.applyTheme();
        // Delay button update to ensure DOM is ready
        setTimeout(() => this.updateToggleButton(), 0);
        this.bindEvents();
        this.updateAvatarImage();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    storeTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    applyTheme() {
        const html = document.documentElement;
        html.setAttribute('data-theme', this.currentTheme);
        this.updateAvatarImage();
    }

    updateAvatarImage() {
        const avatar = document.querySelector('.avatar');
        if (!avatar) return;

        const imageSrc = this.currentTheme === 'dark' ? 'almond_head_dark.png' : 'almond_head.png';
        
        if (avatar.src !== window.location.origin + '/' + imageSrc) {
            avatar.src = imageSrc;
        }
    }

    updateToggleButton() {
        const toggle = document.getElementById('theme-toggle');
        const icon = document.getElementById('theme-icon');
        const text = document.getElementById('theme-text');
        
        if (!toggle || !icon || !text) {
            setTimeout(() => this.updateToggleButton(), 100);
            return;
        }
        
        if (this.currentTheme === 'dark') {
            icon.className = 'fas fa-moon theme-toggle-icon';
            text.textContent = 'Dark';
        } else {
            icon.className = 'fas fa-sun theme-toggle-icon';
            text.textContent = 'Light';
        }
    }

    toggleTheme() {
        // Toggle between light and dark only
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.storeTheme(this.currentTheme);
        this.applyTheme();
        this.updateToggleButton();
    }

    bindEvents() {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggleTheme());
        }
    }
}

// Personal website with data-driven content
class PersonalWebsite {
    constructor() {
        // Configuration constants
        this.MAX_PUBLICATIONS_PREVIEW = 4; // Show first 4 publications by default
        this.MAX_TALKS_DISPLAY = 6; // Show first 10 talks/videos
        
        this.baseUrl = window.location.origin + window.location.pathname.replace('index.html', '');
        this.githubApiUrl = 'https://api.github.com/repos/';
        this.publicationsVisible = this.MAX_PUBLICATIONS_PREVIEW;
        this.content = null;
        this.themeManager = new ThemeManager();
        
        this.init();
    }

    async init() {
        try {
            // Load main content file first
            this.content = await this.loadContent();
            if (!this.content) {
                console.error('Failed to load main content file');
                return;
            }

            await Promise.all([
                this.loadPublications(),
                this.loadOpenSource(),
                this.loadCourse(),
                this.loadCSSP(),
                this.loadAwareness(),
                this.loadTalks()
            ]);
            console.log('Personal website loaded successfully');
        } catch (error) {
            console.error('Error loading website data:', error);
        }
    }

    async loadContent() {
        try {
            const response = await fetch(`${this.baseUrl}content.json`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error loading content.json:', error);
            return null;
        }
    }

    async loadJSON(path) {
        try {
            const response = await fetch(`${this.baseUrl}data/${path}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error loading ${path}:`, error);
            return null;
        }
    }

    async loadPublications() {
        const publications = this.content?.publications;
        if (!publications) return;

        const publicationsContainer = document.getElementById('publications-list');
        const showMoreBtn = document.getElementById('publications-show-more');

        // Show first few publications
        const visiblePublications = publications.slice(0, this.publicationsVisible);
        
        publicationsContainer.innerHTML = visiblePublications.map(pub => `
            <div class="publication">
                <div class="publication-title">
                    <a href="${pub.link}" class="publication-link" target="_blank" rel="noopener noreferrer">${pub.title}</a>
                </div>
                <div class="publication-journal">${pub.journal}, ${pub.year}</div>
                <div class="publication-description">${this.formatAuthors(pub.authors, pub.my_author_position)}</div>
            </div>
        `).join('');

        // Show "View all" button only if there are more publications than we display
        if (publications.length > this.MAX_PUBLICATIONS_PREVIEW) {
            showMoreBtn.style.display = 'block';
            showMoreBtn.innerHTML = 'View All Publications →';
            showMoreBtn.onclick = () => {
                window.location.href = 'publications.html';
            };
        } else {
            showMoreBtn.style.display = 'none';
        }
    }

    async loadOpenSource() {
        const allProjects = await this.loadJSON('opensource.json'); // Auto-generated from GitHub
        const showcase = this.content?.showcase_repositories;
        
        if (!allProjects || !showcase) return;

        const container = document.getElementById('open-source-carousel');
        
        console.log(`Loading showcased GitHub repositories`);
        
        // Create a map of all projects for easy lookup
        const projectMap = new Map();
        allProjects.forEach(project => {
            projectMap.set(project.name, project);
        });
        
        // Get showcase repositories in the specified order
        const showcaseProjects = showcase.selected
            .map(repoName => {
                const project = projectMap.get(repoName);
                if (project) {
                    // Use custom description if available
                    const customDesc = showcase.custom_descriptions?.[repoName];
                    if (customDesc) {
                        project.description = customDesc;
                    }
                    return project;
                }
                return null;
            })
            .filter(project => project !== null)
            .slice(0, showcase.max_display || 8);

        console.log(`Displaying ${showcaseProjects.length} curated repositories`);

        container.innerHTML = showcaseProjects.map(project => `
            <div class="repo-card">
                <h3><a href="${project.link}" class="publication-link" target="_blank" rel="noopener noreferrer">${project.name}</a></h3>
                <p>${project.description}</p>
                <div class="repo-stats">
                    <div class="repo-stat">
                        <i class="fas fa-star"></i>
                        <span>${project.stars}</span>
                    </div>
                    <div class="repo-stat">
                        <i class="fas fa-code-branch"></i>
                        <span>${project.forks}</span>
                    </div>
                </div>
                <div class="repo-language">${project.language}</div>
                ${project.is_fork ? '<div class="repo-fork-badge">Fork</div>' : ''}
            </div>
        `).join('') + `
            <a href="https://github.com/shakedzy" class="see-more-card" target="_blank" rel="noopener noreferrer">
                <span>See more on GitHub →</span>
            </a>
        `;
    }

    async getGitHubStats(repoPath) {
        try {
            const response = await fetch(`${this.githubApiUrl}${repoPath}`);
            if (!response.ok) {
                return { stars: 0, forks: 0 };
            }
            const data = await response.json();
            return {
                stars: data.stargazers_count || 0,
                forks: data.forks_count || 0
            };
        } catch (error) {
            console.error(`Error fetching GitHub stats for ${repoPath}:`, error);
            return { stars: 0, forks: 0 };
        }
    }

    async loadCourse() {
        const course = this.content?.online_course;
        if (!course) return;

        const container = document.getElementById('course-card');
        container.innerHTML = `
            <div class="course-logo">
                <img src="${course.logo_url}" alt="${course.platform} logo" onerror="this.style.display='none'">
            </div>
            <div class="course-content">
                <div class="course-title">${course.title}</div>
                <div class="course-provider">${course.platform}</div>
                <div class="course-description">${course.description}</div>
                <div class="course-highlights">
                    ${course.highlights.map(highlight => 
                        `<span class="course-highlight">${highlight}</span>`
                    ).join('')}
                </div>
                <a href="${course.link}" class="course-link" target="_blank" rel="noopener noreferrer">View Course →</a>
            </div>
        `;
    }

    async loadCSSP() {
        const csspProjects = this.content?.cssp;
        if (!csspProjects || !Array.isArray(csspProjects)) return;

        const container = document.getElementById('cssp-carousel');
        
        container.innerHTML = csspProjects.map(project => `
            <a href="${project.link}" class="cssp-card" target="_blank" rel="noopener noreferrer">
                <div class="cssp-icon">
                    <img src="${project.icon}" alt="${project.name} icon" class="cssp-favicon" onerror="this.style.display='none'">
                </div>
                <div class="cssp-content">
                    <div class="cssp-title">${project.name}</div>
                    <div class="cssp-description">${project.description}</div>
                </div>
            </a>
        `).join('');
    }

    async loadAwareness() {
        const awareness = this.content?.awareness;
        const section = document.querySelector('.awareness-raising');
        
        // Check if awareness object exists and has meaningful content
        const hasTitle = awareness?.title && awareness.title.trim();
        const hasContent = awareness?.content && awareness.content.trim();
        const hasLinks = awareness?.links && Array.isArray(awareness.links) && awareness.links.length > 0;
        
        // Hide section if no meaningful content
        if (!awareness || (!hasTitle && !hasContent && !hasLinks)) {
            if (section) {
                section.style.display = 'none';
            }
            return;
        }
        
        // Show section if it has content
        if (section) {
            section.style.display = 'block';
        }

        const container = document.getElementById('awareness-content');
        
        // Use the first link as the main link for the entire section
        const primaryLink = hasLinks ? awareness.links[0] : null;
        
        if (primaryLink) {
            container.innerHTML = `
                <a href="${primaryLink.url}" class="awareness-clickable" target="_blank" rel="noopener noreferrer">
                    <h2>${awareness.title || 'Awareness'}</h2>
                    <p>${awareness.content || ''}</p>
                </a>
            `;
        } else {
            container.innerHTML = `
                <h2>${awareness.title || 'Awareness'}</h2>
                <p>${awareness.content || ''}</p>
            `;
        }
    }

    async loadTalks() {
        const talksData = await this.loadJSON('talks.json'); // Auto-fetched content
        const manualTalks = this.content?.manual_talks || [];
        const manualPodcastGuests = this.content?.manual_podcast_guests || [];

        // Merge all talk sources
        const allTalks = [
            ...manualTalks,
            ...manualPodcastGuests,
            ...(talksData?.auto_fetched || [])
        ];

        // Sort chronologically (newest first)
        allTalks.sort((a, b) => new Date(b.date) - new Date(a.date));

        // Show only first N items
        const displayTalks = allTalks.slice(0, this.MAX_TALKS_DISPLAY);
        
        const container = document.getElementById('talks-carousel');
        // Debug: Log the talks being rendered
        console.log('Rendering talks:', displayTalks.length);
        displayTalks.forEach((talk, i) => {
            console.log(`${i+1}. ${talk.title} -> ${talk.link}`);
        });
        
        container.innerHTML = displayTalks.map(talk => `
            <a href="${talk.link}" class="talk-card" target="_blank" rel="noopener noreferrer" onclick="console.log('Click detected:', '${talk.link}'); return true;">
                <div class="talk-header">
                    <i class="${talk.icon} talk-icon"></i>
                    <span class="talk-platform">${talk.platform}</span>
                    ${talk.language ? `<span class="language-tag lang-${talk.language}">${talk.language}</span>` : ''}
                </div>
                <div class="talk-title">${talk.title}</div>
                <div class="talk-type">${talk.type}</div>
                ${talk.show_name ? `<div class="podcast-name">${talk.show_name}</div>` : ''}
                ${talk.description ? `<div class="talk-description">${talk.description}</div>` : ''}
                <div class="talk-meta">
                    <span>${this.formatDate(talk.date)}</span>
                    ${talk.claps && this.isSignificantClaps(talk.claps) ? `<span>${talk.claps} claps</span>` : (talk.views && talk.views !== 'N/A' && talk.type !== 'Podcast' ? `<span>${talk.views} views</span>` : '')}
                </div>
            </a>
        `).join('') + `
            <a href="blogs-talks-videos.html" class="see-more-card">
                <span>View all →</span>
            </a>
        `;
        
        console.log('HTML generated for talks carousel');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    formatAuthors(authors, myPosition) {
        if (!authors || !Array.isArray(authors)) return '';
        
        const authorList = authors.map((author, index) => {
            const position = index + 1; // Convert to 1-based index
            if (myPosition && position === myPosition) {
                return `<strong>${author}</strong>`;
            }
            return author;
        }).join(', ');
        return `<em>${authorList}</em>`;
    }
    
    isSignificantClaps(claps) {
        if (!claps) return false;
        
        // Handle string values like "1.1K", "500", etc.
        if (typeof claps === 'string') {
            // Remove any non-numeric characters except decimal points and K/M
            const cleanClaps = claps.replace(/[^\d.KM]/g, '');
            
            if (cleanClaps.includes('K')) {
                // Convert K to thousands (e.g., "1.1K" -> 1100)
                const num = parseFloat(cleanClaps.replace('K', '')) * 1000;
                return num >= 10;
            } else if (cleanClaps.includes('M')) {
                // Convert M to millions (e.g., "1.5M" -> 1500000)
                const num = parseFloat(cleanClaps.replace('M', '')) * 1000000;
                return num >= 10;
            } else {
                // Regular number
                const num = parseFloat(cleanClaps);
                return !isNaN(num) && num >= 10;
            }
        }
        
        // Handle numeric values
        return typeof claps === 'number' && claps >= 10;
    }
}

// Initialize the website when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PersonalWebsite();
});
