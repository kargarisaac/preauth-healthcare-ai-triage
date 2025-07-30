// Modern Nazmito Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // FAQ Toggle Functionality
    initializeFAQ();

    // Smooth scroll for navigation links
    initializeSmoothScroll();

    // Navigation scroll effect
    initializeNavScroll();

    // Intersection Observer for animations
    initializeScrollAnimations();

    // Mobile navigation toggle
    initializeMobileNav();
});

// FAQ Toggle
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');

        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');

            // Close all other FAQ items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                    const otherAnswer = otherItem.querySelector('.faq-answer');
                    otherAnswer.style.maxHeight = null;
                }
            });

            // Toggle current item
            if (isActive) {
                item.classList.remove('active');
                answer.style.maxHeight = null;
            } else {
                item.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + 'px';
            }
        });
    });
}

// Smooth scroll for navigation links
function initializeSmoothScroll() {
    const navLinks = document.querySelectorAll('a[href^="#"]');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);

            if (targetSection) {
                const headerOffset = 80;
                const elementPosition = targetSection.offsetTop;
                const offsetPosition = elementPosition - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Navigation scroll effect
function initializeNavScroll() {
    const nav = document.querySelector('.nav');
    let lastScrollTop = 0;

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        // Add/remove scrolled class
        if (scrollTop > 100) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }

        // Hide/show nav on scroll
        if (scrollTop > lastScrollTop && scrollTop > 200) {
            nav.style.transform = 'translateY(-100%)';
        } else {
            nav.style.transform = 'translateY(0)';
        }

        lastScrollTop = scrollTop;
    });
}

// Scroll animations using Intersection Observer
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll(
        '.timeline-card, .value-card, .floating-card, .comparison-card, .security-timeline .timeline-milestone'
    );

    animateElements.forEach(el => {
        observer.observe(el);
    });

    // Add CSS for animations
    addAnimationStyles();
}

// Add animation styles dynamically
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .timeline-card,
        .value-card,
        .floating-card,
        .comparison-card,
        .timeline-milestone {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease-out;
        }

        .timeline-card.animate-in,
        .value-card.animate-in,
        .floating-card.animate-in,
        .comparison-card.animate-in,
        .timeline-milestone.animate-in {
            opacity: 1;
            transform: translateY(0);
        }

        .nav.scrolled {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .nav {
            transition: all 0.3s ease-out;
        }

        .faq-answer {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }

        @media (max-width: 768px) {
            .nav-menu.active {
                display: flex;
                flex-direction: column;
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(20px);
                border-top: 1px solid var(--border-light);
                padding: var(--space-lg);
                gap: var(--space-md);
            }

            .nav-toggle.active span:nth-child(1) {
                transform: rotate(45deg) translate(5px, 5px);
            }

            .nav-toggle.active span:nth-child(2) {
                opacity: 0;
            }

            .nav-toggle.active span:nth-child(3) {
                transform: rotate(-45deg) translate(7px, -6px);
            }
        }
    `;
    document.head.appendChild(style);
}

// Mobile navigation toggle
function initializeMobileNav() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close mobile menu when clicking on a link
        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
    }
}

// Utility function to add stagger animation delays
function addStaggerDelay() {
    const staggerElements = document.querySelectorAll('.value-card, .timeline-item');

    staggerElements.forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
    });
}

// Initialize stagger delays
document.addEventListener('DOMContentLoaded', addStaggerDelay);

// Parallax effect for hero orbs
function initializeParallax() {
    const orbs = document.querySelectorAll('.gradient-orb');

    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;

        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 0.1;
            orb.style.transform = `translateY(${rate * speed}px)`;
        });
    });
}

// Initialize parallax on load
window.addEventListener('load', initializeParallax);

// Form validation and enhancement (if contact form is added later)
function initializeFormEnhancements() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea');

        inputs.forEach(input => {
            // Add floating label effect
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', () => {
                if (!input.value) {
                    input.parentElement.classList.remove('focused');
                }
            });

            // Check if input has value on load
            if (input.value) {
                input.parentElement.classList.add('focused');
            }
        });
    });
}

// Loading animation
function showLoadingAnimation() {
    document.body.classList.add('loading');

    setTimeout(() => {
        document.body.classList.remove('loading');
        document.body.classList.add('loaded');
    }, 1000);
}

// Initialize loading animation
window.addEventListener('load', showLoadingAnimation);

// Add loading styles
const loadingStyles = `
    body.loading * {
        animation-play-state: paused !important;
    }

    body.loaded .hero-content > * {
        animation: slideInUp 0.8s ease-out forwards;
        opacity: 0;
    }

    body.loaded .hero-content > *:nth-child(1) { animation-delay: 0.1s; }
    body.loaded .hero-content > *:nth-child(2) { animation-delay: 0.2s; }
    body.loaded .hero-content > *:nth-child(3) { animation-delay: 0.3s; }
    body.loaded .hero-content > *:nth-child(4) { animation-delay: 0.4s; }
    body.loaded .hero-content > *:nth-child(5) { animation-delay: 0.5s; }

    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;

// Add loading styles to document
const loadingStyleSheet = document.createElement('style');
loadingStyleSheet.textContent = loadingStyles;
document.head.appendChild(loadingStyleSheet);
