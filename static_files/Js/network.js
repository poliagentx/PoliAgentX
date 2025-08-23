document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('upload-form');

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
            uploadForm.submit();   // 🚀 auto-submit on drop
        }
    });

    // Click drop zone opens file chooser
    dropZone.addEventListener('click', () => fileInput.click());

    // Auto-submit on file select
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadForm.submit();   // 🚀 auto-submit on select
        }
    });

    // Disable Next button default submit (optional, to avoid double submit)
    const nextButton = document.getElementById('next-button');
    if (nextButton) {
        nextButton.addEventListener('click', (e) => e.preventDefault());
    }
});
