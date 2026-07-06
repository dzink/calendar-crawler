/*
 * theme.js — Dark/light theme toggle.
 */

var THEME_DARK_CLASS = 'dark';
var THEME_LIGHT_CLASS = 'light';

function updateThemeToggle(on) {
  var btn = document.getElementById('theme-toggle');
  btn.className = on ? THEME_LIGHT_CLASS : THEME_DARK_CLASS;
  btn.querySelector('.hidden').textContent = on ? 'Switch to dark theme' : 'Switch to light theme';
}

function toggleTheme() {
  document.body.classList.toggle('stage-theme');
  var on = document.body.classList.contains('stage-theme');
  localStorage.setItem('stage-theme', on ? '1' : '');
  updateThemeToggle(on);
}
(function() {
  if (localStorage.getItem('stage-theme') === '1') {
    document.body.classList.add('stage-theme');
    updateThemeToggle(true);
  }
})();
