// BugYou Leaderboard JavaScript
class Leaderboard {
    constructor() {
        this.currentFilter = 'overall';
        this.currentFilterValue = '';
        this.currentUser = null;
        this.init();
    }

    init() {
        this.checkUserLogin();
        this.setupEventListeners();
        this.loadLeaderboard();
    }

    checkUserLogin() {
        const username = localStorage.getItem('currentUser');
        if (username) {
            this.currentUser = username;
            this.showUserSection(username);
            this.loadUserPosition(username);
        }
    }

    showUserSection(username) {
        const userSection = document.getElementById('userSection');
        const usernameElement = document.getElementById('currentUsername');
        
        if (userSection && usernameElement) {
            userSection.style.display = 'flex';
            usernameElement.textContent = username;
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

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleLogout();
            });
        }
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

        // Show loading
        leaderboardBody.innerHTML = `
            <div class="loading">
                Loading leaderboard...
            </div>
        `;

        try {
            // Build API URL with filters
            let url = 'https://bug-you-4frc-2qzzj8dse-muhammad-taahas-projects.vercel.app/api/leaderboard?limit=50';
            if (this.currentFilter !== 'overall') {
                url += `&filter_type=${this.currentFilter}`;
                if (this.currentFilterValue) {
                    url += `&filter_value=${this.currentFilterValue}`;
                }
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                this.renderLeaderboard(data.leaderboard);
            } else {
                this.showError('Failed to load leaderboard data');
            }
        } catch (error) {
            console.error('Error loading leaderboard:', error);
            this.showError('Network error while loading leaderboard');
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

        const entries = leaderboardData.map(entry => this.createLeaderboardEntry(entry)).join('');
        leaderboardBody.innerHTML = entries;
    }

    createLeaderboardEntry(entry) {
        const medal = entry.medal || `#${entry.rank_position}`;
        const bestLanguage = entry.best_language ? entry.best_language.toUpperCase() : 'N/A';
        const bestDifficulty = entry.best_difficulty ? entry.best_difficulty.charAt(0).toUpperCase() + entry.best_difficulty.slice(1) : 'N/A';
        const streakText = entry.streak_days > 0 ? `${entry.streak_days} days` : '0 days';

        return `
            <div class="leaderboard-entry">
                <div class="entry-rank">
                    ${medal}
                </div>
                <div class="entry-user">
                    ${entry.username}
                </div>
                <div class="entry-score">
                    ${entry.total_score.toLocaleString()}
                </div>
                <div class="entry-solved">
                    ${entry.total_solved}
                </div>
                <div class="entry-level">
                    ${entry.level}
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
            const response = await fetch(`https://bug-you-4frc-2qzzj8dse-muhammad-taahas-projects.vercel.app/api/leaderboard/user/${username}`);
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
        const userPositionCard = document.getElementById('userPositionCard');
        const userRank = document.getElementById('userRank');
        const userScore = document.getElementById('userScore');
        const userSolved = document.getElementById('userSolved');
        const userLevel = document.getElementById('userLevel');

        if (userPositionCard && userRank && userScore && userSolved && userLevel) {
            userRank.textContent = `#${positionData.rank_position}`;
            userScore.textContent = positionData.total_score.toLocaleString();
            userSolved.textContent = positionData.total_solved;
            userLevel.textContent = positionData.level;
            userPositionCard.style.display = 'block';
        }
    }

    hideUserPosition() {
        const userPositionCard = document.getElementById('userPositionCard');
        if (userPositionCard) {
            userPositionCard.style.display = 'none';
        }
    }

    handleLogout() {
        localStorage.removeItem('currentUser');
        window.location.reload();
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
document.addEventListener('DOMContentLoaded', () => {
    new Leaderboard();
}); 