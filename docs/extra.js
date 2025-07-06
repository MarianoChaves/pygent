document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.md-typeset h1').forEach(el => {
    const span = document.createElement('span');
    span.className = 'cursor';
    el.appendChild(span);
  });
});
