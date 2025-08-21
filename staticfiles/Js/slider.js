  const slider = document.getElementById("slider");
  const display = document.getElementById("slider-value");

  slider.addEventListener("input", function () {
    display.textContent = parseFloat(this.value).toFixed(2);
  });