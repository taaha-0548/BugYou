// BugYou Debugging Interface JavaScript
console.log('JS loaded 🎉');  // Test log to verify script loading

// Configuration
const API_BASE = 'http://localhost:5000/api';  // Flask backend
let editor;
let currentLanguage = 'python';
let currentDifficulty = 'basic';
let currentChallengeId = 1;
let currentChallenge = null;
let startTime = Date.now();
let timerInterval;
let attempts = 0;
let score = 10;
let hintsUsed = 0;
let wrongSubmissions = 0;

// Test case navigation variables
let currentTestCase = 0;
let testCases = [];
let testResults = [];

// --- HINTS FEATURE STATE ---
let challengeHints = []; // Array of hints for the current challenge
let revealedHints = [];  // Indices of revealed hints (reset on new challenge)

// Cache for API responses
const apiCache = new Map();
const API_CACHE_DURATION = 5000; // 5 seconds

// Add cache busting parameter to API calls
function getApiUrl(endpoint) {
    const timestamp = new Date().getTime();
    return `${API_BASE}${endpoint}${endpoint.includes('?') ? '&' : '?'}_=${timestamp}`;
}

// Optimized API call function with caching
async function fetchWithCache(endpoint, options = {}) {
    const cacheKey = endpoint + JSON.stringify(options);
    const now = Date.now();
    
    // Check cache first
    if (apiCache.has(cacheKey)) {
        const cached = apiCache.get(cacheKey);
        if (now - cached.timestamp < API_CACHE_DURATION) {
            return cached.data;
        }
        apiCache.delete(cacheKey);
    }
    
    // Make API call
    const response = await fetch(getApiUrl(endpoint), options);
    const data = await response.json();
    
    // Cache the response
    if (response.ok && !endpoint.includes('/execute') && !endpoint.includes('/validate')) {
        apiCache.set(cacheKey, {
            timestamp: now,
            data: data
        });
    }
    
    return data;
}

// Debounce function to prevent rapid button clicks
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    // Initialize UI components first
    initEditor();
    initTimer();
    initTestCaseNavigation();
    initEventListeners();
    initUIHandlers();
    
    // Apply default theme
    applyTheme('basic');
    
    // Clear backend cache and load challenge
    try {
        await fetch(getApiUrl('/cache/clear'));
        await loadCurrentChallenge();
    } catch (error) {
        console.error('Failed to initialize:', error);
        showResultsNotification('Initialization Error', 'Failed to load initial challenge. Please refresh the page.', 'error');
    }
});

// Initialize CodeMirror editor
function initEditor() {
    const textarea = document.getElementById('code');
    editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: 'python',
        theme: 'material-darker',
        autoCloseBrackets: true,
        matchBrackets: true,
        indentUnit: 4,
        smartIndent: true
    });

    editor.setValue('// Loading challenge from database...');
}

// Initialize count-up timer
function initTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

// Initialize test case navigation functionality
function initTestCaseNavigation() {
    const testCaseButtons = document.getElementById('testCaseButtons');
    if (!testCaseButtons) return;

    // Remove old event listeners
    const oldButtons = testCaseButtons.querySelectorAll('.test-case-btn');
    oldButtons.forEach(btn => {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
    });

    // Add new event listeners
    const buttons = testCaseButtons.querySelectorAll('.test-case-btn');
    buttons.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            currentTestCase = index;
            showTestCase(index);
            updateActiveTestCaseButton();
        });
    });
}

function updateActiveTestCaseButton() {
    const testCaseButtons = document.querySelectorAll('.test-case-btn');
    testCaseButtons.forEach((btn, index) => {
        btn.classList.remove('active', 'passed', 'failed', 'pending');
        if (index === currentTestCase) {
            btn.classList.add('active');
        }
        // Add result status if available
        if (testResults[index]) {
            btn.classList.add(testResults[index].passed ? 'passed' : 'failed');
        }
    });

    // Update test case display
    showTestCase(currentTestCase);
}

// Helper to get test panel elements by context
function getTestPanelElements(context = 'main') {
    if (context === 'results') {
        return {
            testInputDisplay: document.querySelector('.results-test-input-display'),
            testExpectedDisplay: document.querySelector('.results-test-expected-display'),
            testActualDisplay: document.querySelector('.results-test-actual-display'),
            testResultBadge: document.querySelector('.results-test-result-badge'),
            actualOutputSection: document.querySelector('.results-actual-output-section'),
        };
    } else {
        return {
            testInputDisplay: document.getElementById('testInputDisplay'),
            testExpectedDisplay: document.getElementById('testExpectedDisplay'),
            testActualDisplay: document.getElementById('testActualDisplay'),
            testResultBadge: document.getElementById('testResultBadge'),
            actualOutputSection: document.getElementById('actualOutputSection'),
        };
    }
}

function showTestCase(index, context = 'main') {
    const {
        testInputDisplay,
        testExpectedDisplay,
        testActualDisplay,
        testResultBadge,
        actualOutputSection
    } = getTestPanelElements(context);
    
    if (testCases[index]) {
        const testCase = testCases[index];
        // Always preserve input and expected output
        testInputDisplay.innerHTML = `<pre>${testCase.input}</pre>`;
        // Handle both expected_output and expected fields for backward compatibility
        const expectedOutput = testCase.expected_output || testCase.expected;
        testExpectedDisplay.innerHTML = `<pre>${expectedOutput}</pre>`;
        
        // Display actual output if test has been run
        if (testResults && testResults[index]) {
            actualOutputSection.style.display = 'block';
            const actualOutput = testResults[index].output !== undefined ? testResults[index].output : 'No output';
            testActualDisplay.innerHTML = `<pre>${actualOutput}</pre>`;
            
            // Update result badge with detailed feedback
            if (testResults[index].passed) {
                testResultBadge.innerHTML = '<i class="fas fa-check"></i> Test Case ' + (index + 1) + ' Passed';
                testResultBadge.className = 'badge success';
            } else {
                const isHidden = testCase.hidden;
                const failMessage = isHidden ? 
                    'Hidden Test Case ' + (index + 1) + ' Failed' :
                    'Test Case ' + (index + 1) + ' Failed';
                testResultBadge.innerHTML = `<i class="fas fa-times"></i> ${failMessage}`;
                testResultBadge.className = 'badge error';
                if (testResults[index].error) {
                    testActualDisplay.innerHTML += `<pre class="error">${testResults[index].error}</pre>`;
                }
                if (!isHidden) {
                    testActualDisplay.innerHTML += `<pre class="error">Expected: ${expectedOutput}\nActual: ${actualOutput}</pre>`;
                }
            }
        } else {
            actualOutputSection.style.display = 'none';
            testResultBadge.innerHTML = '<i class="fas fa-minus"></i> Test Case ' + (index + 1) + ' Not Run';
            testResultBadge.className = 'badge';
        }
    }
}

// Initialize event listeners with optimizations
function initEventListeners() {
    // Run button - debounced to prevent rapid clicks
    const runBtn = document.getElementById('runCode');
    if (runBtn) {
        const debouncedRun = debounce(async () => {
            if (runBtn.disabled) return;
            runBtn.disabled = true;
            try {
                await runTests();
            } finally {
                setTimeout(() => {
                    runBtn.disabled = false;
                }, 500);
            }
        }, 300);
        runBtn.addEventListener('click', debouncedRun);
    }

    // Submit button - debounced
    const submitBtn = document.getElementById('submitCode');
    if (submitBtn) {
        const debouncedSubmit = debounce(async () => {
            if (submitBtn.disabled) return;
            submitBtn.disabled = true;
            try {
                await submitSolution();
            } finally {
                setTimeout(() => {
                    submitBtn.disabled = false;
                }, 500);
            }
        }, 300);
        submitBtn.addEventListener('click', debouncedSubmit);
    }

    // Hint button - instant response
    const hintBtn = document.getElementById('hintBtn');
    if (hintBtn) {
        hintBtn.addEventListener('click', () => {
            if (!hintBtn.disabled) {
                showHint();
            }
        });
    }

    // Language selector - debounced
    const langSelect = document.getElementById('language');
    if (langSelect) {
        const debouncedChange = debounce((event) => {
            changeLanguage(event);
        }, 300);
        langSelect.addEventListener('change', debouncedChange);
    }

    // Random challenge button - debounced
    const randomBtn = document.getElementById('loadRandomBtn');
    if (randomBtn) {
        const debouncedRandom = debounce(async () => {
            if (randomBtn.disabled) return;
            randomBtn.disabled = true;
            try {
                await loadRandomChallenge();
            } finally {
                setTimeout(() => {
                    randomBtn.disabled = false;
                }, 500);
            }
        }, 300);
        randomBtn.addEventListener('click', debouncedRandom);
    }
}

// Initialize UI handlers for modals and notifications
function initUIHandlers() {
    // Hint modal handlers
    const hintModal = document.getElementById('hintModal');
    const hintModalClose = document.getElementById('hintModalClose');
    const hintModalOk = document.getElementById('hintModalOk');
    
    hintModalClose.addEventListener('click', () => hideHintModal());
    hintModalOk.addEventListener('click', () => hideHintModal());
    
    // Results notification handlers
    const resultsNotification = document.getElementById('resultsNotification');
    const resultsNotificationClose = document.getElementById('resultsNotificationClose');
    
    resultsNotificationClose.addEventListener('click', () => hideResultsNotification());
    
    // Results panel handlers
    const resultsPanel = document.getElementById('resultsPanel');
    const panelClose = document.getElementById('panelClose');
    const resultsOverlay = document.getElementById('resultsOverlay');
    
    panelClose.addEventListener('click', () => hideResultsPanel());
    resultsOverlay.addEventListener('click', () => hideResultsPanel());
    
    // Random challenge modal handlers
    const randomChallengeModal = document.getElementById('randomChallengeModal');
    const randomChallengeModalClose = document.getElementById('randomChallengeModalClose');
    const randomChallengeModalOk = document.getElementById('randomChallengeModalOk');
    
    randomChallengeModalClose.addEventListener('click', () => hideRandomChallengeModal());
    randomChallengeModalOk.addEventListener('click', () => hideRandomChallengeModal());
    
    // Submission modal handlers
    const submissionModal = document.getElementById('submissionModal');
    const submissionModalClose = document.getElementById('submissionModalClose');
    const submissionModalClose2 = document.getElementById('submissionModalClose2');
    const loadNextChallenge = document.getElementById('loadNextChallenge');
    
    submissionModalClose.addEventListener('click', () => hideSubmissionModal());
    submissionModalClose2.addEventListener('click', () => hideSubmissionModal());
    loadNextChallenge.addEventListener('click', () => {
        hideSubmissionModal();
        loadRandomChallenge();
    });
    
    // Click outside to close modals
    hintModal.addEventListener('click', (e) => {
        if (e.target === hintModal) hideHintModal();
    });
    
    randomChallengeModal.addEventListener('click', (e) => {
        if (e.target === randomChallengeModal) hideRandomChallengeModal();
    });
    
    submissionModal.addEventListener('click', (e) => {
        if (e.target === submissionModal) hideSubmissionModal();
    });
    
    // Auto-hide will be handled in showResultsNotification function
}

// UI Helper functions
function showHintModal(hintText) {
    const hintModal = document.getElementById('hintModal');
    const hintContent = document.getElementById('hintContent');
    const hintsRemaining = document.getElementById('hintsRemaining');
    
    hintContent.textContent = hintText;
    hintsRemaining.textContent = `${3 - hintsUsed} hints remaining`;
    hintModal.classList.add('show');
}

function hideHintModal() {
    const hintModal = document.getElementById('hintModal');
    hintModal.classList.remove('show');
}

function showResultsNotification(title, message, type = 'success') {
    const resultsNotification = document.getElementById('resultsNotification');
    const resultsIcon = document.getElementById('resultsIcon');
    const resultsTitle = document.getElementById('resultsTitle');
    const resultsMessage = document.getElementById('resultsMessage');
    
    // Set icon based on type
    resultsIcon.className = type === 'success' ? 'fas fa-check-circle' : 
                           type === 'error' ? 'fas fa-exclamation-circle' : 
                           'fas fa-info-circle';
    
    // Set notification type class
    resultsNotification.className = `notification show ${type}`;
    
    resultsTitle.textContent = title;
    resultsMessage.textContent = message;
    
    // Auto-hide after 3 seconds (shorter for notification bar)
    setTimeout(() => {
        if (resultsNotification.classList.contains('show')) {
            hideResultsNotification();
        }
    }, 3000);
}

function hideResultsNotification() {
    const resultsNotification = document.getElementById('resultsNotification');
    resultsNotification.classList.remove('show');
}

function showResultsPanel() {
    const resultsPanel = document.getElementById('resultsPanel');
    const resultsOverlay = document.getElementById('resultsOverlay');
    
    resultsPanel.classList.add('show');
    resultsOverlay.classList.add('show');
    
    // Auto-hide after 15 seconds
    setTimeout(() => {
        if (resultsPanel.classList.contains('show')) {
            hideResultsPanel();
        }
    }, 15000);
}

function hideResultsPanel() {
    const resultsPanel = document.getElementById('resultsPanel');
    const resultsOverlay = document.getElementById('resultsOverlay');
    
    resultsPanel.classList.remove('show');
    resultsOverlay.classList.remove('show');
}

// Show submission modal with enhanced test results
function showSubmissionModal(data) {
    const submissionModal = document.getElementById('submissionModal');
    const submissionIcon = document.getElementById('submissionIcon');
    const submissionTitle = document.getElementById('submissionTitle');
    const submissionContent = document.getElementById('submissionContent');
    const finalScore = document.getElementById('finalScore');
    const finalTime = document.getElementById('finalTime');
    const finalAttempts = document.getElementById('finalAttempts');
    const finalHints = document.getElementById('finalHints');
    const submissionMessage = document.getElementById('submissionMessage');
    
    // Determine success status
    const isSuccess = data.success !== false && !data.error;
    
    // Set modal class and icon based on success
    submissionModal.className = `modal-overlay submission-modal ${isSuccess ? 'success' : 'error'}`;
    submissionIcon.className = isSuccess ? 'fas fa-trophy' : 'fas fa-exclamation-triangle';
    submissionTitle.textContent = isSuccess ? 'Submission Complete!' : 'Submission Failed';
    
    // Update stats
    if (finalScore) finalScore.textContent = `${score}/${currentChallenge?.max_score || 10}`;
    if (finalTime) finalTime.textContent = formatTime(getElapsedTime());
    if (finalAttempts) finalAttempts.textContent = attempts;
    if (finalHints) finalHints.textContent = hintsUsed;
    
    // Create detailed message
    let message = '';
    
    if (data.error) {
        message = `Error: ${data.error}`;
    } else {
        // Show comprehensive test results
        const visiblePassed = data.visible_tests_passed || 0;
        const visibleTotal = data.visible_tests_total || 0;
        const hiddenPassed = data.hidden_tests_passed || 0;
        const hiddenTotal = data.hidden_tests_total || 0;
        const totalPassed = data.total_tests_passed || 0;
        const totalTests = data.total_tests || 0;
        
        if (totalTests > 0) {
            message += `🧪 Test Results:\n`;
            message += `   • Visible Tests: ${visiblePassed}/${visibleTotal} passed\n`;
            if (hiddenTotal > 0) {
                message += `   • Hidden Tests: ${hiddenPassed}/${hiddenTotal} passed\n`;
            }
            message += `   • Overall: ${totalPassed}/${totalTests} tests passed\n\n`;
            
            const passPercentage = Math.round((totalPassed / totalTests) * 100);
            
            if (passPercentage === 100) {
                message += `🎉 Perfect! All tests passed!\n`;
                message += `Your solution handles all test cases correctly, including edge cases and hidden validation tests.`;
            } else if (passPercentage >= 80) {
                message += `✅ Great job! Most tests passed.\n`;
                message += `Your solution is mostly correct. Consider edge cases that might need attention.`;
            } else if (passPercentage >= 60) {
                message += `⚠️  Good progress, but some tests failed.\n`;
                message += `Your solution works for basic cases but may need fixes for edge cases or error handling.`;
            } else {
                message += `❌ Several tests failed.\n`;
                message += `Your solution needs significant improvements. Review the algorithm logic and test cases.`;
            }
        } else {
            message = data.message || 'Your submission has been processed.';
        }
        
        // Add performance notes
        if (getElapsedTime() < 60) {
            message += `\n\n⚡ Fast completion time!`;
        }
        if (hintsUsed === 0) {
            message += `\n🧠 No hints used - excellent problem-solving!`;
        }
    }
    
    if (submissionMessage) {
        submissionMessage.textContent = message;
    }
    
    submissionModal.classList.add('show');
}

function hideSubmissionModal() {
    const submissionModal = document.getElementById('submissionModal');
    submissionModal.classList.remove('show');
}

// Show random challenge modal
function showRandomChallengeModal(language, difficulty, title) {
    const modal = document.getElementById('randomChallengeModal');
    const languageElement = document.getElementById('randomLanguage');
    const difficultyElement = document.getElementById('randomDifficulty');
    const titleElement = document.getElementById('randomTitle');
    const messageElement = document.getElementById('randomChallengeMessage');
    
    if (languageElement) languageElement.textContent = language;
    if (difficultyElement) difficultyElement.textContent = difficulty;
    if (titleElement) titleElement.textContent = title;
    if (messageElement) {
        messageElement.textContent = `Your random ${difficulty} challenge in ${language} has been loaded! Good luck fixing the bug!`;
    }
    
    modal.classList.add('show');
}

function hideRandomChallengeModal() {
    const randomChallengeModal = document.getElementById('randomChallengeModal');
    randomChallengeModal.classList.remove('show');
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Apply theme based on difficulty level
function applyTheme(difficulty) {
    const body = document.body;
    
    // Remove existing theme classes
    body.classList.remove('theme-basic', 'theme-intermediate', 'theme-advanced');
    
    // Apply new theme based on difficulty
    switch (difficulty.toLowerCase()) {
        case 'basic':
            body.classList.add('theme-basic');
            break;
        case 'intermediate':
            body.classList.add('theme-intermediate');
            break;
        case 'advanced':
            body.classList.add('theme-advanced');
            break;
        default:
            body.classList.add('theme-basic');
            break;
    }
}

// Show hint functionality (now robust, array-based, and sidebar-aware)
function showHint() {
    if (!challengeHints || challengeHints.length === 0) {
        showResultsNotification('No Hints', 'No hints are available for this challenge.', 'info');
        return;
    }
    // Find the next unrevealed hint
    const nextHintIdx = revealedHints.length;
    if (nextHintIdx >= challengeHints.length) {
        showResultsNotification('No More Hints', 'You have used all available hints for this challenge.', 'warning');
        updateHintsDisplay(); // Ensure button disables
        return;
    }
    // Reveal next hint
    revealedHints.push(nextHintIdx);
    hintsUsed = revealedHints.length;
    score = Math.max(0, score - 2);
    updateScore();
    updateHintsSidebar();
    updateHintsDisplay();
    // Show notification
    showResultsNotification('Hint Revealed', `Hint ${nextHintIdx + 1} has been revealed! (-2 points)`, 'info');
}

// Update the hints sidebar to show revealed hints
function updateHintsSidebar() {
    const hintsSection = document.getElementById('hintsSection');
    const hintsList = document.getElementById('hintsList');
    if (!hintsSection || !hintsList) return;
    hintsList.innerHTML = '';
    if (!challengeHints || challengeHints.length === 0) {
        hintsSection.style.display = 'none';
        return;
    }
    if (revealedHints.length === 0) {
        hintsSection.style.display = 'block';
        hintsList.innerHTML = '<div class="hint-item hint-empty">No hints revealed yet. Click the Hint button to reveal one!</div>';
        return;
    }
    hintsSection.style.display = 'block';
    revealedHints.forEach(idx => {
        if (challengeHints[idx]) {
            const hintItem = document.createElement('div');
            hintItem.className = 'hint-item';
            hintItem.id = `hint-${idx+1}`;
            const hintHeader = document.createElement('div');
            hintHeader.className = 'hint-header';
            hintHeader.innerHTML = `<span class="hint-number">Hint ${idx+1}</span>`;
            const hintContent = document.createElement('div');
            hintContent.className = 'hint-content';
            hintContent.innerHTML = challengeHints[idx].replace(/\n/g, '<br>');
            hintItem.appendChild(hintHeader);
            hintItem.appendChild(hintContent);
            hintsList.appendChild(hintItem);
        }
    });
}

// Update the hint button and section display
function updateHintsDisplay() {
    const hintBtn = document.getElementById('hintBtn');
    const hintsSection = document.getElementById('hintsSection');
    
    if (!currentChallenge) {
        hintBtn.style.display = 'none';
        hintsSection.style.display = 'none';
        return;
    }
    
    // Initialize hints array if not present
    if (!challengeHints) {
        challengeHints = [];
    }
    
    // Always show the hint button, but disable it if no hints are available
    hintBtn.style.display = 'inline-flex';
    
    // Update hint button text and state
    const remainingHints = challengeHints.length - revealedHints.length;
    if (remainingHints <= 0) {
        hintBtn.disabled = true;
        hintBtn.innerHTML = `
            <i class="fas fa-lightbulb"></i>
            No more hints
        `;
    } else {
        hintBtn.disabled = false;
        hintBtn.innerHTML = `
            <i class="fas fa-lightbulb"></i>
            Hint (${remainingHints})
        `;
    }
    
    // Show/hide hints section based on whether there are any hints
    hintsSection.style.display = challengeHints.length > 0 ? 'block' : 'none';
    
    // Update hints list
    const hintsList = document.getElementById('hintsList');
    hintsList.innerHTML = '';
    
    revealedHints.forEach((hintIndex) => {
        const hint = challengeHints[hintIndex];
        if (hint) {
            const hintElement = document.createElement('div');
            hintElement.className = 'hint-item';
            hintElement.innerHTML = `
                <div class="hint-header">
                    <span class="hint-number">Hint ${hintIndex + 1}</span>
                </div>
                <div class="hint-content">${hint}</div>
            `;
            hintsList.appendChild(hintElement);
        }
    });
}

// Update score display
function updateScore() {
    const scoreElements = [
        document.getElementById('score'),
        document.getElementById('scoreValue'),
        document.getElementById('finalScore')
    ];
    
    scoreElements.forEach(element => {
        if (element) {
            element.textContent = `${score}/10`;
        }
    });
}

// Submit code for validation
async function submitSolution() {
    if (!currentChallenge) {
        showResultsNotification('Error', 'No challenge loaded', 'error');
        return;
    }

    const code = editor.getValue();
    if (!code.trim()) {
        showResultsNotification('Error', 'Please write some code first', 'error');
        return;
    }

    try {
        // Show loading state
        const submitBtn = document.getElementById('submitCode');
        if (!submitBtn) {
            console.error('Submit button not found');
            showResultsNotification('Error', 'Internal error: Submit button not found', 'error');
            return;
        }

        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Tests...';
        submitBtn.disabled = true;

        // Initialize test results and show running state
        testResults = [];
        testCases.forEach((_, index) => {
            testResults[index] = { status: 'running' };
            showTestCase(index);
        });

        try {
            const response = await fetch(getApiUrl('/validate'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: code,
                    language: currentLanguage,
                    challenge_id: currentChallenge.challenge_id,
                    difficulty: currentChallenge.difficulty
                })
            });

            const data = await response.json();
            console.log('Submission results:', data);

            // Process visible test results first with delay
            if (data.visible_results && data.visible_results.test_results) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Visible Tests...';
                for (let i = 0; i < data.visible_results.test_results.length; i++) {
                    testResults[i] = data.visible_results.test_results[i];
                    showTestCase(i);
                    await new Promise(resolve => setTimeout(resolve, 300)); // 300ms delay between tests
                }
            }

            // Process hidden test results
            if (data.hidden_results && data.hidden_results.test_results) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Hidden Tests...';
                const startIndex = testResults.length;
                for (let i = 0; i < data.hidden_results.test_results.length; i++) {
                    const result = data.hidden_results.test_results[i];
                    testResults[startIndex + i] = {
                        ...result,
                        output: result.passed ? '[Hidden Test Output]' : 'Test Failed',
                        error: result.error || (result.passed ? null : 'Hidden test case failed')
                    };
                    showTestCase(startIndex + i);
                    await new Promise(resolve => setTimeout(resolve, 300)); // 300ms delay between tests
                }
            }

            updateTestResults();

            if (data.success && data.all_passed) {
                // Show success message with score
                showResultsNotification(
                    'Success', 
                    `Congratulations! All test cases passed (including hidden tests). Score: ${data.score}`, 
                    'success'
                );
                
                // Update user progress if needed
                if (typeof updateUserProgress === 'function') {
                    updateUserProgress(currentChallenge.challenge_id, data.score);
                }
            } else {
                // Show appropriate error message
                if (data.error === 'Hidden test cases failed') {
                    const visiblePassed = data.visible_results.test_results.every(r => r.passed);
                    const message = visiblePassed ?
                        'Your code passed all visible test cases but failed some hidden test cases. Try to make your solution more robust!' :
                        'Some test cases failed. Please check the results and try again.';
                    showResultsNotification('Warning', message, 'warning');
                } else {
                    showResultsNotification(
                        'Error',
                        data.error || 'Not all test cases passed. Please fix your solution and try again.',
                        'error'
                    );
                }
            }
        } finally {
            // Always reset button state
            if (submitBtn) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        }
    } catch (error) {
        console.error('Error submitting solution:', error);
        showResultsNotification('Error', 'Failed to submit solution: ' + error.message, 'error');
        
        // Reset button state if we can
        const submitBtn = document.getElementById('submitCode');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit';
            submitBtn.disabled = false;
        }
    }
}

// Update loadCurrentChallenge to use correct API endpoint
async function loadCurrentChallenge() {
    try {
        const data = await fetchWithCache(`/challenge/${currentLanguage}/${currentDifficulty}/${currentChallengeId}`);
        
        if (data.success) {
            currentChallenge = data.challenge;
            testCases = currentChallenge.test_cases || [];
            challengeHints = Array.isArray(currentChallenge.hints) ? currentChallenge.hints : [];
            revealedHints = [];
            
            // Reset state
            score = 10;
            hintsUsed = 0;
            wrongSubmissions = 0;
            attempts = 0;
            startTime = Date.now();
            
            updateChallengeDisplay();
            updateScore();
            
            // Show first test case
            if (testCases.length > 0) {
                currentTestCase = 0;
                showTestCase(0);
                updateActiveTestCaseButton();
            }
            
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Challenge loading error:', error);
        showResultsNotification('Loading Failed', `Failed to load challenge: ${error.message}`, 'error');
    }
}

// --- CHALLENGE DISPLAY: update sidebar and hint button on new challenge ---
function updateChallengeDisplay() {
    if (!currentChallenge) {
        console.error('No challenge data available');
        return;
    }
    
    console.log('Updating challenge display:', currentChallenge);
    
    // Update title and difficulty badge
    const titleElement = document.getElementById('challengeTitle');
    const difficultyBadge = document.getElementById('difficultyBadge');
    
    if (titleElement && currentChallenge.title) {
        titleElement.textContent = currentChallenge.title;
    }
    
    if (difficultyBadge && currentChallenge.difficulty) {
        difficultyBadge.textContent = currentChallenge.difficulty.toUpperCase();
        difficultyBadge.className = `difficulty-badge ${currentChallenge.difficulty.toLowerCase()}`;
    }
    
    // Update description (if available)
    const descriptionElement = document.getElementById('challengeDescription');
    if (descriptionElement) {
        descriptionElement.innerHTML = currentChallenge.description || '';
    }
    
    // Update problem statement with proper newline handling
    const problemElement = document.getElementById('challengeProblem');
    if (problemElement && currentChallenge.problem_statement) {
        const formattedProblem = currentChallenge.problem_statement.replace(/\n/g, '<br>');
        problemElement.innerHTML = formattedProblem;
    }
    
    // Update code editor with buggy code
    if (editor && currentChallenge.buggy_code) {
        editor.setValue(currentChallenge.buggy_code);
        editor.refresh(); // Force CodeMirror to refresh
    }
    
    // Update test cases
    updateTestCasesDisplay();
    
    // Update hints display
    updateHintsDisplay();
    
    // Apply theme based on difficulty
    applyTheme(currentChallenge.difficulty);
    
    // Reset hints when loading a new challenge
    const hintsList = document.getElementById('hintsList');
    if (hintsList) {
        hintsList.innerHTML = '';
        console.log('Cleared hints list');
    }
    
    // Ensure hints sidebar is reset and shown appropriately
    updateHintsSidebar();
    
    console.log('Challenge display updated successfully');
}

// Update test cases display to handle test case objects
function updateTestCasesDisplay() {
    if (!currentChallenge || !testCases) {
        console.log('No challenge data available for test cases');
        return;
    }
    
    console.log('Updating test cases display');
    testResults = [];
    
    // Update test case buttons
    const testCaseButtons = document.getElementById('testCaseButtons');
    if (testCaseButtons && testCases.length > 0) {
        let buttonsHtml = '';
        testCases.forEach((testCase, index) => {
            buttonsHtml += `
                <button class="test-case-btn ${index === 0 ? 'active' : ''}" data-case="${index}">
                    Case ${index + 1}
                </button>`;
        });
        testCaseButtons.innerHTML = buttonsHtml;
        
        // Reinitialize test case navigation
        initTestCaseNavigation();
        
        // Show first test case
        currentTestCase = 0;
        showTestCase(0);
        
        // Update test summary
        const testSummary = document.getElementById('testSummary');
        if (testSummary) {
            testSummary.style.display = 'block';
            const totalCount = testSummary.querySelector('.total-count');
            const passedCount = testSummary.querySelector('.passed-count');
            if (totalCount) totalCount.textContent = testCases.length;
            if (passedCount) passedCount.textContent = '0';
        }
    } else {
        console.log('No test cases found or test case buttons container missing');
    }
}

// Update loadRandomChallenge to properly handle test cases and score
async function loadRandomChallenge() {
    const randomBtn = document.getElementById('loadRandomBtn');
    const originalText = randomBtn.innerHTML;
    
    randomBtn.disabled = true;
    randomBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>Loading...';
    
    try {
        const response = await fetch(getApiUrl(`/challenge/random/${currentLanguage}`));
        const data = await response.json();
        
        if (data.success) {
            const randomInfo = data.random_info;
            
            currentLanguage = randomInfo.language;
            currentDifficulty = randomInfo.difficulty;
            currentChallengeId = randomInfo.challenge_id;
            currentChallenge = data.challenge;
            
            // Extract test cases from challenge data
            testCases = currentChallenge.test_cases || [];
            testResults = [];
            
            // Update language selector
            const langSelect = document.getElementById('language');
            if (langSelect) {
                langSelect.value = currentLanguage;
            }
            
            // Update editor mode
            let mode = currentLanguage;
            if (currentLanguage === 'java') {
                mode = 'text/x-java';
            } else if (currentLanguage === 'cpp') {
                mode = 'text/x-c++src';
            }
            editor.setOption('mode', mode);
            
            // Reset state
            score = 10;
            hintsUsed = 0;
            wrongSubmissions = 0;
            attempts = 0;
            startTime = Date.now();
            
            // Update hints
            challengeHints = Array.isArray(currentChallenge.hints) ? currentChallenge.hints : [];
            revealedHints = [];
            
            // Update display
            updateChallengeDisplay();
            updateScore();
            updateHintsDisplay();
            
            // Show the random challenge modal
            showRandomChallengeModal(currentLanguage, currentDifficulty, currentChallenge.title);
            
        } else {
            throw new Error(data.error || 'Failed to load random challenge');
        }
        
    } catch (error) {
        console.error('Random challenge loading error:', error);
        showResultsNotification('Loading Failed', `Failed to load random challenge: ${error.message}`, 'error');
    } finally {
        randomBtn.disabled = false;
        randomBtn.innerHTML = originalText;
    }
}

// Change programming language
function changeLanguage(event) {
    currentLanguage = event.target.value;
    
    let mode = currentLanguage;
    if (currentLanguage === 'java') {
        mode = 'text/x-java';
    } else if (currentLanguage === 'cpp') {
        mode = 'text/x-c++src';
    }
    editor.setOption('mode', mode);
    
    score = 10;
    hintsUsed = 0;
    wrongSubmissions = 0;
    attempts = 0;
    startTime = Date.now();
    updateScore();
    
    loadCurrentChallenge();
}

// Extract function name from code
function extractFunctionName(code, language) {
    let match;
    
    switch (language) {
        case 'python':
            match = code.match(/def\s+(\w+)\s*\(/);
            return match ? match[1] : 'main_function';
            
        case 'javascript':
            match = code.match(/function\s+(\w+)\s*\(/) || code.match(/const\s+(\w+)\s*=/) || code.match(/let\s+(\w+)\s*=/);
            return match ? match[1] : 'main_function';
            
        case 'java':
            match = code.match(/public\s+static\s+\w+\s+(\w+)\s*\(/);
            return match ? match[1] : 'main_function';
            
        case 'cpp':
            match = code.match(/\w+\s+(\w+)\s*\([^)]*\)\s*{/) || code.match(/(\w+)\s*\([^)]*\)\s*{/);
            if (match && !['main', 'int', 'void', 'string', 'using', 'include'].includes(match[1])) {
                return match[1];
            }
            return 'calculateSum';
            
        default:
            return 'main_function';
    }
}

// Run tests for current challenge
async function runTests() {
    // Get button first and store original state
    const runBtn = document.getElementById('runCode');
    const originalText = runBtn ? runBtn.innerHTML : '';
    let buttonRestored = false;

    // Function to restore button state
    const restoreButton = () => {
        if (runBtn && !buttonRestored) {
            runBtn.innerHTML = originalText;
            runBtn.disabled = false;
            buttonRestored = true;
        }
    };

    try {
        if (!currentChallenge) {
            showResultsNotification('Error', 'No challenge loaded', 'error');
            return;
        }

        const code = editor.getValue();
        if (!code.trim()) {
            showResultsNotification('Error', 'Please write some code first', 'error');
            return;
        }

        // Initialize test results
        testResults = [];
        // Show initial state for all test cases
        if (!testCases || !Array.isArray(testCases)) {
            showResultsNotification('Error', 'No test cases available', 'error');
            return;
        }

        testCases.forEach((_, index) => {
            testResults[index] = { status: 'running' };
            showTestCase(index);
        });

        // Update button state
        if (runBtn) {
            runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Tests...';
            runBtn.disabled = true;
        }

        // Prepare request data
        const requestData = {
            code: code,
            language: currentLanguage,
            test_cases: testCases
        };

        // Execute tests with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

        try {
            const response = await fetch(getApiUrl('/execute'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const data = await response.json();
            console.log('Test results:', data);

            if (data.success) {
                // Ensure test_results exists and is an array
                const testResultsArray = Array.isArray(data.test_results) ? data.test_results : [];
                
                // Process test results one by one with a small delay for visual feedback
                for (let i = 0; i < testResultsArray.length; i++) {
                    testResults[i] = testResultsArray[i];
                    showTestCase(i);
                    await new Promise(resolve => setTimeout(resolve, 300)); // 300ms delay between tests
                }
                
                updateTestResults();
                
                // Show success/failure message
                const testsPassedCount = data.tests_passed || 0;
                const totalTestsCount = data.total_tests || testResultsArray.length;
                
                if (testsPassedCount === totalTestsCount) {
                    showResultsNotification('Success', 'All test cases passed! Try submitting your solution.', 'success');
                } else {
                    const failedTests = totalTestsCount - testsPassedCount;
                    const failMessage = `${testsPassedCount} out of ${totalTestsCount} test cases passed. ${failedTests} test${failedTests > 1 ? 's' : ''} failed.`;
                    showResultsNotification('Warning', failMessage, 'warning');
                }
            } else {
                testResults = [];  // Reset test results on error
                updateTestResults();
                showResultsNotification('Error', data.error || 'Failed to run tests', 'error');
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                showResultsNotification('Error', 'Test execution timed out. Please try again.', 'error');
            } else {
                throw error;
            }
        }

    } catch (error) {
        console.error('Error running tests:', error);
        testResults = [];  // Reset test results on error
        updateTestResults();
        showResultsNotification('Error', 'Failed to run tests: ' + error.message, 'error');
    } finally {
        // Always restore button state
        restoreButton();
    }
}

// Helper function to update test results in the UI
function updateTestResults() {
    if (!testResults) {
        testResults = [];  // Initialize if undefined
    }
    
    // Update test panel for each test case
    testCases.forEach((_, index) => {
        showTestCase(index);
    });
    
    // Update overall test status
    const passedTests = testResults.filter(result => result && result.passed).length;
    const totalTests = testResults.length;
    const testStatusElement = document.getElementById('testStatus');
    if (testStatusElement) {
        testStatusElement.innerHTML = `${passedTests}/${totalTests} tests passed`;
        testStatusElement.className = passedTests === totalTests ? 'success' : 'warning';
    }
}

// Get elapsed time in seconds
function getElapsedTime() {
    return Math.floor((Date.now() - startTime) / 1000);
}