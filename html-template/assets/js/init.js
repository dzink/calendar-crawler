/*
 * init.js — Show nav and offset content.
 */

(function() {
  nav.classList.add('ready');
  requestAnimationFrame(function() {
    var h = nav.offsetHeight;
    document.querySelector('main').style.paddingTop = h + 'px';
  });
})();
