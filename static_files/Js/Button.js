document.addEventListener('DOMContentLoaded', function() {
    const manualRadio = document.getElementById('radio-manual');
    const uploadRadio = document.getElementById('radio-upload');
    const manualSection = document.getElementById('manual-input-section');
    const uploadSection = document.getElementById('file-upload-section');
    const fileUploadInput = document.getElementById('government_expenditure');
    const dropZone = document.getElementById('drop-zone');

    const nextButton = document.getElementById('next-button');
    const nextBtnContainer = document.getElementById('next-button-container');
    const nextDisabled = document.getElementById('next-disabled');

    const budgetInput = document.getElementById('id_budget');
    const inflationInput = document.getElementById('id_inflation_rate');

    let uploadSubmitted = false;

    function checkFormCompletion() {
        let isFormValid = false;

        if (manualRadio.checked) {
            isFormValid =
                (budgetInput?.value.trim() !== '' && !isNaN(parseFloat(budgetInput?.value))) &&
                (inflationInput?.value.trim() !== '' && !isNaN(parseFloat(inflationInput?.value)));
        } else if (uploadRadio.checked) {
            isFormValid = fileUploadInput?.files.length > 0;
        }

        if (isFormValid) {
            enableNextButton();
        } else {
            disableNextButton();
        }
    }

    function enableNextButton() {
        nextBtnContainer.classList.remove('hidden');
        nextDisabled.classList.add('hidden');
    }

    function disableNextButton() {
        nextBtnContainer.classList.add('hidden');
        nextDisabled.classList.remove('hidden');
    }

    function toggleSections() {
        if (manualRadio.checked) {
            manualSection.classList.remove('hidden');
            uploadSection.classList.add('hidden');
        } else {
            manualSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
        checkFormCompletion();
    }

    // Auto-submit for file uploads
    function trySubmitUpload() {
        if (uploadSubmitted) return; // prevent double submission
        if (uploadRadio.checked && fileUploadInput?.files.length > 0) {
            uploadSubmitted = true;
            // document.getElementById('upload-form').submit();
        }
    }

    // Next button click
    if (nextButton) {
        nextButton.addEventListener('click', () => {
            if (manualRadio.checked) {
                document.getElementById('budget-form').submit();
            } else if (uploadRadio.checked) {
                document.getElementById('upload-form').submit();
            }
        });
    }

    toggleSections();
    manualRadio.addEventListener('change', toggleSections);
    uploadRadio.addEventListener('change', toggleSections);

    // Drag & drop functionality (merged!)
    if (dropZone && fileUploadInput) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500', 'bg-blue-50');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileUploadInput.files = files;
                fileUploadInput.dispatchEvent(new Event('change')); // 🔑 keeps everything in sync
                dropZone.querySelector("p.text-gray-700").textContent = files[0].name;
            }
        });

        const chooseFileLabel = document.querySelector('label[for="' + fileUploadInput.id + '"]');
        if (chooseFileLabel) {
            chooseFileLabel.addEventListener('click', (e) => {
                e.preventDefault();
                fileUploadInput.click();
            });
        }
    }

    // Monitor inputs
    if (budgetInput) budgetInput.addEventListener('input', checkFormCompletion);
    if (inflationInput) inflationInput.addEventListener('input', checkFormCompletion);
    if (fileUploadInput) {
        fileUploadInput.addEventListener('change', () => {
            checkFormCompletion();
            trySubmitUpload(); // <-- auto-submit when a file is chosen
        });
    }

    checkFormCompletion();
});
