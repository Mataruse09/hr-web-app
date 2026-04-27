// ── Benefits Dropdown ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const benefitsLink = document.getElementById('benefits-link');
  const benefitsDropdown = document.getElementById('benefits-dropdown');
  if (benefitsLink && benefitsDropdown) {
    benefitsLink.addEventListener('click', function (e) {
      e.preventDefault();
      // Toggle dropdown
      if (benefitsDropdown.style.display === 'block') {
        benefitsDropdown.style.display = 'none';
      } else {
        benefitsDropdown.style.display = 'block';
        // Hide after 2.5s
        setTimeout(function(){
          benefitsDropdown.style.display = 'none';
        }, 2500);
      }
    });
    // Hide dropdown if click outside
    document.addEventListener('click', function(e) {
      if (!benefitsDropdown.contains(e.target) && e.target !== benefitsLink) {
        benefitsDropdown.style.display = 'none';
      }
    });
  }
});
// Sidebar toggle for mobile
function toggleSidebar() {
  var sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}
/* ================================================================
   MatinexHR ERP — Main JavaScript
   ================================================================ */

// ── Live Clock ────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
  }) + '  ' + now.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'
  });
}
updateClock();
setInterval(updateClock, 1000);

// ── Sidebar Toggle (Mobile) ───────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.toggle('open');
}

// Click outside sidebar to close on mobile
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (
    sidebar &&
    sidebar.classList.contains('open') &&
    !sidebar.contains(e.target) &&
    toggle && !toggle.contains(e.target)
  ) {
    sidebar.classList.remove('open');
  }
});

// ── Auto-dismiss flash alerts ────────────────────────────────────
(function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity .5s';
      alert.style.opacity    = '0';
      setTimeout(function () { alert.remove(); }, 500);
    }, 4500);
  });
})();

// ── Password Toggle (Show/Hide) ──────────────────────────────────
function togglePassword(button) {
  event.preventDefault();
  const wrapper = button.closest('.password-wrapper');
  const input = wrapper.querySelector('.password-input');
  const eyeIcon = button.querySelector('.eye-icon');
  
  if (input.type === 'password') {
    input.type = 'text';
    eyeIcon.textContent = '👁️‍🗨️';
  } else {
    input.type = 'password';
    eyeIcon.textContent = '👁️';
  }
}


// ── Confirm deletes ───────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(function (el) {
  el.addEventListener('click', function (e) {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// ── Highlight active nav based on pathname ────────────────────────
(function () {
  const path  = window.location.pathname;
  const items = document.querySelectorAll('.nav-item');
  items.forEach(function (item) {
    const href = item.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') {
      item.classList.add('active');
    }
  });
})();

// ── Table Row Click → first link ─────────────────────────────────
document.querySelectorAll('.data-table tbody tr').forEach(function (row) {
  const link = row.querySelector('a.link-name');
  if (link) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function (e) {
      if (!e.target.closest('a, button, input, select, form')) {
        window.location.href = link.href;
      }
    });
  }
});

// ── Smooth scroll for anchor links ────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
  anchor.addEventListener('click', function (e) {
    const targetId = this.getAttribute('href');
    if (targetId === '#') return;
    const target = document.querySelector(targetId);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ── Add loading state to buttons ─────────────────────────────────
document.querySelectorAll('form').forEach(function (form) {
  form.addEventListener('submit', function (e) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn && !submitBtn.disabled) {
      submitBtn.disabled = true;
      submitBtn.dataset.originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '⏳ Processing...';
      setTimeout(function () {
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtn.dataset.originalText;
      }, 3000);
    }
  });
});

// ── Number counter animation for KPI values ─────────────────────
function animateValue(element, start, end, duration) {
  if (!element) return;
  let startTimestamp = null;
  const step = function (timestamp) {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const value = Math.floor(progress * (end - start) + start);
    element.textContent = value;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

// ── Navbar Dropdown/Tooltip for Inactive Buttons ───────────────
document.addEventListener('DOMContentLoaded', function () {
  const navDropdown = document.getElementById('nav-dropdown');
  // List of nav links that have no section to show
  const dropdownLinks = [
    'Modules',
    'Pricing',
    'About'
  ];
  document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
    const text = link.textContent.trim();
    if (dropdownLinks.includes(text)) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        // Show dropdown/tooltip near the button
        const rect = link.getBoundingClientRect();
        navDropdown.style.left = (rect.left + window.scrollX + rect.width/2 - 70) + 'px';
        navDropdown.style.top = (rect.bottom + window.scrollY + 8) + 'px';
        navDropdown.style.display = 'block';
        navDropdown.style.opacity = '1';
        navDropdown.textContent = 'Coming Soon';
        setTimeout(function () {
          navDropdown.style.opacity = '0';
          setTimeout(function(){navDropdown.style.display = 'none';}, 200);
        }, 1400);
      });
    }
    // For demo: show alert for Get Started
    if (text === 'Get Started') {
      link.addEventListener('click', function (e) {
        // Allow default navigation, but show a message
        alert('Redirecting to registration!');
      });
    }
    // For demo: show alert for Login
    if (text === 'Login') {
      link.addEventListener('click', function (e) {
        // Allow default navigation, but show a message
        alert('Redirecting to login!');
      });
    }
  });
});

// Animate KPI values on page load
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.kpi-value').forEach(function (el) {
    const text = el.textContent.trim();
    const match = text.match(/^(\d+)/);
    if (match) {
      const num = parseInt(match[1]);
      if (num > 0) {
        el.textContent = '0';
        animateValue(el, 0, num, 1500);
      }
    }
  });
});