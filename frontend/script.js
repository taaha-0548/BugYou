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

function showTestCase(index) {
    const testInputDisplay = document.getElementById('testInputDisplay');
    const testExpectedDisplay = document.getElementById('testExpectedDisplay');
    const testActualDisplay = document.getElementById('testActualDisplay');
    const testResultBadge = document.getElementById('testResultBadge');
    const actualOutputSection = document.getElementById('actualOutputSection');
    
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
    document.getElementById('runAllTests').addEventListener('click', runTests);
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
    body.classList.remove('theme-basic', 'theme-intermediate', 'theme-expert');
    
    // Apply new theme based on difficulty
    switch (difficulty.toLowerCase()) {
        case 'basic':
            body.classList.add('theme-basic');
            break;
        case 'intermediate':
            body.classList.add('theme-intermediate');
            break;
        case 'advanced':
        case 'expert':
            body.classList.add('theme-expert');
            break;
        default:
            body.classList.add('theme-basic');
            break;
    }
}

// Show hint functionality
function showHint() {
    if (hintsUsed < 3 && currentChallenge) {
        hintsUsed++;
        score = Math.max(0, score - 2);
        updateScore();
        
        let hintText = "";
        if (hintsUsed === 1 && currentChallenge.hint_1) {
            hintText = currentChallenge.hint_1;
        } else if (hintsUsed === 2 && currentChallenge.hint_2) {
            hintText = currentChallenge.hint_2;
        } else if (hintsUsed === 3 && currentChallenge.hint_3) {
            hintText = currentChallenge.hint_3;
        } else {
            const fallbackHints = {
                python: [
                    "Hint 1: What happens when you divide by zero? You need to handle empty lists somehow!",
                    "Hint 2: Multiple approaches work: if/else check, try/catch, or using built-in functions. Pick your style!",
                    "Hint 3: Focus on the OUTPUT: empty list should return 0. How you achieve this is up to you!"
                ],
                javascript: [
                    "Hint 1: Starting with max = 0 fails for negative-only arrays. Think about better initialization!",
                    "Hint 2: Many solutions exist: arr[0], Math.max(...arr), reduce, etc. Choose what feels natural!",
                    "Hint 3: Focus on correct OUTPUT: your solution is valid if it passes all test cases!"
                ],
                java: [
                    "Hint 1: Starting with min = 0 fails for negative-only arrays. Think about better initialization!",
                    "Hint 2: Try initializing min with the first element of the array instead of 0!",
                    "Hint 3: What if you set min = numbers[0] and start the loop from index 1?"
                ],
                cpp: [
                    "Hint 1: Look at the loop condition. What happens when i equals numbers.size()?",
                    "Hint 2: Arrays/vectors are zero-indexed. If size is 5, valid indices are 0-4, not 0-5!",
                    "Hint 3: Change <= to < in the for loop condition. Multiple solutions work!"
                ]
            };
            hintText = fallbackHints[currentLanguage]?.[hintsUsed - 1] || "No more hints available!";
        }
        
        showHintModal(hintText);
        
        const hintBtn = document.getElementById('hintBtn');
        if (hintsUsed >= 3) {
            hintBtn.disabled = true;
            hintBtn.innerHTML = '<i class="fas fa-lightbulb"></i>No More Hints';
        } else {
            hintBtn.innerHTML = `<i class="fas fa-lightbulb"></i>Hint (-2 pts) [${3 - hintsUsed} left]`;
        }
    } else if (hintsUsed >= 3) {
        showResultsNotification('No More Hints', 'You have used all available hints for this challenge.', 'warning');
    }
}

// Update score display
function updateScore() {
    document.getElementById('scoreValue').textContent = score;
}

// Run test cases
async function runTests() {
    if (!currentChallenge) {
        showResultsNotification('Challenge Loading', 'Please wait for challenge to load...', 'warning');
        return;
    }
    
    attempts++;
    testResults = []; // Clear previous results
    
    const runButton = document.getElementById('runCode');
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>Running...';
    
    let passedTests = 0;
    let totalTests = testCases.length;
    
    // Run each test case
    for (let i = 0; i < testCases.length; i++) {
        try {
            const testCase = testCases[i];
            let testCode = editor.getValue() + '\n\n';
            const functionName = extractFunctionName(editor.getValue(), currentLanguage);
            
            if (currentLanguage === 'python') {
                testCode += `# Test case ${i + 1}\nresult = ${functionName}(${testCase.input})\nprint(result)`;
            } else if (currentLanguage === 'javascript') {
                testCode += `// Test case ${i + 1}\nconst result = ${functionName}(${testCase.input});\nconsole.log(result);`;
            } else if (currentLanguage === 'java') {
                const javaInput = testCase.input.replace(/\[/g, '{').replace(/\]/g, '}');
                testCode += `\npublic static void main(String[] args) {\n    int[] testArray = ${javaInput};\n    int result = ${functionName}(testArray);\n    System.out.println(result);\n}`;
            } else if (currentLanguage === 'cpp') {
                const cppInput = testCase.input.replace(/\[/g, '{').replace(/\]/g, '}');
                testCode += `\nint main() {\n    vector<int> testArray = ${cppInput};\n    int result = ${functionName}(testArray);\n    cout << result << endl;\n    return 0;\n}`;
            }
            
            const result = await executeCode(testCode);
            const output = (result.run.stdout || '').trim();
            const error = result.run.stderr || '';
            
            let actualOutput = output;
            let passed = false;
            
            if (error) {
                actualOutput = `Error: ${error}`;
                passed = false;
            } else {
                // Compare output with expected
                const expected = testCase.expected_output.toString().trim();
                passed = output === expected;
                if (passed) passedTests++;
            }
            
            testResults[i] = {
                passed: passed,
                actual_output: actualOutput,
                expected_output: testCase.expected_output
            };
            
        } catch (error) {
            testResults[i] = {
                passed: false,
                actual_output: `Error: ${error.message}`,
                expected_output: testCases[i].expected_output
            };
        }
    }
    
    // Update UI
    updateActiveTestCaseButton();
    showTestCase(currentTestCase);
    
    // Update test summary
    const passedCount = document.querySelector('.passed-count');
    const totalCount = document.querySelector('.total-count');
    const testSummary = document.getElementById('testSummary');
    
    if (passedCount) passedCount.textContent = passedTests;
    if (totalCount) totalCount.textContent = totalTests;
    
    // Show test summary when there are results
    if (testSummary && testResults.length > 0) {
        testSummary.style.display = 'block';
    }
    
    // Re-enable run button
    runButton.disabled = false;
    runButton.innerHTML = '<i class="fas fa-play"></i>Run';
    
    // Show brief notification in top-right corner
    if (passedTests === totalTests) {
        showResultsNotification('All Tests Passed!', `Great job! All ${totalTests} test cases passed.`, 'success');
    } else {
        showResultsNotification('Tests Completed', `${passedTests}/${totalTests} test cases passed. Keep trying!`, 'warning');
    }
}

// Run all tests (visible + hidden) and submit
async function runAllTestsAndSubmit() {
    if (!currentChallenge) {
        showResultsNotification('Challenge Loading', 'Please wait for challenge to load...', 'warning');
        return;
    }
    
    const submitBtn = document.getElementById('submitCode');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>Running All Tests...';
    
    let allTestResults = [];
    let visibleTestsPassed = 0;
    let hiddenTestsPassed = 0;
    let totalTests = 0;
    
    try {
        // First run visible test cases (same as runTests)
        testResults = []; // Clear previous results
        totalTests = testCases.length;
        
        showResultsNotification('Testing Phase 1', 'Running visible test cases...', 'warning');
        
        for (let i = 0; i < testCases.length; i++) {
            const testCase = testCases[i];
            const result = await runSingleTest(testCase, i + 1);
            testResults[i] = result;
            allTestResults.push(result);
            if (result.passed) visibleTestsPassed++;
        }
        
        // Update UI with visible test results
        updateActiveTestCaseButton();
        showTestCase(currentTestCase);
        
        // Update test summary
        const passedCount = document.querySelector('.passed-count');
        const totalCount = document.querySelector('.total-count');
        const testSummary = document.getElementById('testSummary');
        
        if (passedCount) passedCount.textContent = visibleTestsPassed;
        if (totalCount) totalCount.textContent = testCases.length;
        if (testSummary) testSummary.style.display = 'block';
        
        // Now run hidden test cases
        const hiddenTests = [];
        for (let i = 1; i <= 2; i++) {
            const hiddenInput = currentChallenge[`hidden_test_${i}_input`];
            const hiddenExpected = currentChallenge[`hidden_test_${i}_expected`];
            if (hiddenInput && hiddenExpected) {
                hiddenTests.push({
                    input: hiddenInput,
                    expected_output: hiddenExpected,
                    description: `Hidden test ${i}`
                });
            }
        }
        
        if (hiddenTests.length > 0) {
            showResultsNotification('Testing Phase 2', `Running ${hiddenTests.length} hidden test cases...`, 'warning');
            
            for (let i = 0; i < hiddenTests.length; i++) {
                const hiddenTest = hiddenTests[i];
                const result = await runSingleTest(hiddenTest, `H${i + 1}`);
                allTestResults.push(result);
                if (result.passed) hiddenTestsPassed++;
            }
        }
        
        totalTests = testCases.length + hiddenTests.length;
        const totalPassed = visibleTestsPassed + hiddenTestsPassed;
        
        // Show comprehensive results
        showResultsNotification('All Tests Complete', 
            `Results: ${visibleTestsPassed}/${testCases.length} visible, ${hiddenTestsPassed}/${hiddenTests.length} hidden tests passed`, 
            totalPassed === totalTests ? 'success' : 'warning');
        
        // Update score based on test results
        const testPassPercentage = totalTests > 0 ? totalPassed / totalTests : 0;
        if (testPassPercentage === 1.0) {
            // All tests passed - keep current score
        } else if (testPassPercentage >= 0.8) {
            score = Math.max(score - 2, 1); // Small penalty
        } else if (testPassPercentage >= 0.6) {
            score = Math.max(score - 4, 1); // Medium penalty
        } else {
            score = Math.max(score - 6, 1); // Large penalty
        }
        updateScore();
        
        // Now submit with comprehensive test results
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>Submitting...';
        
        const response = await fetch(`${API_BASE}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                challenge_id: currentChallengeId,
                language: currentLanguage,
                difficulty: currentDifficulty,
                code: editor.getValue(),
                score: score,
                attempts: attempts,
                hints_used: hintsUsed,
                elapsed_time: getElapsedTime(),
                visible_tests_passed: visibleTestsPassed,
                visible_tests_total: testCases.length,
                hidden_tests_passed: hiddenTestsPassed,
                hidden_tests_total: hiddenTests.length,
                all_tests_passed: totalPassed,
                all_tests_total: totalTests
            })
        });
        
        const data = await response.json();
        
        // Enhance submission data with test results
        data.visible_tests_passed = visibleTestsPassed;
        data.visible_tests_total = testCases.length;
        data.hidden_tests_passed = hiddenTestsPassed;
        data.hidden_tests_total = hiddenTests.length;
        data.total_tests_passed = totalPassed;
        data.total_tests = totalTests;
        
        showSubmissionModal(data);
        
    } catch (error) {
        showSubmissionModal({
            success: false,
            error: `Error during testing/submission: ${error.message}`
        });
    }
    
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>Submit';
}

// Helper function to run a single test case
async function runSingleTest(testCase, testNumber) {
    try {
        let testCode = editor.getValue() + '\n\n';
        const functionName = extractFunctionName(editor.getValue(), currentLanguage);
        
        if (currentLanguage === 'python') {
            testCode += `# Test case ${testNumber}\nresult = ${functionName}(${testCase.input})\nprint(result)`;
        } else if (currentLanguage === 'javascript') {
            testCode += `// Test case ${testNumber}\nconst result = ${functionName}(${testCase.input});\nconsole.log(result);`;
        } else if (currentLanguage === 'java') {
            const javaInput = testCase.input.replace(/\[/g, '{').replace(/\]/g, '}');
            testCode += `\npublic static void main(String[] args) {\n    int[] testArray = ${javaInput};\n    int result = ${functionName}(testArray);\n    System.out.println(result);\n}`;
        } else if (currentLanguage === 'cpp') {
            const cppInput = testCase.input.replace(/\[/g, '{').replace(/\]/g, '}');
            testCode += `\nint main() {\n    vector<int> testArray = ${cppInput};\n    int result = ${functionName}(testArray);\n    cout << result << endl;\n    return 0;\n}`;
        }
        
        const result = await executeCode(testCode);
        const output = (result.run.stdout || '').trim();
        const error = result.run.stderr || '';
        
        let actualOutput = output;
        let passed = false;
        
        if (error) {
            actualOutput = `Error: ${error}`;
            passed = false;
        } else {
            const expected = testCase.expected_output.toString().trim();
            passed = output === expected;
        }
        
        return {
            passed: passed,
            actual_output: actualOutput,
            expected_output: testCase.expected_output
        };
        
    } catch (error) {
        return {
            passed: false,
            actual_output: `Error: ${error.message}`,
            expected_output: testCase.expected_output
        };
    }
}

// Submit code (now calls the comprehensive testing function)
async function submitCode() {
    await runAllTestsAndSubmit();
}

// Get elapsed time
function getElapsedTime() {
    return Math.floor((Date.now() - startTime) / 1000);
}

// Execute code using Piston API
async function executeCode(code) {
    const languageMap = {
        'python': 'python',
        'javascript': 'javascript',
        'java': 'java',
        'cpp': 'cpp'
    };
    
    const response = await fetch('https://emkc.org/api/v2/piston/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            language: languageMap[currentLanguage],
            version: '*',
            files: [{
                content: code
            }]
        })
    });
    
    return await response.json();
}

// Load current challenge from database
async function loadCurrentChallenge() {
    try {
        const response = await fetch(`${API_BASE}/challenge/${currentLanguage}/${currentDifficulty}/${currentChallengeId}`);
        const data = await response.json();
        
        if (data.success) {
            currentChallenge = data.challenge;
            // Update currentDifficulty based on actual challenge data
            if (currentChallenge.difficulty) {
                currentDifficulty = currentChallenge.difficulty;
            }
            updateChallengeDisplay();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Error loading challenge:', error);
        alert('Error connecting to server. Please check if the server is running.');
    }
}

// Update challenge display with loaded data
function updateChallengeDisplay() {
    if (!currentChallenge) return;
    
    const challengeTitle = document.getElementById('challengeTitle');
    if (challengeTitle) {
        challengeTitle.textContent = currentChallenge.title;
    }
    
    const challengeDescription = document.getElementById('challengeDescription');
    if (challengeDescription) {
        challengeDescription.textContent = currentChallenge.description;
    }
    
    const challengeProblem = document.getElementById('challengeProblem');
    if (challengeProblem) {
        challengeProblem.innerHTML = currentChallenge.problem_statement || currentChallenge.description;
    }
    
    const challengeTips = document.getElementById('challengeTips');
    if (challengeTips) {
        challengeTips.innerHTML = currentChallenge.tips || 'Loading task details...';
    }
    
    const difficultyBadge = document.getElementById('difficultyBadge');
    if (difficultyBadge) {
        difficultyBadge.textContent = currentChallenge.difficulty?.toUpperCase() || 'BASIC';
    }
    
    // Apply theme based on difficulty
    applyTheme(currentChallenge.difficulty || 'basic');
    
    if (editor && currentChallenge.buggy_code) {
        editor.setValue(currentChallenge.buggy_code);
    }
    
    updateTestCasesDisplay();
    updateHintsDisplay();
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

// Update hints display
function updateHintsDisplay() {
    const hintBtn = document.getElementById('hintBtn');
    if (currentChallenge && currentChallenge.hint_1) {
        hintBtn.style.display = 'inline-flex';
    } else {
        hintBtn.style.display = 'none';
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