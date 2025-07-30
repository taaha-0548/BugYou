// Login functionality

// Enhanced login functionality with comprehensive validation
document.addEventListener('DOMContentLoaded', function() {
  const form = document.querySelector('.login-form');
  const errorElement = document.getElementById('login-error');
  if (!form) return;

  function showError(message) {
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    setTimeout(() => {
      errorElement.style.display = 'none';
    }, 5000);
  }

  function hideError() {
    errorElement.style.display = 'none';
  }

  // Validation functions
  function validateUsername(username) {
    if (username.length < 1) {
      return 'Enter username.';
    }
    if (username.length > 50) {
      return 'Username too long.';
    }
    return null;
  }

  function validatePassword(password) {
    if (password.length < 1) {
      return 'Enter password.';
    }
    if (password.length > 100) {
      return 'Password too long.';
    }
    return null;
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    hideError();
    
    const username = form.username.value.trim();
    const password = form.password.value;
    
    // Check for empty fields
    if (!username || !password) {
      showError('Enter username and password.');
      return;
    }
    
    // Validate username
    const usernameError = validateUsername(username);
    if (usernameError) {
      showError(usernameError);
      return;
    }
    
    // Validate password
    const passwordError = validatePassword(password);
    if (passwordError) {
      showError(passwordError);
      return;
    }
    
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await res.json();
      
      if (data.success) {
        // Store user data
        localStorage.setItem('currentUser', username);
        window.location.href = '/';
      } else {
        // Handle specific backend errors
        if (data.error && data.error.toLowerCase().includes('no account found')) {
          showError('Username not found.');
        } else if (data.error && data.error.toLowerCase().includes('incorrect password')) {
          showError('Incorrect password.');
        } else if (data.error && data.error.toLowerCase().includes('account')) {
          showError('Account not found.');
        } else if (data.error && data.error.toLowerCase().includes('locked')) {
          showError('Account locked.');
        } else {
          showError(data.error || 'Login failed.');
        }
      }
    } catch (err) {
      showError('Network error. Check connection.');
    }
  });
});
