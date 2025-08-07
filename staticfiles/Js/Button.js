document.addEventListener('DOMContentLoaded', function () {
        const nextBtnContainer = document.getElementById('next-button-container');
        const nextDisabled = document.getElementById('next-disabled');

        const budgetInput = document.getElementById('id_budget');
        const inflationInput = document.getElementById('id_inflation_rate');
        const fileInput = document.getElementById('id_government_expenditure');

        function enableNextButton() {
            nextBtnContainer.classList.remove('hidden');
            nextDisabled.classList.add('hidden');
        }

        function disableNextButton() {
            nextBtnContainer.classList.add('hidden');
            nextDisabled.classList.remove('hidden');
        }

        function checkFormCompletion() {
            const isManualFilled = budgetInput?.value.trim() !== '' && inflationInput?.value.trim() !== '';
            const isFileUploaded = fileInput?.files.length > 0;

            if (isManualFilled || isFileUploaded) {
                enableNextButton();
            } else {
                disableNextButton();
            }
        }

        // Monitor manual form inputs
        if (budgetInput) budgetInput.addEventListener('input', checkFormCompletion);
        if (inflationInput) inflationInput.addEventListener('input', checkFormCompletion);

        // Monitor file input
        if (fileInput) fileInput.addEventListener('change', checkFormCompletion);

        // Also call on page load in case of retained inputs (e.g., on form error)
        checkFormCompletion();
    });