const text = "Welcome Back!";
const container = document.getElementById("typewriter-text");

let i = 0;
function type() {
  if (i < text.length) {
    const char = text.charAt(i);
    const span = document.createElement("span");

    span.classList.add("glitch-letter");

    if (char === " ") {
      span.innerHTML = "&nbsp;";
      span.setAttribute("data-char", " ");
    } else {
      span.textContent = char;
      span.setAttribute("data-char", char);
    }

    container.appendChild(span);
    i++;
    setTimeout(type, 200);
  }
}

window.onload = type;

// Simple login functionality
document.addEventListener('DOMContentLoaded', function() {
  const form = document.querySelector('.login-form');
  if (!form) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = form.username.value.trim();
    const password = form.password.value;
    
    if (!username || !password) {
      alert('Please enter both username and password.');
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
        alert(data.error || 'Login failed.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  });
});
