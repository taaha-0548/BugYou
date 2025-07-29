// User Profile JavaScript - BugYou

class UserProfile {
    constructor() {
        // Prevent multiple instances
        if (window.userProfileInstance) {
            return window.userProfileInstance;
        }
        
        this.currentUser = null;
        this.profileData = null;
        this.initialized = false;
        this.init();
        
        // Store instance globally
        window.userProfileInstance = this;
    }

    async init() {
        // Prevent multiple initializations
        if (this.initialized) {
            console.log('Profile already initialized');
            return;
        }
        
        try {
            // Check if user is logged in
            this.currentUser = localStorage.getItem('currentUser');
            if (!this.currentUser) {
                window.location.href = '/login';
                return;
            }

            // Set up event listeners
            this.setupEventListeners();
            
            // Load profile data
            await this.loadProfileData();
            
            // Update UI
            this.updateUI();
            
            this.initialized = true;
            console.log('Profile initialized successfully');
            
        } catch (error) {
            console.error('Error initializing profile:', error);
            this.showError('Failed to load profile data');
        }
    }

    setupEventListeners() {
        // Logo click - go to home
        const homeLogo = document.getElementById('homeLogo');
        if (homeLogo) {
            homeLogo.addEventListener('click', () => {
                window.location.href = '/';
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }

    async loadProfileData() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/user/${this.currentUser}/profile`);
            const data = await response.json();
            
            if (data.success) {
                this.profileData = data.profile;
                console.log('Profile data loaded:', this.profileData);
            } else {
                throw new Error(data.error || 'Failed to load profile');
            }
            
        } catch (error) {
            console.error('Error loading profile:', error);
            throw error;
        } finally {
            this.showLoading(false);
        }
    }

    updateUI() {
        if (!this.profileData) return;

        console.log('Updating UI...');

        // Update header
        this.updateHeader();
        
        // Update profile stats
        this.updateProfileStats();
        
        // Update XP progress
        this.updateXPProgress();
        
        // Update language statistics
        this.updateLanguageStats();
        
        // Update recent activity
        this.updateRecentActivity();
        
        // Update achievements
        this.updateAchievements();
        
        console.log('UI update completed');
    }

    updateHeader() {
        const usernameElement = document.getElementById('currentUsername');
        const profileNameElement = document.getElementById('profileName');
        
        if (usernameElement) {
            usernameElement.textContent = this.currentUser;
        }
        
        if (profileNameElement) {
            profileNameElement.textContent = this.currentUser;
        }
    }

    updateProfileStats() {
        const levelElement = document.getElementById('userLevel');
        const xpElement = document.getElementById('userXP');
        const totalSolvedElement = document.getElementById('totalSolved');
        
        if (levelElement) {
            levelElement.textContent = this.profileData.level || 1;
        }
        
        if (xpElement) {
            xpElement.textContent = this.profileData.xp || 0;
        }
        
        if (totalSolvedElement) {
            totalSolvedElement.textContent = this.profileData.total_solved || 0;
        }
    }

    updateXPProgress() {
        const xpProgressFill = document.getElementById('xpProgressFill');
        const xpProgressText = document.getElementById('xpProgressText');
        
        if (!xpProgressFill || !xpProgressText) return;
        
        const currentXP = this.profileData.xp || 0;
        const currentLevel = this.profileData.level || 1;
        
        // Calculate XP needed for current level (simple formula)
        const xpForCurrentLevel = (currentLevel - 1) * 100;
        const xpForNextLevel = currentLevel * 100;
        const xpInCurrentLevel = currentXP - xpForCurrentLevel;
        const xpNeededForNextLevel = xpForNextLevel - xpForCurrentLevel;
        
        // Calculate progress percentage
        const progressPercentage = Math.min((xpInCurrentLevel / xpNeededForNextLevel) * 100, 100);
        
        // Update progress bar
        xpProgressFill.style.width = `${progressPercentage}%`;
        
        // Update progress text
        xpProgressText.textContent = `${xpInCurrentLevel}/${xpNeededForNextLevel} XP to next level`;
    }

    updateLanguageStats() {
        const languageGrid = document.getElementById('languageGrid');
        if (!languageGrid) return;
        
        const languageStats = this.profileData.language_stats || {};
        
        // Clear existing content
        languageGrid.innerHTML = '';
        
        // Language icons mapping
        const languageIcons = {
            'python': 'fab fa-python',
            'javascript': 'fab fa-js-square',
            'java': 'fab fa-java',
            'cpp': 'fas fa-code'
        };
        
        // Create language cards
        Object.entries(languageStats).forEach(([language, stats]) => {
            const card = this.createLanguageCard(language, stats, languageIcons[language] || 'fas fa-code');
            languageGrid.appendChild(card);
        });
        
        // If no languages, show empty state
        if (Object.keys(languageStats).length === 0) {
            const emptyCard = this.createEmptyLanguageCard();
            languageGrid.appendChild(emptyCard);
        }
    }

    createLanguageCard(language, stats, iconClass) {
        const card = document.createElement('div');
        card.className = 'language-card';
        
        const total = stats.total || 0;
        const basic = stats.basic || 0;
        const intermediate = stats.intermediate || 0;
        const advanced = stats.advanced || 0;
        
        card.innerHTML = `
            <div class="language-header">
                <i class="${iconClass} language-icon"></i>
                <span class="language-name">${this.capitalizeFirst(language)}</span>
            </div>
            <div class="language-stats-grid">
                <div class="language-stat">
                    <div class="language-stat-value">${total}</div>
                    <div class="language-stat-label">Total</div>
                </div>
                <div class="language-stat">
                    <div class="language-stat-value">${basic}</div>
                    <div class="language-stat-label">Basic</div>
                </div>
                <div class="language-stat">
                    <div class="language-stat-value">${intermediate}</div>
                    <div class="language-stat-label">Intermediate</div>
                </div>
                <div class="language-stat">
                    <div class="language-stat-value">${advanced}</div>
                    <div class="language-stat-label">Advanced</div>
                </div>
            </div>
        `;
        
        return card;
    }

    createEmptyLanguageCard() {
        const card = document.createElement('div');
        card.className = 'language-card';
        card.innerHTML = `
            <div class="language-header">
                <i class="fas fa-code language-icon"></i>
                <span class="language-name">No Languages Yet</span>
            </div>
            <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                <i class="fas fa-code" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>Start solving challenges to see your language progress here!</p>
            </div>
        `;
        return card;
    }

    updateRecentActivity() {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;
        
        const recentSolved = this.profileData.recent_solved || [];
        
        // Clear existing content
        activityList.innerHTML = '';
        
        if (recentSolved.length === 0) {
            const emptyActivity = document.createElement('div');
            emptyActivity.className = 'activity-item';
            emptyActivity.innerHTML = `
                <i class="fas fa-clock activity-icon"></i>
                <div class="activity-content">
                    <div class="activity-title">No Recent Activity</div>
                    <div class="activity-meta">Start solving challenges to see your recent activity here!</div>
                </div>
            `;
            activityList.appendChild(emptyActivity);
            return;
        }
        
        // Create activity items (show last 5)
        recentSolved.slice(-5).reverse().forEach(problem => {
            const activityItem = this.createActivityItem(problem);
            activityList.appendChild(activityItem);
        });
    }

    createActivityItem(problem) {
        const item = document.createElement('div');
        item.className = 'activity-item';
        
        const solvedDate = new Date(problem.solved_at);
        const timeAgo = this.getTimeAgo(solvedDate);
        const timeTaken = problem.time_taken || 0;
        const timeTakenFormatted = this.formatTime(timeTaken);
        
        item.innerHTML = `
            <i class="fas fa-check-circle activity-icon"></i>
            <div class="activity-content">
                <div class="activity-title">${problem.title || `Challenge ${problem.challenge_id}`}</div>
                <div class="activity-meta">
                    <span class="activity-difficulty ${problem.difficulty}">${problem.difficulty}</span>
                    <span>${this.capitalizeFirst(problem.language)}</span>
                    <span>${timeAgo}</span>
                    <span class="time-taken">⏱️ ${timeTakenFormatted}</span>
                </div>
            </div>
        `;
        
        return item;
    }

    updateAchievements() {
        const badgesGrid = document.getElementById('badgesGrid');
        if (!badgesGrid) return;
        
        // Clear existing content to prevent duplication
        badgesGrid.innerHTML = '';
        
        // Define achievements
        const achievements = this.getAchievements();
        
        // Add each achievement badge
        achievements.forEach(achievement => {
            const badge = this.createAchievementBadge(achievement);
            badgesGrid.appendChild(badge);
        });
        
        console.log(`Updated ${achievements.length} achievements`);
    }

    getAchievements() {
        const totalSolved = this.profileData.total_solved || 0;
        const languageStats = this.profileData.language_stats || {};
        
        return [
            {
                id: 'first_solve',
                title: 'First Bug Squashed',
                description: 'Complete your first debugging challenge',
                icon: 'fas fa-bug',
                unlocked: totalSolved >= 1,
                condition: 'Solve 1 challenge'
            },
            {
                id: 'python_master',
                title: 'Python Master',
                description: 'Master Python debugging challenges',
                icon: 'fab fa-python',
                unlocked: (languageStats.python?.total || 0) >= 5,
                condition: 'Solve 5 Python challenges'
            },
            {
                id: 'javascript_master',
                title: 'JavaScript Master',
                description: 'Master JavaScript debugging challenges',
                icon: 'fab fa-js-square',
                unlocked: (languageStats.javascript?.total || 0) >= 5,
                condition: 'Solve 5 JavaScript challenges'
            },
            {
                id: 'java_master',
                title: 'Java Master',
                description: 'Master Java debugging challenges',
                icon: 'fab fa-java',
                unlocked: (languageStats.java?.total || 0) >= 5,
                condition: 'Solve 5 Java challenges'
            },
            {
                id: 'cpp_master',
                title: 'C++ Master',
                description: 'Master C++ debugging challenges',
                icon: 'fas fa-code',
                unlocked: (languageStats.cpp?.total || 0) >= 5,
                condition: 'Solve 5 C++ challenges'
            },
            {
                id: 'advanced_solver',
                title: 'Advanced Solver',
                description: 'Tackle complex debugging challenges',
                icon: 'fas fa-crown',
                unlocked: this.countAdvancedSolved() >= 3,
                condition: 'Solve 3 advanced challenges'
            },
            {
                id: 'level_5',
                title: 'Level 5 Achiever',
                description: 'Reach intermediate debugging skills',
                icon: 'fas fa-star',
                unlocked: (this.profileData.level || 1) >= 5,
                condition: 'Reach level 5'
            },
            {
                id: 'level_10',
                title: 'Level 10 Master',
                description: 'Become a debugging expert',
                icon: 'fas fa-star',
                unlocked: (this.profileData.level || 1) >= 10,
                condition: 'Reach level 10'
            }
        ];
    }

    countAdvancedSolved() {
        const languageStats = this.profileData.language_stats || {};
        let totalAdvanced = 0;
        
        Object.values(languageStats).forEach(stats => {
            totalAdvanced += stats.advanced || 0;
        });
        
        return totalAdvanced;
    }

    createAchievementBadge(achievement) {
        const badge = document.createElement('div');
        badge.className = `badge ${achievement.unlocked ? 'unlocked' : 'locked'}`;
        
        // Create badge content without descriptions
        const badgeContent = `
            <i class="${achievement.icon} badge-icon"></i>
            <div class="badge-title">${achievement.title}</div>
        `;
        
        // Only add condition for locked badges
        const conditionContent = !achievement.unlocked ? `<div class="badge-condition">${achievement.condition}</div>` : '';
        
        badge.innerHTML = badgeContent + conditionContent;
        
        return badge;
    }

    // Utility functions
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }

    formatTime(seconds) {
        if (seconds < 60) {
            return `${seconds}s`;
        } else {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        }
    }

    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = show ? 'flex' : 'none';
        }
    }

    showError(message) {
        // Create a simple error notification
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #EF4444;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            z-index: 1000;
            font-weight: 600;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 4000);
    }

    logout() {
        // Clear localStorage
        localStorage.removeItem('currentUser');
        
        // Redirect to home page
        window.location.href = '/';
    }
}

// Initialize the profile when the page loads
let userProfileInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!userProfileInstance) {
        userProfileInstance = new UserProfile();
    }
}); 