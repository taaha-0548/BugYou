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

// --- LOGIN FORM HANDLING ---
document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.login-form');
  if (!form) return;

  // Remove any previous error divs
  const oldUserError = document.getElementById('username-error');
  if (oldUserError) oldUserError.remove();
  const oldPassError = document.getElementById('password-error');
  if (oldPassError) oldPassError.remove();
  const usernameInput = form.querySelector('#username');
  const passwordInput = form.querySelector('#password');

  // Create error containers below each input
  let userErrorDiv = document.createElement('div');
  userErrorDiv.id = 'username-error';
  userErrorDiv.style.color = 'red';
  userErrorDiv.style.fontWeight = 'bold';
  userErrorDiv.style.fontSize = '0.6rem';
  userErrorDiv.style.marginTop = '2px';
  usernameInput.parentNode.appendChild(userErrorDiv);

  let passErrorDiv = document.createElement('div');
  passErrorDiv.id = 'password-error';
  passErrorDiv.style.color = 'red';
  passErrorDiv.style.fontWeight = 'bold';
  passErrorDiv.style.fontSize = '0.6rem';
  passErrorDiv.style.marginTop = '2px';
  passwordInput.parentNode.appendChild(passErrorDiv);

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    userErrorDiv.textContent = '';
    passErrorDiv.textContent = '';
    const username = form.username.value.trim();
    const password = form.password.value;
    if (!username || !password) {
      if (!username) userErrorDiv.textContent = 'Enter username.';
      if (!password) passErrorDiv.textContent = 'Enter password.';
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
        window.location.href = '/home';
      } else {
        if (data.error && data.error.toLowerCase().includes('no account')) {
          userErrorDiv.textContent = 'No account found.';
        } else if (data.error && data.error.toLowerCase().includes('password')) {
          passErrorDiv.textContent = 'Wrong password.';
        } else {
          // fallback
          passErrorDiv.textContent = data.error || 'Login failed.';
        }
      }
    } catch (err) {
      passErrorDiv.textContent = 'Network error.';
    }
  });
});
