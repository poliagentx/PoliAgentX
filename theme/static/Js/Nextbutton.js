document.addEventListener('DOMContentLoaded', function() {
        const dropZone = document.getElementById('drop-zone');
        // Use the ID you specified in the Django form's widget attrs
        const fileInput = document.getElementById('file-upload'); 
        const uploadForm = document.getElementById('upload-form');
        const successMessage = document.getElementById('upload-success-message');
        const nextButtonContainer = document.getElementById('next-button-container');
        const disabledNext = document.getElementById('next-disabled');

        // Drag & drop events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500'); // Note: Changed to border-blue-500 for consistency
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-blue-500');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                uploadForm.submit(); // Auto-submit the form
            }
        });

        // Click drop zone opens file chooser
       // dropZone.addEventListener('click', () => fileInput.click());//

        // Auto-submit on file select
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                uploadForm.submit(); // Auto-submit the form
            }
        });

        // Handle success state after page reload
        if (successMessage) {
            nextButtonContainer.classList.remove('hidden');
            disabledNext.classList.add('hidden');
        }

        // Prevent Next button from re-submitting the upload form
        const nextButton = nextButtonContainer.querySelector('a');
        if (nextButton) {
            nextButton.addEventListener('click', (e) => {
                // The anchor tag already has an href, so this is handled naturally.
                // You can remove this listener if the a tag is just for redirection
                // and doesn't need to prevent a form submission.
            });
        }
    });