// Global client side JS
document.addEventListener("DOMContentLoaded", () => {

    // ── Auto-dismiss flash alert boxes after 5 seconds ──────────────────
    const alerts = document.querySelectorAll('.alert-custom');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // ── SCROLL REVEAL ENGINE (Intersection Observer) ─────────────────────
    // Watches every element with data-reveal attribute.
    // Adds class "revealed" when element enters viewport → CSS does the animation.
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                // Unobserve after reveal so it doesn't re-trigger
                revealObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12,       // Trigger when 12% of element is visible
        rootMargin: '0px 0px -40px 0px'  // Slight bottom offset for natural feel
    });

    // Observe all elements that have a data-reveal attribute
    document.querySelectorAll('[data-reveal]').forEach(el => {
        revealObserver.observe(el);
    });

    // ── NAVBAR SCROLL SHRINK EFFECT ──────────────────────────────────────
    const navbar = document.querySelector('.navbar-custom');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 60) {
                navbar.style.padding = '0.4rem 0';
                navbar.style.backdropFilter = 'blur(24px) saturate(180%)';
                navbar.style.boxShadow = '0 4px 30px rgba(0,0,0,0.35)';
            } else {
                navbar.style.padding = '';
                navbar.style.backdropFilter = '';
                navbar.style.boxShadow = '';
            }
        }, { passive: true });
    }

    // ── SMOOTH ACTIVE NAV HIGHLIGHT ON SCROLL ────────────────────────────
    const sections = document.querySelectorAll('section[id], div[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link[href^="#"]');

    if (sections.length && navLinks.length) {
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === `#${entry.target.id}`) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        }, { threshold: 0.4 });

        sections.forEach(sec => sectionObserver.observe(sec));
    }

    // ── STAT COUNTER ANIMATION (counts up when scrolled into view) ───────
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.counted) {
                    entry.target.dataset.counted = 'true';
                    const rawText = entry.target.textContent.trim();
                    const numMatch = rawText.match(/([\d,]+\.?\d*)/);
                    if (!numMatch) return;

                    const rawNum = parseFloat(numMatch[1].replace(/,/g, ''));
                    const suffix = rawText.replace(numMatch[1], '').trim();
                    const isDecimal = rawNum % 1 !== 0;
                    const duration = 1800;
                    const start = performance.now();

                    const tick = (now) => {
                        const elapsed = now - start;
                        const progress = Math.min(elapsed / duration, 1);
                        // Ease-out cubic
                        const eased = 1 - Math.pow(1 - progress, 3);
                        const current = rawNum * eased;
                        const formatted = isDecimal
                            ? current.toFixed(1)
                            : Math.floor(current).toLocaleString();
                        entry.target.textContent = formatted + suffix;
                        if (progress < 1) requestAnimationFrame(tick);
                    };
                    requestAnimationFrame(tick);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        statNumbers.forEach(el => counterObserver.observe(el));
    }
});
