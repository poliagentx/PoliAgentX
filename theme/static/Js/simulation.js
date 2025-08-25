
    
function updateEquivalent(value) {
    const years = (value / 50) * 10;
    document.getElementById('time-equivalent').textContent = `Equivalent to ${years.toFixed(1)} years of simulation time`;
    document.getElementById('current-selection').textContent = value;
}

// Handle form submission with loading animation and Next button logic
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('simulation-form');
    const startBtn = document.getElementById('start-btn');
    const processingState = document.getElementById('processing-state');
    const nextButtonContainer = document.getElementById('next-button-container');
    const disabledNext = document.getElementById('next-disabled');
    const formCard = document.querySelector('.simulation-card');
    let isSubmitting = false;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Prevent double submission
        if (isSubmitting) {
            return;
        }
        
        isSubmitting = true;
        
        // Show processing state immediately
        startBtn.style.display = 'none';
        processingState.classList.remove('hidden');
        processingState.classList.add('fade-in');
        
        // Add visual feedback to the card
        formCard.style.opacity = '0.8';
        
        const formData = new FormData(form);

        fetch("{% url 'results' %}", {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Simulation failed");
            }
            return response.text(); // Django returns HTML
        })
        .then(html => {
            // Simulation finished
            processingState.classList.add("hidden");
            
            // Show Next button
            nextButtonContainer.classList.remove("hidden");
            disabledNext.classList.add("hidden");

            // Optionally: show some results if needed
            const resultsContainer = document.createElement("div");
            resultsContainer.innerHTML = html;
            document.querySelector(".mx-auto").appendChild(resultsContainer);
        })
        .catch(err => {
            alert("Error: " + err.message);
            startBtn.style.display = "block";
            processingState.classList.add("hidden");
            formCard.style.opacity = '1';
            isSubmitting = false;
        });
    });
});

