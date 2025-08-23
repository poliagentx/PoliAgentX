const slider = document.getElementById("slider");
  const display = document.getElementById("slider-value");

  // Show live slider value
  slider.addEventListener("input", function () {
    display.textContent = parseFloat(this.value).toFixed(2);
  });

  // Disable double clicks while calibration runs
  const form = document.getElementById("calibration-form");
  form.addEventListener("submit", () => {
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Calibrating...";
  });