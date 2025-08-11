const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-upload'); 

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-500');
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
      document.getElementById('upload-form').submit();
    }
  });

  document.getElementById('file-upload').addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    document.getElementById('upload-form').submit();
  });

  document.addEventListener("DOMContentLoaded", function () {
    const successMessage = document.getElementById("upload-success-message");
    const nextButton = document.getElementById("next-button-container");
    const disabledButton = document.getElementById("next-disabled");

    if (successMessage) {
      nextButton.classList.remove("hidden");
      disabledButton.classList.add("hidden");
    }
<<<<<<< HEAD
  });
=======
  });
  


  
>>>>>>> c7f7550ce5f43d111d4981cba5605c6f0ffcde0e
