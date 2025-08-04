// Excel file validation script with success indication
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('network-file');
    const form = document.querySelector('form');
    const fileDropArea = document.querySelector('.file-drop-area');
    
    // Valid Excel file extensions and MIME types
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const validMimeTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel', // .xls
        'text/csv', // .csv
        'application/csv'
    ];
    
    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.id = 'file-error';
    errorDiv.style.cssText = `
        color: #dc3545;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        padding: 10px;
        margin: 10px 0;
        display: none;
        font-size: 14px;
        font-family: inherit;
    `;
    
    // Create success message element
    const successDiv = document.createElement('div');
    successDiv.id = 'file-success';
    successDiv.style.cssText = `
        color: #155724;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        padding: 10px;
        margin: 10px 0;
        display: none;
        font-size: 14px;
        font-family: inherit;
    `;
    
    // Insert message divs after the file drop area
    fileDropArea.insertAdjacentElement('afterend', successDiv);
    fileDropArea.insertAdjacentElement('afterend', errorDiv);
    
    // Store original styles to restore later
    const originalDropAreaStyle = {
        border: fileDropArea.style.border || '',
        backgroundColor: fileDropArea.style.backgroundColor || '',
        borderColor: fileDropArea.style.borderColor || ''
    };
    
    // Function to show error message
    function showError(message) {
        hideSuccess();
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Apply error styling to file drop area (non-destructive)
        fileDropArea.style.borderColor = '#dc3545';
        fileDropArea.style.backgroundColor = '#f8d7da';
        fileDropArea.classList.add('error-state');
    }
    
    // Function to show success message
    function showSuccess(fileName, fileSize) {
        hideError();
        const fileSizeKB = (fileSize / 1024).toFixed(2);
        successDiv.innerHTML = `
            <strong>✅ File uploaded successfully!</strong><br>
            📄 <strong>File:</strong> ${fileName}<br>
            📊 <strong>Size:</strong> ${fileSizeKB} KB<br>
            🟢 <strong>Status:</strong> Ready to process
        `;
        successDiv.style.display = 'block';
        
        // Apply success styling to file drop area (non-destructive)
        fileDropArea.style.borderColor = '#28a745';
        fileDropArea.style.backgroundColor = '#d4edda';
        fileDropArea.classList.add('success-state');
        fileDropArea.classList.remove('error-state');
    }
    
    // Function to hide error message
    function hideError() {
        errorDiv.style.display = 'none';
    }
    
    // Function to hide success message
    function hideSuccess() {
        successDiv.style.display = 'none';
    }
    
    // Function to reset styling to original
    function resetStyling() {
        hideError();
        hideSuccess();
        
        // Restore original styling
        fileDropArea.style.border = originalDropAreaStyle.border;
        fileDropArea.style.backgroundColor = originalDropAreaStyle.backgroundColor;
        fileDropArea.style.borderColor = originalDropAreaStyle.borderColor;
        fileDropArea.classList.remove('error-state', 'success-state');
    }
    
    // Function to validate file
    function validateFile(file) {
        if (!file) {
            return true; // Allow empty selection
        }
        
        // Get file extension
        const fileName = file.name.toLowerCase();
        const fileExtension = '.' + fileName.split('.').pop();
        
        // Check file extension
        const hasValidExtension = validExtensions.includes(fileExtension);
        
        // Check MIME type
        const hasValidMimeType = validMimeTypes.includes(file.type);
        
        // File is valid if it has either valid extension or valid MIME type
        return hasValidExtension || hasValidMimeType;
    }
    
    // Function to get file type description
    function getFileTypeDescription(fileName) {
        const extension = fileName.toLowerCase().split('.').pop();
        switch(extension) {
            case 'xlsx':
                return 'Excel Workbook (.xlsx)';
            case 'xls':
                return 'Excel 97-2003 Workbook (.xls)';
            case 'csv':
                return 'Comma Separated Values (.csv)';
            default:
                return 'Unknown file type';
        }
    }
    
    // File input change event
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            if (!validateFile(file)) {
                showError('❌ Invalid file format! Please select a valid Excel file (.xlsx, .xls) or CSV file (.csv)');
                e.target.value = ''; // Clear the input
            } else {
                showSuccess(file.name, file.size);
                console.log('Valid file selected:', file.name, 'Type:', getFileTypeDescription(file.name));
            }
        } else {
            resetStyling();
        }
    });
    
    // Form submit event (additional validation)
    form.addEventListener('submit', function(e) {
        const file = fileInput.files[0];
        
        if (file && !validateFile(file)) {
            e.preventDefault();
            showError('❌ Invalid file format! Please select a valid Excel file (.xlsx, .xls) or CSV file (.csv)');
            return false;
        }
        
        // Optional: Show processing message on successful submission
        if (file && validateFile(file)) {
            console.log('Form submitted with valid file:', file.name);
        }
    });
    
    // Enhanced drag and drop validation
    if (fileDropArea) {
        fileDropArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            // Only add hover effect if not in error or success state
            if (!this.classList.contains('error-state') && !this.classList.contains('success-state')) {
                this.style.opacity = '0.8';
                this.style.transform = 'scale(1.02)';
            }
        });
        
        fileDropArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            // Reset hover effect
            if (!this.classList.contains('error-state') && !this.classList.contains('success-state')) {
                this.style.opacity = '';
                this.style.transform = '';
            }
        });
        
        fileDropArea.addEventListener('drop', function(e) {
            e.preventDefault();
            
            // Reset hover effect
            this.style.opacity = '';
            this.style.transform = '';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                
                if (!validateFile(file)) {
                    showError('❌ Invalid file format! Please select a valid Excel file (.xlsx, .xls) or CSV file (.csv)');
                } else {
                    fileInput.files = files;
                    showSuccess(file.name, file.size);
                    console.log('Valid file dropped:', file.name, 'Type:', getFileTypeDescription(file.name));
                }
            }
        });
        
        // Add click event to the label (for better accessibility)
        fileDropArea.addEventListener('click', function(e) {
            // This will automatically trigger the file input due to the label association
        });
    }
});