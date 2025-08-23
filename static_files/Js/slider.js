  // const slider = document.getElementById("slider");
  // const display = document.getElementById("slider-value");

  // slider.addEventListener("input", function () {
  //   display.textContent = parseFloat(this.value).toFixed(2);
  // });

 
  // /* enable NEXT after successful POST (your existing logic) */
  // const form = document.querySelector('form');
  // const nextBtnContainer = document.getElementById('next-button-container');
  // const nextDisabled = document.getElementById('next-disabled');
  // form.addEventListener('submit', () => {
  //     form.querySelector('button[type="submit"]').disabled = true;
  //     /* on server redirect you can instead set session flag and show NEXT */
  // });


  const slider = document.getElementById("slider");
  const display = document.getElementById("slider-value");

  // Show live slider value
  slider.addEventListener("input", function () {
    display.textContent = parseFloat(this.value).toFixed(2);
  });

  // Handle form submit
  const form = document.querySelector("form");
  const nextBtnContainer = document.getElementById("next-button-container");
  const nextDisabled = document.getElementById("next-disabled");

  form.addEventListener("submit", (e) => {
    // Prevent double clicks
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Processing...";

    // Simulate server response (if you want to test without backend)
    // Remove this block when Django handles redirect + session flag
    setTimeout(() => {
      // Hide disabled "NEXT" and show enabled "NEXT"
      nextDisabled.classList.add("hidden");
      nextBtnContainer.classList.remove("hidden");
    }, 1500);
  });

