
function updateEquivalent(value) {
    const years = (value / 50) * 10;
    document.getElementById('time-equivalent').textContent = `Equivalent to ${years.toFixed(1)} years of simulation time`;
    document.getElementById('current-selection').textContent = value;
}

// Handle form submission with loading animation
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const startBtn = document.getElementById('start-btn');
    const processingState = document.getElementById('processing-state');
    const formCard = document.querySelector('.simulation-card');
    let isSubmitting = false;
    
    form.addEventListener('submit', function(e) {
        // Prevent double submission
        if (isSubmitting) {
            e.preventDefault();
            return;
        }
        
        isSubmitting = true;
        
        // Show processing state immediately
        startBtn.style.display = 'none';
        processingState.classList.remove('hidden');
        processingState.classList.add('fade-in');
        
        // Disable the submit button to prevent double clicks
        startBtn.disabled = true;
        
        // Add visual feedback to the card
        formCard.style.opacity = '0.8';
        
        // Let the form submit naturally with CSRF token
        // The processing animation will show while the page loads
    });
});
