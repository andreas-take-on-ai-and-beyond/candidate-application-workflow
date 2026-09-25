// IT Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('IT Dashboard loaded');
    
    // Add smooth scrolling for navigation
    document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add active state to navigation based on scroll position
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('nav a[href^="#"]');
        
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
    
    // Simulate real-time updates (for demo purposes)
    setInterval(() => {
        const statNumbers = document.querySelectorAll('.stat-number');
        // This would be replaced with actual API calls in production
    }, 30000);
});

// Placeholder for chat initialization
window.initITChat = function() {
    console.log('IT Chat initialization placeholder');
    // Chat will be initialized here with the embed code
};

// Made with Bob
