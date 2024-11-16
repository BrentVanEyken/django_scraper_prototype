document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('scrape-all-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const scrapeButton = document.getElementById('scrape-all-button');

    form.addEventListener('submit', function(event) {
        // Show the loading overlay
        loadingOverlay.style.display = 'flex';
        
        // Optionally, disable the button to prevent multiple submissions
        scrapeButton.disabled = true;
        scrapeButton.innerText = 'Scraping...';
    });
});