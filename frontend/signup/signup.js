const text = "Join  us";
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

// --- SIGNUP FORM HANDLING ---
document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.signup-form');
  if (!form) return;

  // Remove any previous error divs
  const oldNameError = document.getElementById('fullname-error');
  if (oldNameError) oldNameError.remove();
  const oldEmailError = document.getElementById('email-error');
  if (oldEmailError) oldEmailError.remove();
  const oldUserError = document.getElementById('username-error');
  if (oldUserError) oldUserError.remove();
  const oldPassError = document.getElementById('password-error');
  if (oldPassError) oldPassError.remove();

  const fullnameInput = form.querySelector('#fullname');
  const emailInput = form.querySelector('#email');
  const usernameInput = form.querySelector('#username');
  const passwordInput = form.querySelector('#password');

  // Create error containers below each input
  let nameErrorDiv = document.createElement('div');
  nameErrorDiv.id = 'fullname-error';
  nameErrorDiv.style.color = 'red';
  nameErrorDiv.style.fontWeight = 'bold';
  nameErrorDiv.style.fontSize = '0.6rem';
  nameErrorDiv.style.marginTop = '2px';
  fullnameInput.parentNode.appendChild(nameErrorDiv);

  let emailErrorDiv = document.createElement('div');
  emailErrorDiv.id = 'email-error';
  emailErrorDiv.style.color = 'red';
  emailErrorDiv.style.fontWeight = 'bold';
  emailErrorDiv.style.fontSize = '0.6rem';
  emailErrorDiv.style.marginTop = '2px';
  emailInput.parentNode.appendChild(emailErrorDiv);

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
    nameErrorDiv.textContent = '';
    emailErrorDiv.textContent = '';
    userErrorDiv.textContent = '';
    passErrorDiv.textContent = '';
    const fullname = form.fullname.value.trim();
    const email = form.email.value.trim();
    const username = form.username.value.trim();
    const password = form.password.value;
    // Show error below the first empty field
    if (!fullname) { nameErrorDiv.textContent = 'Please fill in all fields.'; return; }
    if (!email) { emailErrorDiv.textContent = 'Please fill in all fields.'; return; }
    if (!username) { userErrorDiv.textContent = 'Please fill in all fields.'; return; }
    if (!password) { passErrorDiv.textContent = 'Please fill in all fields.'; return; }
    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fullname, email, username, password })
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = '/home';
      } else {
        if (data.error && data.error.toLowerCase().includes('username')) {
          userErrorDiv.textContent = 'Username already exists.';
        } else if (data.error && data.error.toLowerCase().includes('email')) {
          emailErrorDiv.textContent = data.error;
        } else {
          // fallback: show on password field
          passErrorDiv.textContent = data.error || 'Signup failed.';
        }
      }
    } catch (err) {
      passErrorDiv.textContent = 'Network error.';
    }
  });
});
