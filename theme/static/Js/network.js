document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('upload-form');
    const successMessage = document.getElementById('upload-success-message');
    const nextButton = document.getElementById('next-button'); // Corrected to get the button directly
    const nextButtonContainer = document.getElementById('next-button-container');
    const disabledNext = document.getElementById('next-disabled');
    const skipButton = document.getElementById('skip-button');

    // Drag & drop events
    dropZone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-gray-500');
    });

    dropZone?.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-gray-500');
    });

    dropZone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-gray-500');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            uploadForm.submit();
        }
    });

    // Click drop zone opens file chooser
    dropZone?.addEventListener('click', () => fileInput.click());

    // Auto-submit on file select
    fileInput?.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadForm.submit();
        }
    });

    // Handle success state after reload
    if (successMessage) {
        // Show active "Next" button
        if (nextButtonContainer) nextButtonContainer.classList.remove('hidden');
        if (disabledNext) disabledNext.classList.add('hidden');
    }

    // Redirect to the next step using the URL from a data attribute
    if (nextButton) {
        nextButton.addEventListener('click', (e) => {
            e.preventDefault();
            // Get the correct URL from the button's data attribute
            const nextUrl = nextButton.getAttribute('data-next-url');
            if (nextUrl) {
                window.location.href = nextUrl;
            }
        });
    }

    // SKIP button submits skip form
    if (skipButton) {
        skipButton.addEventListener('click', () => {
            const skipForm = document.getElementById('skip-form');
            if (skipForm) skipForm.submit();
        });
    }
});