
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('fileInput');
    const nextContainer = document.getElementById('next-button-container');
    const nextDisabled = document.getElementById('next-disabled');

    // Show/hide NEXT button based on file selection
    function checkFileStatus() {
        if (fileInput.files.length > 0) {
            nextContainer.classList.remove('hidden');
            nextDisabled.classList.add('hidden');
        } else {
            nextContainer.classList.add('hidden');
            nextDisabled.classList.remove('hidden');
        }
    }

    // Drag & drop events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-gray-500');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-gray-500');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-gray-500');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            checkFileStatus();
        }
    });

    // Clicking the label triggers file input
    const chooseFileLabel = dropZone.querySelector('label');
    chooseFileLabel.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });

    fileInput.addEventListener('change', checkFileStatus);

    checkFileStatus(); // initial check

    // NEXT button submits upload form
    const nextButton = document.getElementById('next-button');
    if (nextButton) {
        nextButton.addEventListener('click', () => {
            const uploadForm = document.getElementById('upload-form');
            if (uploadForm) uploadForm.submit();
        });
    }

    // SKIP button submits skip form
    const skipButton = document.getElementById('skip-button');
    if (skipButton) {
        skipButton.addEventListener('click', () => {
            const skipForm = document.getElementById('skip-form');
            if (skipForm) skipForm.submit();
        });
    }
});

