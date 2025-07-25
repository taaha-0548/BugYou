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

// Simple signup functionality
document.addEventListener('DOMContentLoaded', function() {
  const form = document.querySelector('.signup-form');
  if (!form) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fullname = form.fullname.value.trim();
    const email = form.email.value.trim();
    const username = form.username.value.trim();
    const password = form.password.value;
    
    if (!fullname || !email || !username || !password) {
      alert('Please fill in all fields.');
      return;
    }
    
    try {
      const res = await fetch('https://bug-you-4frc-2qzzj8dse-muhammad-taahas-projects.vercel.app/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fullname, email, username, password })
      });
      
      const data = await res.json();
      
      if (data.success) {
        // Store user data
        localStorage.setItem('currentUser', username);
        window.location.href = '/';
      } else {
        alert(data.error || 'Signup failed.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  });
});
