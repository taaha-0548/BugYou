// Signup functionality
console.log('Signup script loaded');

// Enhanced signup functionality with comprehensive validation
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM Content Loaded - Signup');
  const form = document.querySelector('.signup-form');
  const errorElement = document.getElementById('signup-error');
  
  console.log('Form found:', !!form);
  console.log('Error element found:', !!errorElement);
  
  if (!form) {
    console.error('Form not found');
    return;
  }
  
  if (!errorElement) {
    console.error('Error element not found');
    return;
  }
  
  // Test button click
  const submitButton = form.querySelector('button[type="submit"]');
  if (submitButton) {
    submitButton.addEventListener('click', function(e) {
      console.log('Button clicked');
    });
  }

  function showError(message) {
    console.log('Showing error:', message);
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
      setTimeout(() => {
        errorElement.style.display = 'none';
      }, 5000);
    } else {
      console.error('Error element not found');
    }
  }

  function hideError() {
    errorElement.style.display = 'none';
  }

  // Validation functions
  function validateFullName(fullname) {
    if (fullname.length < 2) {
      return 'Name too short.';
    }
    if (fullname.length > 50) {
      return 'Name too long.';
    }
    if (!/^[a-zA-Z\s]+$/.test(fullname)) {
      return 'Name can only contain letters and spaces.';
    }
    return null;
  }

  function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return 'Invalid email format.';
    }
    if (email.length > 100) {
      return 'Email too long.';
    }
    return null;
  }

  function validateUsername(username) {
    if (username.length < 3) {
      return 'Username too short.';
    }
    if (username.length > 20) {
      return 'Username too long.';
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return 'Username can only contain letters, numbers, and underscores.';
    }
    return null;
  }

  function validatePassword(password) {
    if (password.length < 6) {
      return 'Password too short.';
    }
    if (password.length > 50) {
      return 'Password too long.';
    }
    if (!/(?=.*[a-z])/.test(password)) {
      return 'Password needs a lowercase letter.';
    }
    if (!/(?=.*[A-Z])/.test(password)) {
      return 'Password needs an uppercase letter.';
    }
    if (!/(?=.*\d)/.test(password)) {
      return 'Password needs a number.';
    }
    return null;
  }

  form.addEventListener('submit', async function(e) {
    console.log('Submit event triggered');
    e.preventDefault();
    console.log('Form submitted');
    hideError();
    
    const fullname = form.fullname.value.trim();
    const email = form.email.value.trim();
    const username = form.username.value.trim();
    const password = form.password.value;
    
    console.log('Form data:', { fullname, email, username, password: '***' });
    
    // Check for empty fields
    if (!fullname || !email || !username || !password) {
      showError('Please fill in all fields.');
      return;
    }
    
    // Validate full name
    const fullNameError = validateFullName(fullname);
    if (fullNameError) {
      showError(fullNameError);
      return;
    }
    
    // Validate email
    const emailError = validateEmail(email);
    if (emailError) {
      showError(emailError);
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
    
    // Check if username contains common reserved words
    const reservedWords = ['admin', 'administrator', 'root', 'system', 'user', 'guest', 'test', 'demo'];
    if (reservedWords.includes(username.toLowerCase())) {
      showError('Username is reserved.');
      return;
    }
    
    // Check if password is too common
    const commonPasswords = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome'];
    if (commonPasswords.includes(password.toLowerCase())) {
      showError('Choose a stronger password.');
      return;
    }
    
    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fullname, email, username, password })
      });
      
      const data = await res.json();
      console.log('API response:', data);
      
      if (data.success) {
        console.log('Signup successful, redirecting...');
        // Store user data
        localStorage.setItem('currentUser', username);
        window.location.href = '/';
      } else {
        console.log('Signup failed, showing error...');
        // Handle specific backend errors
        if (data.error === 'username_exists') {
          showError(data.message || 'Username taken.');
        } else if (data.error === 'email_exists') {
          showError(data.message || 'Email already registered.');
        } else if (data.error && data.error.includes('username')) {
          showError('Username taken.');
        } else if (data.error && data.error.includes('email')) {
          showError('Email already registered.');
        } else {
          showError(data.message || data.error || 'Signup failed.');
        }
      }
    } catch (err) {
      showError('Network error. Check connection.');
    }
  });
});
