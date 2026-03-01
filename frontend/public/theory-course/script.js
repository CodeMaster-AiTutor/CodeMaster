function toggleLevel(element) {
    const level = element.closest('.level');
    if (level && level.classList.contains('locked')) {
        return;
    }
    const topics = element.nextElementSibling;
    const isVisible = topics.style.display === "block";
    topics.style.display = isVisible ? "none" : "block";
}

const getUserLevel = () => {
    try {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            const level = (user.skill_level || 'beginner').toLowerCase();
            if (level === 'intermediate' || level === 'advanced' || level === 'beginner') {
                return level;
            }
        }
    } catch {
        return 'beginner';
    }
    return 'beginner';
};

const applyTheme = (theme) => {
    document.body.classList.toggle('theme-dark', theme === 'dark');
    document.body.classList.toggle('theme-light', theme === 'light');
};

const setupThemeToggle = () => {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) {
        return;
    }
    const controls = document.createElement('div');
    controls.className = 'course-controls';
    const label = document.createElement('div');
    label.textContent = 'Course Theme';
    label.style.fontSize = '12px';
    label.style.fontWeight = '600';
    label.style.color = 'inherit';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'theme-toggle';
    const themeKey = 'theory-course-theme';
    const storedTheme = localStorage.getItem(themeKey) || 'light';
    applyTheme(storedTheme);
    button.textContent = storedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
    button.addEventListener('click', () => {
        const nextTheme = document.body.classList.contains('theme-dark') ? 'light' : 'dark';
        localStorage.setItem(themeKey, nextTheme);
        applyTheme(nextTheme);
        button.textContent = nextTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
    });
    controls.appendChild(label);
    controls.appendChild(button);
    sidebar.prepend(controls);
};

const getLevelKeyFromTitle = (titleText) => {
    const text = titleText.toLowerCase();
    if (text.includes('beginner')) return 'beginner';
    if (text.includes('intermediate')) return 'intermediate';
    if (text.includes('advanced')) return 'advanced';
    return 'beginner';
};

const applyLocks = () => {
    const userLevel = getUserLevel();
    const rank = userLevel === 'advanced' ? 2 : userLevel === 'intermediate' ? 1 : 0;
    const levels = document.querySelectorAll('.level');
    levels.forEach((level) => {
        const titleEl = level.querySelector('.level-title');
        const topics = level.querySelector('.level-topics');
        if (!titleEl) {
            return;
        }
        const levelKey = getLevelKeyFromTitle(titleEl.textContent || '');
        const levelRank = levelKey === 'advanced' ? 2 : levelKey === 'intermediate' ? 1 : 0;
        const locked = levelRank > rank;
        if (locked) {
            level.classList.add('locked');
            if (topics) {
                topics.style.display = 'none';
            }
            if (!titleEl.querySelector('.level-lock')) {
                const lockSpan = document.createElement('span');
                lockSpan.className = 'level-lock';
                lockSpan.textContent = '🔒';
                titleEl.appendChild(lockSpan);
            }
            level.querySelectorAll('a').forEach((link) => {
                link.classList.add('locked');
                link.setAttribute('aria-disabled', 'true');
            });
        } else {
            level.classList.remove('locked');
            const lockSpan = titleEl.querySelector('.level-lock');
            if (lockSpan) {
                lockSpan.remove();
            }
            level.querySelectorAll('a').forEach((link) => {
                link.classList.remove('locked');
                link.removeAttribute('aria-disabled');
            });
        }
    });
};

const setupSubtopicToggles = () => {
    document.querySelectorAll('.page-subtopics').forEach((subtopics) => {
        const topicLink = subtopics.previousElementSibling;
        if (!topicLink || !topicLink.classList.contains('topic-link')) {
            return;
        }
        topicLink.classList.add('has-subtopics');
        if (!topicLink.hasAttribute('data-subtopics-toggle')) {
            topicLink.setAttribute('data-subtopics-toggle', 'true');
            topicLink.setAttribute('aria-expanded', 'true');
            topicLink.addEventListener('click', (event) => {
                if (topicLink.classList.contains('locked')) {
                    event.preventDefault();
                    return;
                }
                event.preventDefault();
                const isOpen = subtopics.style.display !== 'none';
                subtopics.style.display = isOpen ? 'none' : 'block';
                topicLink.setAttribute('aria-expanded', String(!isOpen));
                topicLink.classList.toggle('collapsed', isOpen);
            });
        }
    });
};

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.querySelector('.menu-btn');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);

    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        });
    }

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });

    setupThemeToggle();
    setupSubtopicToggles();
    applyLocks();
});
