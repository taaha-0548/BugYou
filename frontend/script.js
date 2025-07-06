// BugYou Debugging Interface JavaScript

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

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initEditor();
    initTimer();
    initTestCaseNavigation();
    initEventListeners();
    initUIHandlers();
    
    // Apply default theme
    applyTheme('basic');
    
    loadCurrentChallenge();
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
    const testCaseButtons = document.querySelectorAll('.test-case-btn');
    testCaseButtons.forEach((btn, index) => {
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
        // Display input and expected output
        testInputDisplay.innerHTML = `<pre>${testCases[index].input}</pre>`;
        testExpectedDisplay.innerHTML = `<pre>${testCases[index].expected_output}</pre>`;
        
        // Display actual output if test has been run
        if (testResults[index]) {
            actualOutputSection.style.display = 'block';
            testActualDisplay.innerHTML = `<pre>${testResults[index].actual_output}</pre>`;
            testResultBadge.textContent = testResults[index].passed ? 'Passed' : 'Failed';
            testResultBadge.className = `test-result-badge ${testResults[index].passed ? 'passed' : 'failed'}`;
        } else {
            actualOutputSection.style.display = 'none';
            testResultBadge.textContent = 'Not tested';
            testResultBadge.className = 'test-result-badge not-tested';
        }
    }
}

// Initialize event listeners
function initEventListeners() {
    document.getElementById('runCode').addEventListener('click', runTests);
    document.getElementById('submitCode').addEventListener('click', submitCode);
    document.getElementById('hintBtn').addEventListener('click', showHint);
    document.getElementById('language').addEventListener('change', changeLanguage);
    document.getElementById('loadRandomBtn').addEventListener('click', loadRandomChallenge);
    document.getElementById('runAllTests').addEventListener('click', runAllTestsAndSubmit);
    // Results panel run all tests button (class-based)
    document.querySelectorAll('.results-run-all-tests').forEach(btn => {
        btn.addEventListener('click', runAllTestsAndSubmit);
    });
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
    const randomChallengeModal = document.getElementById('randomChallengeModal');
    const randomLanguage = document.getElementById('randomLanguage');
    const randomDifficulty = document.getElementById('randomDifficulty');
    const randomTitle = document.getElementById('randomTitle');
    const randomChallengeIcon = document.getElementById('randomChallengeIcon');
    
    // Set modal content
    randomLanguage.textContent = language.charAt(0).toUpperCase() + language.slice(1);
    randomDifficulty.textContent = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
    randomTitle.textContent = title;
    
    // Set appropriate icon based on difficulty
    const iconMap = {
        'basic': 'fas fa-dice',
        'intermediate': 'fas fa-dice-d6',
        'advanced': 'fas fa-dice-d20',
        'expert': 'fas fa-dice-d20'
    };
    randomChallengeIcon.className = iconMap[difficulty] || 'fas fa-dice';
    
    randomChallengeModal.classList.add('show');
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
    if (!challengeHints || challengeHints.length === 0) {
        hintBtn.style.display = 'none';
        return;
    }
    hintBtn.style.display = 'inline-flex';
    const hintsLeft = challengeHints.length - revealedHints.length;
    if (hintsLeft <= 0) {
        hintBtn.disabled = true;
        hintBtn.innerHTML = '<i class="fas fa-lightbulb"></i>No More Hints';
    } else {
        hintBtn.disabled = false;
        hintBtn.innerHTML = `<i class="fas fa-lightbulb"></i>Hint (-2 pts) [${hintsLeft} left]`;
    }
}

// --- CHALLENGE LOADING: fetch and store hints array, reset revealed hints ---
async function loadCurrentChallenge() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    try {
        const response = await fetch(`${API_BASE}/challenge/${currentLanguage}/${currentDifficulty}/${currentChallengeId}`);
        const data = await response.json();
        if (data.success) {
            currentChallenge = data.challenge;
            // --- HINTS: robustly fetch and store hints array ---
            challengeHints = Array.isArray(currentChallenge.hints) ? currentChallenge.hints : [];
            revealedHints = [];
            hintsUsed = 0;
            updateChallengeDisplay();
            updateHintsSidebar(); // <-- Ensure sidebar is reset after loading
        } else {
            throw new Error(data.error || 'Failed to load challenge');
        }
    } catch (error) {
        console.error('Error loading challenge:', error);
        showResultsNotification('Loading Error', `Failed to load challenge: ${error.message}`, 'error');
    } finally {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
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
    document.getElementById('challengeTitle').textContent = currentChallenge.title;
    document.getElementById('difficultyBadge').textContent = currentChallenge.difficulty.toUpperCase();
    
    // Update description
    document.getElementById('challengeDescription').innerHTML = currentChallenge.description || '';
    
    // Update problem statement with proper newline handling
    const problemStatement = currentChallenge.problem_statement || '';
    const formattedProblem = problemStatement.replace(/\n/g, '<br>');
    document.getElementById('challengeProblem').innerHTML = formattedProblem;
    
    // Update code editor with buggy code
    if (currentChallenge.buggy_code) {
        editor.setValue(currentChallenge.buggy_code);
    }
    
    // Update test cases
    updateTestCasesDisplay();
    
    // Update hints display
    updateHintsDisplay();
    
    // Apply theme based on difficulty
    applyTheme(currentChallenge.difficulty);
    
    // Clear hints list when loading a new challenge
    const hintsList = document.getElementById('hintsList');
    if (hintsList) {
        hintsList.innerHTML = '';
        console.log('Cleared hints list');
    }
    // Ensure hints sidebar is reset and shown appropriately
    updateHintsSidebar();
}

// Update test cases display
function updateTestCasesDisplay() {
    if (!currentChallenge) return;
    
    testCases = [];
    testResults = [];
    
    for (let i = 1; i <= 5; i++) {
        const input = currentChallenge[`test_case_${i}_input`];
        const expected = currentChallenge[`test_case_${i}_expected`];
        const description = currentChallenge[`test_case_${i}_description`];
        
        if (input && expected) {
            testCases.push({
                input: input,
                expected_output: expected,
                description: description || `Test case ${i}`
            });
        }
    }
    
    const testCaseButtons = document.getElementById('testCaseButtons');
    if (testCaseButtons && testCases.length > 0) {
        let buttonsHtml = '';
        testCases.forEach((testCase, index) => {
            buttonsHtml += `<button class="test-case-btn ${index === 0 ? 'active' : ''}" data-case="${index}">Case ${index + 1}</button>`;
        });
        testCaseButtons.innerHTML = buttonsHtml;
        
        initTestCaseNavigation();
        
        currentTestCase = 0;
        showTestCase(0);
        
        const totalCount = document.querySelector('.total-count');
        const passedCount = document.querySelector('.passed-count');
        if (totalCount) totalCount.textContent = testCases.length;
        if (passedCount) passedCount.textContent = '0';
    }
}

// Load random challenge
async function loadRandomChallenge() {
    const randomBtn = document.getElementById('loadRandomBtn');
    const originalText = randomBtn.innerHTML;
    
    randomBtn.disabled = true;
    randomBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>Loading...';
    
    try {
        const response = await fetch(`${API_BASE}/challenge/random/${currentLanguage}`);
        const data = await response.json();
        
        if (data.success) {
            const randomInfo = data.random_info;
            
            currentLanguage = randomInfo.language;
            currentDifficulty = randomInfo.difficulty;
            currentChallengeId = randomInfo.challenge_id;
            currentChallenge = data.challenge;
            
            document.getElementById('language').value = currentLanguage;
            
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
            // --- HINTS: robustly fetch and store hints array ---
            challengeHints = Array.isArray(currentChallenge.hints) ? currentChallenge.hints : [];
            revealedHints = [];
            updateScore();
            
            updateChallengeDisplay();
            
            // Show the random challenge modal instead of alert
            showRandomChallengeModal(currentLanguage, currentDifficulty, currentChallenge.title);
            
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Random challenge loading error:', error);
        showResultsNotification('Loading Failed', `Failed to load random challenge: ${error.message}`, 'error');
    }
    
    randomBtn.disabled = false;
    randomBtn.innerHTML = originalText;
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