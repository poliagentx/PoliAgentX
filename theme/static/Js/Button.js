document.addEventListener('DOMContentLoaded', function () {
    // ---------- DOM elements ----------
    const manualRadio = document.getElementById('radio-manual');
    const uploadRadio = document.getElementById('radio-upload');

    const manualSection = document.getElementById('manual-input-section');
    const uploadSection = document.getElementById('file-upload-section');

    const manualForm = document.getElementById('budget-form');
    const uploadForm = document.getElementById('upload-form');

    const budgetInput = document.getElementById('id_budget');
    const inflationInput = document.getElementById('id_inflation_rate');

    const fileInput = document.querySelector('#upload-form input[type="file"]');
    const dropZone = document.getElementById('drop-zone');

    const nextButtonContainer = document.getElementById('next-button-container'); 
    const nextButton = document.getElementById('next-button');                    
    const disabledNext = document.getElementById('next-disabled');                

    const successMessage = document.getElementById('upload-success-message');

    let submitting = false;

    // ---------- helper functions ----------
    const show = (el) => el && el.classList.remove('hidden');
    const hide = (el) => el && el.classList.add('hidden');

    function toggleSections() {
        if (manualRadio && manualRadio.checked) {
            show(manualSection);
            hide(uploadSection);
        } else {
            hide(manualSection);
            show(uploadSection);
        }
    }

    function isNum(val) {
        if (val == null) return false;
        const v = String(val).trim();
        return v !== '' && !isNaN(parseFloat(v));
    }

    function manualInputsValid() {
        return isNum(budgetInput?.value) && isNum(inflationInput?.value);
    }

    async function trySubmitManual() {
        if (submitting) return;
        if (manualRadio?.checked && manualInputsValid()) {
            submitting = true;

            const formData = new FormData(manualForm);
            await fetch(manualForm.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            });

            // Full page reload to render Django messages
            window.location.reload();
        }
    }

    async function trySubmitUpload() {
        if (submitting) return;
        if (uploadRadio?.checked && fileInput?.files?.length > 0) {
            submitting = true;

            const formData = new FormData(uploadForm);
            await fetch(uploadForm.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            });

            // Full page reload to render Django messages
            window.location.reload();
        }
    }

    function enableNextButton() {
        hide(disabledNext);
        show(nextButtonContainer);
        if (nextButton) {
            nextButton.addEventListener('click', () => {
                window.location.href = '/upload_network/';
            }, { once: true });
        }
    }

    // ---------- initial UI ----------
    toggleSections();

    // Enable NEXT if Django rendered success message
    if (successMessage) {
        enableNextButton();
    }

    // ---------- radio handling ----------
    manualRadio?.addEventListener('change', () => {
        toggleSections();
        trySubmitManual();
    });
    uploadRadio?.addEventListener('change', () => {
        toggleSections();
        trySubmitUpload();
    });

    // ---------- manual input events ----------
    budgetInput?.addEventListener('input', trySubmitManual);
    inflationInput?.addEventListener('input', trySubmitManual);

    // ---------- file input events ----------
    fileInput?.addEventListener('change', trySubmitUpload);

    // ---------- drag & drop ----------
    if (dropZone && fileInput) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500', 'bg-gray-100');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-blue-500', 'bg-gray-100');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500', 'bg-gray-100');

            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                fileInput.files = files;

                const nameTarget = dropZone.querySelector('p.text-gray-700');
                if (nameTarget) nameTarget.textContent = files[0].name;

                if (uploadRadio && !uploadRadio.checked) {
                    uploadRadio.checked = true;
                    toggleSections();
                }
                trySubmitUpload();
            }
        });

        const labelInDropzone = dropZone.querySelector('label');
        labelInDropzone?.addEventListener('click', (e) => {
            e.preventDefault();
            fileInput.click();
        });
    }
});
