document.addEventListener('DOMContentLoaded', () => {
    // Scroll Reveal Animation
    const reveals = document.querySelectorAll('.reveal');

    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const elementVisible = 150;

        reveals.forEach((reveal) => {
            const elementTop = reveal.getBoundingClientRect().top;
            
            if (elementTop < windowHeight - elementVisible) {
                reveal.classList.add('active');
            }
        });
    };

    window.addEventListener('scroll', revealOnScroll);
    
    // Trigger once on load to reveal elements currently in viewport
    setTimeout(() => {
        revealOnScroll();
    }, 100);

    // Parallax effect for ambient glows
    const glow1 = document.querySelector('.glow-1');
    const glow2 = document.querySelector('.glow-2');

    window.addEventListener('mousemove', (e) => {
        const x = e.clientX / window.innerWidth;
        const y = e.clientY / window.innerHeight;

        if (glow1) {
            glow1.style.transform = `translate(${x * 30}px, ${y * 30}px)`;
        }
        if (glow2) {
            glow2.style.transform = `translate(${x * -30}px, ${y * -30}px)`;
        }
    });
});
