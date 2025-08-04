document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('form');
  const fileInput = document.getElementById('budget-file');
  const fileDropArea = document.querySelector('.file-drop-area');
  const messageContainer = document.getElementById('message-container');
  const submitButton = form.querySelector('button[type="submit"]');

  const validExtensions = ['.xlsx', '.xls', '.csv'];

  function showMessage(message, type) {
    messageContainer.innerHTML = message;
    messageContainer.style.display = 'block';

    if (type === 'success') {
      messageContainer.style.backgroundColor = '#d1f2eb';
      messageContainer.style.color = '#0c5460';
      messageContainer.style.border = '2px solid #17a2b8';
    } else if (type === 'error') {
      messageContainer.style.backgroundColor = '#f8d7da';
      messageContainer.style.color = '#721c24';
      messageContainer.style.border = '2px solid #dc3545';
    }
  }

  function clearMessage() {
    messageContainer.style.display = 'none';
    messageContainer.innerHTML = '';
  }

  function isValidFile(file) {
    if (!file) return false;
    const name = file.name.toLowerCase();
    return validExtensions.some(ext => name.endsWith(ext));
  }

  function updateDropAreaStyle(isValid) {
    if (isValid) {
      fileDropArea.style.backgroundColor = '#d1f2eb';
      fileDropArea.style.borderColor = '#17a2b8';
    } else {
      fileDropArea.style.backgroundColor = '';
      fileDropArea.style.borderColor = '';
    }
  }

  fileInput.addEventListener('change', function (e) {
    const file = e.target.files[0];

    if (!file) {
      clearMessage();
      updateDropAreaStyle(false);
      return;
    }

    if (!isValidFile(file)) {
      e.target.value = '';
      updateDropAreaStyle(false);
      showMessage('❌ Invalid file format. Only .xls, .xlsx, and .csv allowed.', 'error');
    } else {
      updateDropAreaStyle(true);
      showMessage('✅ File uploaded successfully.', 'success');
    }
  });

  // Drag and Drop Handling
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    fileDropArea.addEventListener(eventName, e => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  fileDropArea.addEventListener('drop', function (e) {
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      fileInput.files = e.dataTransfer.files; // Update actual input
      fileInput.dispatchEvent(new Event('change')); // Trigger validation
    }
  });

  // Form Submit Validation
  form.addEventListener('submit', function (e) {
    const file = fileInput.files[0];

    if (!file) {
      e.preventDefault();
      showMessage('⚠️ No file selected. Please choose a file to continue.', 'error');
      return;
    }

    if (!isValidFile(file)) {
      e.preventDefault();
      showMessage('❌ Invalid file format. Only .xls, .xlsx, and .csv allowed.', 'error');
      return;
    }

    // Optional: Disable button and show minimal progress
    submitButton.disabled = true;
    submitButton.innerText = '⏳ Uploading...';
  });
});
