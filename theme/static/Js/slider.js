
const slider = document.getElementById("slider");
const display = document.getElementById("slider-value");
const qualityLabel = document.getElementById("quality-label");
const currentQuality = document.getElementById("current-quality");
const form = document.getElementById("calibration-form");
const startBtn = document.getElementById("start-calibration-button");
const processingState = document.getElementById("processing-state");
const nextButtonContainer = document.getElementById("next-button-container");
const disabledNext = document.getElementById("next-disabled");

let isSubmitting = false;

// Update quality label dynamically
function updateQualityLabel(value) {
    const numValue = parseFloat(value);
    if (numValue <= 0.30) {
        qualityLabel.className = "quality-indicator quality-low";
        qualityLabel.textContent = "Quick Test";
    } else if (numValue <= 0.70) {
        qualityLabel.className = "quality-indicator quality-medium";
        qualityLabel.textContent = "Balanced";
    } else {
        qualityLabel.className = "quality-indicator quality-high";
        qualityLabel.textContent = "High Precision";
    }
}

// Show live slider value
slider.addEventListener("input", function () {
    const value = parseFloat(this.value).toFixed(2);
    display.textContent = value;
    currentQuality.textContent = value;
    updateQualityLabel(this.value);
});

// Initialize on load
updateQualityLabel(slider.value);

form.addEventListener("submit", function (e) {
    e.preventDefault(); // Prevent actual form submission

    if (isSubmitting) return; // Prevent double-clicks
    isSubmitting = true;

    // Show "calibrating..." state
    startBtn.style.display = "none";
    processingState.classList.remove("hidden");

    // Simulate calibration (adjust time as needed)
    setTimeout(() => {
        processingState.classList.add("hidden");          // Hide spinner
        nextButtonContainer.classList.remove("hidden");   // Show NEXT button
        disabledNext.classList.add("hidden");            // Hide disabled notice
    }, 3000); // 3 seconds simulation
});
