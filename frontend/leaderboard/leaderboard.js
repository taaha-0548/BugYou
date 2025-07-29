// BugYou Leaderboard JavaScript
class Leaderboard {
    constructor() {
        this.currentFilter = 'overall';
        this.currentFilterValue = '';
        this.currentUser = null;
        this.updateInterval = null;
        this.init();
    }

    init() {
        this.checkUserLogin();
        this.setupEventListeners();
        this.loadLeaderboard();
        this.startAutoRefresh();
    }

    startAutoRefresh() {
        // Refresh leaderboard every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadLeaderboard();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    checkUserLogin() {
        const username = localStorage.getItem('currentUser');
        if (username) {
            this.currentUser = username;
            this.showUserProfile(username);
            this.loadUserPosition(username);
        }
    }

    showUserProfile(username) {
        const userProfile = document.getElementById('userProfile');
        const currentUsername = document.getElementById('currentUsername');
        
        if (userProfile && currentUsername) {
            userProfile.style.display = 'flex';
            currentUsername.textContent = username;
            
            // Setup user info click
            const userInfo = document.getElementById('userInfo');
            if (userInfo) {
                userInfo.addEventListener('click', () => {
                    window.location.href = '/user_profile';
                });
            }
        }
    }

    setupEventListeners() {
        // Filter button clicks
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleFilterClick(e);
            });
        });
    }

    handleFilterClick(e) {
        const btn = e.currentTarget;
        const filterType = btn.dataset.filter;
        const filterValue = btn.dataset.value;

        // Update active button
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update filter
        this.currentFilter = filterType;
        this.currentFilterValue = filterValue;

        // Reload leaderboard
        this.loadLeaderboard();
    }

    async loadLeaderboard() {
        const leaderboardBody = document.getElementById('leaderboardBody');
        if (!leaderboardBody) return;

        // Show loading state
        this.showLoadingState();

        try {
            // Build API URL with filters
            let url = '/api/leaderboard?limit=50';
            if (this.currentFilter !== 'overall') {
                url += `&filter_type=${this.currentFilter}`;
                if (this.currentFilterValue) {
                    url += `&filter_value=${this.currentFilterValue}`;
                }
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();

            if (data.success) {
                this.renderLeaderboard(data.leaderboard);
            } else {
                throw new Error(data.error || 'Failed to load leaderboard');
            }
        } catch (error) {
            console.error('Error loading leaderboard:', error);
            this.showErrorState(`Failed to load leaderboard: ${error.message}`);
        }
    }

    showLoadingState() {
        const leaderboardBody = document.getElementById('leaderboardBody');
        if (leaderboardBody) {
            leaderboardBody.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <div class="loading-text">Loading leaderboard...</div>
                </div>
            `;
        }
    }

    showErrorState(message) {
        const leaderboardBody = document.getElementById('leaderboardBody');
        if (leaderboardBody) {
            leaderboardBody.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div class="error-text">${message}</div>
                    <button class="retry-btn" onclick="leaderboard.loadLeaderboard()">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
        }
    }

    renderLeaderboard(leaderboardData) {
        const leaderboardBody = document.getElementById('leaderboardBody');
        if (!leaderboardBody) return;

        if (!leaderboardData || leaderboardData.length === 0) {
            leaderboardBody.innerHTML = `
                <div class="loading">
                    No data available for this filter
                </div>
            `;
            return;
        }

        // Validate each entry has required fields
        const validEntries = leaderboardData.filter(entry => {
            return entry && entry.username && 
                   (entry.total_score !== undefined && entry.total_score !== null) &&
                   (entry.total_solved !== undefined && entry.total_solved !== null) &&
                   (entry.level !== undefined && entry.level !== null);
        });

        if (validEntries.length === 0) {
            leaderboardBody.innerHTML = `
                <div class="loading">
                    No valid data available for this filter
                </div>
            `;
            return;
        }

        const entries = validEntries.map(entry => this.createLeaderboardEntry(entry)).join('');
        leaderboardBody.innerHTML = entries;
    }

    createLeaderboardEntry(entry) {
        // Ensure data types are correct
        const rankPosition = parseInt(entry.rank_position) || 0;
        const totalScore = parseInt(entry.total_score) || 0;
        const totalSolved = parseInt(entry.total_solved) || 0;
        const level = parseInt(entry.level) || 1;
        const streakDays = parseInt(entry.streak_days) || 0;
        
        const medal = entry.medal || `#${rankPosition}`;
        const bestLanguage = entry.best_language ? entry.best_language.toUpperCase() : 'N/A';
        const bestDifficulty = entry.best_difficulty ? entry.best_difficulty.charAt(0).toUpperCase() + entry.best_difficulty.slice(1) : 'N/A';
        const streakText = streakDays > 0 ? `${streakDays} days` : '0 days';

        return `
            <div class="leaderboard-entry">
                <div class="entry-rank">
                    ${medal}
                </div>
                <div class="entry-user">
                    ${entry.username || 'Unknown'}
                </div>
                <div class="entry-score">
                    ${totalScore.toLocaleString()}
                </div>
                <div class="entry-solved">
                    ${totalSolved}
                </div>
                <div class="entry-level">
                    ${level}
                </div>
                <div class="entry-best">
                    <div class="best-language">${bestLanguage}</div>
                    <div class="best-difficulty">${bestDifficulty}</div>
                </div>
                <div class="entry-streak">
                    ${streakText}
                </div>
            </div>
        `;
    }

    async loadUserPosition(username) {
        try {
            const response = await fetch(`/api/leaderboard/user/${username}`);
            const data = await response.json();

            if (data.success) {
                this.showUserPosition(data.position);
            } else {
                // User might not be in leaderboard yet
                this.hideUserPosition();
            }
        } catch (error) {
            console.error('Error loading user position:', error);
            this.hideUserPosition();
        }
    }

    showUserPosition(positionData) {
        const userPositionSection = document.getElementById('userPositionSection');
        const userRank = document.getElementById('userRank');
        const userScore = document.getElementById('userScore');
        const userSolved = document.getElementById('userSolved');
        const userLevel = document.getElementById('userLevel');

        if (userPositionSection && userRank && userScore && userSolved && userLevel) {
            // Ensure data types are correct
            const rankPosition = parseInt(positionData.rank_position) || 0;
            const totalScore = parseInt(positionData.total_score) || 0;
            const totalSolved = parseInt(positionData.total_solved) || 0;
            const level = parseInt(positionData.level) || 1;
            
            userRank.textContent = `#${rankPosition}`;
            userScore.textContent = totalScore.toLocaleString();
            userSolved.textContent = totalSolved;
            userLevel.textContent = level;
            userPositionSection.style.display = 'block';
        }
    }

    hideUserPosition() {
        const userPositionSection = document.getElementById('userPositionSection');
        if (userPositionSection) {
            userPositionSection.style.display = 'none';
        }
    }

    showError(message) {
        const leaderboardBody = document.getElementById('leaderboardBody');
        if (leaderboardBody) {
            leaderboardBody.innerHTML = `
                <div class="loading">
                    ${message}
                </div>
            `;
        }
    }
}

// Initialize leaderboard when DOM is loaded
let leaderboard;
document.addEventListener('DOMContentLoaded', () => {
    leaderboard = new Leaderboard();
}); 