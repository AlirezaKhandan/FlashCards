// myapp/static/js/homepage.js

// Example: Simple carousel functionality for feature highlights
document.addEventListener('DOMContentLoaded', function() {
    let currentSlide = 0;
    const slides = document.querySelectorAll('.feature-slide');
    const totalSlides = slides.length;

    function showSlide(index) {
        slides.forEach((slide, idx) => {
            slide.classList.toggle('hidden', idx !== index);
        });
    }

    document.getElementById('prev-slide').addEventListener('click', function() {
        currentSlide = (currentSlide === 0) ? totalSlides - 1 : currentSlide - 1;
        showSlide(currentSlide);
    });

    document.getElementById('next-slide').addEventListener('click', function() {
        currentSlide = (currentSlide + 1) % totalSlides;
        showSlide(currentSlide);
    });

    // Initialize the first slide
    showSlide(currentSlide);
});
