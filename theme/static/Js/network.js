  // Enhanced JavaScript with animated SVG and AJAX
  document.addEventListener('DOMContentLoaded', function() {
    class NetworkUploader {
      constructor() {
        this.elements = {
          form: document.getElementById('upload-form'),
          dropZone: document.getElementById('drop-zone'),
          fileInput: document.getElementById('file-input'),
          chooseFileBtn: document.getElementById('choose-file-btn'),
          uploadIcon: document.getElementById('upload-icon'),
          uploadText: document.getElementById('upload-text'),
          uploadProgress: document.getElementById('upload-progress'),
          progressBar: document.getElementById('progress-bar'),
          progressText: document.getElementById('progress-text'),
          // statusMessages: document.getElementById('status-messages'),
          nextDisabled: document.getElementById('next-disabled'),
          nextButtonContainer: document.getElementById('next-button-container')
        };

        this.state = {
          uploading: false,
          uploadSuccess: false
        };

        this.init();
      }

      init() {
        this.setupEventListeners();
        this.addAnimatedCSS();
      }

      addAnimatedCSS() {
        // Add CSS for animated checkmark
        const style = document.createElement('style');
        style.textContent = `
          .checkmark-circle {
            stroke-dasharray: 166;
            stroke-dashoffset: 166;
            stroke-width: 2;
            stroke-miterlimit: 10;
            stroke: #10b981;
            fill: none;
            animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
          }
          .checkmark-check {
            transform-origin: 50% 50%;
            stroke-dasharray: 48;
            stroke-dashoffset: 48;
            animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
          }
          @keyframes stroke {
            100% { stroke-dashoffset: 0; }
          }
          .checkmark-container {
            animation: scale 0.3s ease-in-out 0.9s both;
          }
          @keyframes scale {
            0%, 100% { transform: none; }
            50% { transform: scale3d(1.1, 1.1, 1); }
          }
          .spinner { animation: spin 1s linear infinite; }
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .fade-in { animation: fadeIn 0.5s ease-in; }
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `;
        document.head.appendChild(style);
      }

      setupEventListeners() {
        // File input change
        this.elements.fileInput?.addEventListener('change', (e) => {
          this.handleFileSelect(e.target.files);
        });

        // Drag and drop
        this.setupDragAndDrop();
      }

      setupDragAndDrop() {
        const dropZone = this.elements.dropZone;
        if (!dropZone) return;

        dropZone.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropZone.style.borderColor = '#3b82f6';
          dropZone.style.backgroundColor = '#eff6ff';
        });

        dropZone.addEventListener('dragleave', () => {
          dropZone.style.borderColor = '#cb8700';
          dropZone.style.backgroundColor = 'white';
        });

        dropZone.addEventListener('drop', (e) => {
          e.preventDefault();
          dropZone.style.borderColor = '#cb8700';
          dropZone.style.backgroundColor = 'white';
          this.handleFileSelect(e.dataTransfer.files);
        });

        dropZone.addEventListener('click', () => {
          this.elements.fileInput?.click();
        });
      }

      async handleFileSelect(files) {
        if (!files || files.length === 0) return;

        const file = files[0];
        
        // Validate file
        if (!this.validateFile(file)) return;

        // Update UI
        this.elements.uploadText.textContent = file.name;
        
        // Upload file
        await this.uploadFile(file);
      }

      validateFile(file) {
        if (!file.name.match(/\.(xlsx|xls)$/i)) {
          this.showMessage('Please select an Excel file (.xlsx or .xls)', 'error');
          return false;
        }

        if (file.size > 10 * 1024 * 1024) {
          this.showMessage('File size must be less than 10MB', 'error');
          return false;
        }

        return true;
      }

      async uploadFile(file) {
        if (this.state.uploading) return;

        this.state.uploading = true;
        this.updateUploadUI(true);

        const formData = new FormData();
        formData.append('interdependency_network', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
          this.simulateProgress();

          const response = await fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          });

          const result = await response.json();
          
          if (result.success) {
            this.handleUploadSuccess(result.message, result.stats);
          } else {
            this.handleUploadError(result.message);
          }
        } catch (error) {
          console.error('Upload error:', error);
          this.handleUploadError('Network error. Please check your connection and try again.');
        } finally {
          this.state.uploading = false;
          this.updateUploadUI(false);
        }
      }

      simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 25;
          if (progress > 85) progress = 85;
          
          this.elements.progressBar.style.width = `${progress}%`;
          this.elements.progressText.textContent = `${Math.round(progress)}%`;
          
          if (progress >= 85) {
            clearInterval(interval);
          }
        }, 150);
      }

      updateUploadUI(uploading) {
        if (uploading) {
          this.elements.dropZone.style.pointerEvents = 'none';
          this.elements.dropZone.style.opacity = '0.7';
          this.elements.uploadProgress?.classList.remove('hidden');
          this.elements.uploadIcon.innerHTML = `
            <svg class="w-full h-full spinner" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
          `;
        } else {
          this.elements.dropZone.style.pointerEvents = 'auto';
          this.elements.dropZone.style.opacity = '1';
          this.elements.uploadProgress?.classList.add('hidden');
          this.elements.progressBar.style.width = '0%';
          this.elements.progressText.textContent = '0%';
        }
      }

      handleUploadSuccess(message, stats) {
        this.state.uploadSuccess = true;
        
        // Complete progress
        this.elements.progressBar.style.width = '100%';
        this.elements.progressText.textContent = '100%';
        
        // Update icon to animated checkmark
        setTimeout(() => {
          this.elements.uploadIcon.innerHTML = this.getAnimatedCheckmarkSVG();
          this.elements.uploadText.innerHTML = `
            <span class="text-green-600 font-semibold">Upload Complete!</span>
            ${stats ? `<br><span class="text-sm text-gray-600">Network file processed successfully</span>` : ''}
          `;
        }, 500);

        this.showMessage(message, 'success');
        this.enableNext();
      }

      handleUploadError(message) {
        // Reset icon
        this.elements.uploadIcon.innerHTML = `
          <svg class="w-full h-full" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
          </svg>
        `;
        this.elements.uploadText.textContent = 'Drop your network file here';
        this.showMessage(message, 'error');
      }

      getAnimatedCheckmarkSVG() {
        return `
          <div class="checkmark-container w-full h-full flex items-center justify-center">
            <svg class="w-full h-full" viewBox="0 0 52 52">
              <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
              <path class="checkmark-check" fill="none" stroke="#10b981" stroke-width="3" d="m16 26 6 6 14-14"/>
            </svg>
          </div>
        `;
      }

      showMessage(text, type) {
        const messageEl = document.createElement('div');
        messageEl.className = `fade-in flex items-start p-4 rounded-lg border ${
          type === 'success' ? 'bg-green-50 text-green-800 border-green-200' : 
          'bg-red-50 text-red-800 border-red-200'
        }`;
        
        const icon = type === 'success' ? 
          `<svg class="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>` :
          `<svg class="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>`;

        messageEl.innerHTML = `
          ${icon}
          <div>
            <p class="font-medium">${type === 'success' ? 'Success' : 'Error'}</p>
            <p class="text-sm mt-1">${text}</p>
          </div>
        `;

        this.elements.statusMessages?.appendChild(messageEl);

        setTimeout(() => messageEl?.remove(), 8000);
      }

      enableNext() {
        this.elements.nextDisabled?.classList.add('hidden');
        this.elements.nextButtonContainer?.classList.remove('hidden');
      }

      getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (token) return token;

        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
          const [name, value] = cookie.trim().split('=');
          if (name === 'csrftoken') return value;
        }
        return '';
      }
    }

    new NetworkUploader();
  });
