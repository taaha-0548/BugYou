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
