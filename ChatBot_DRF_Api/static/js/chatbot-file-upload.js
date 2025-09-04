/**
 * Chatbot File Upload Component
 * Handles file uploads with WebSocket notifications for two-way file sharing
 */

class ChatbotFileUpload {
    constructor(config) {
        this.config = {
            apiBaseUrl: config.apiBaseUrl || 'http://localhost:8000',
            companyId: config.companyId,
            sessionId: config.sessionId,
            jwt: config.jwt || null,
            maxFileSize: config.maxFileSize || 25 * 1024 * 1024, // 25MB
            allowedTypes: config.allowedTypes || [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain', 'text/csv'
            ],
            ...config
        };
        
        this.ws = null;
        this.uploadQueue = [];
        this.isUploading = false;
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupFileInput();
        this.setupDragAndDrop();
    }
    
    setupWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/chat/${this.config.companyId}/${this.config.sessionId}/`;
        const wsUrlWithAuth = this.config.jwt ? 
            `${wsUrl}?token=${this.config.jwt}` : wsUrl;
        
        this.ws = new WebSocket(wsUrlWithAuth);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected for file sharing');
            this.requestFileList(); // Get existing files on reconnect
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, attempting to reconnect...');
            setTimeout(() => this.setupWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection_established':
                console.log('WebSocket connection established');
                break;
                
            case 'file_shared':
                this.renderFileMessage(data);
                break;
                
            case 'file_list':
                this.renderExistingFiles(data.files);
                break;
                
            case 'error':
                this.showError(data.message);
                break;
        }
    }
    
    setupFileInput() {
        // Create file input if it doesn't exist
        if (!document.getElementById('chatbot-file-input')) {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.id = 'chatbot-file-input';
            fileInput.style.display = 'none';
            fileInput.multiple = true;
            document.body.appendChild(fileInput);
            
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
            });
        }
        
        // Create upload button
        this.createUploadButton();
    }
    
    createUploadButton() {
        const uploadBtn = document.createElement('button');
        uploadBtn.id = 'chatbot-upload-btn';
        uploadBtn.innerHTML = '📎';
        uploadBtn.title = 'Upload file';
        uploadBtn.className = 'chatbot-upload-btn';
        uploadBtn.onclick = () => document.getElementById('chatbot-file-input').click();
        
        // Add to chat input area (customize based on your chat UI)
        const chatInput = document.querySelector('.chat-input-container') || document.body;
        chatInput.appendChild(uploadBtn);
    }
    
    setupDragAndDrop() {
        const chatContainer = document.querySelector('.chat-container') || document.body;
        
        chatContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            chatContainer.classList.add('drag-over');
        });
        
        chatContainer.addEventListener('dragleave', (e) => {
            e.preventDefault();
            chatContainer.classList.remove('drag-over');
        });
        
        chatContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            chatContainer.classList.remove('drag-over');
            this.handleFileSelection(e.dataTransfer.files);
        });
    }
    
    handleFileSelection(files) {
        for (let file of files) {
            if (this.validateFile(file)) {
                this.uploadQueue.push(file);
            }
        }
        this.processUploadQueue();
    }
    
    validateFile(file) {
        // Check file size
        if (file.size > this.config.maxFileSize) {
            this.showError(`File "${file.name}" is too large. Maximum size is ${this.config.maxFileSize / (1024*1024)}MB.`);
            return false;
        }
        
        // Check file type
        if (!this.config.allowedTypes.includes(file.type)) {
            this.showError(`File type "${file.type}" is not allowed.`);
            return false;
        }
        
        return true;
    }
    
    async processUploadQueue() {
        if (this.isUploading || this.uploadQueue.length === 0) return;
        
        this.isUploading = true;
        
        while (this.uploadQueue.length > 0) {
            const file = this.uploadQueue.shift();
            await this.uploadFile(file);
        }
        
        this.isUploading = false;
    }
    
    async uploadFile(file) {
        const messageId = this.showUploadProgress(file);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('company_id', this.config.companyId);
            formData.append('session_id', this.config.sessionId);
            formData.append('uploader', 'user');
            formData.append('original_name', file.name);
            formData.append('mime_type', file.type);
            formData.append('size', file.size);
            
            const headers = {};
            if (this.config.jwt) {
                headers['Authorization'] = `Bearer ${this.config.jwt}`;
            }
            
            const response = await fetch(`${this.config.apiBaseUrl}/api/chat/upload/`, {
                method: 'POST',
                body: formData,
                headers: headers
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
            
            const result = await response.json();
            this.updateUploadProgress(messageId, 'completed', result);
            
        } catch (error) {
            console.error('Upload error:', error);
            this.updateUploadProgress(messageId, 'failed', null, error.message);
        }
    }
    
    showUploadProgress(file) {
        const messageId = `upload-${Date.now()}-${Math.random()}`;
        const messageHtml = `
            <div id="${messageId}" class="chat-message user-message upload-message">
                <div class="upload-progress">
                    <div class="file-info">
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">(${this.formatFileSize(file.size)})</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="upload-status">Uploading...</div>
                </div>
            </div>
        `;
        
        this.appendMessage(messageHtml);
        return messageId;
    }
    
    updateUploadProgress(messageId, status, result = null, error = null) {
        const messageEl = document.getElementById(messageId);
        if (!messageEl) return;
        
        const progressFill = messageEl.querySelector('.progress-fill');
        const statusEl = messageEl.querySelector('.upload-status');
        
        if (status === 'completed') {
            progressFill.style.width = '100%';
            statusEl.textContent = 'Upload complete';
            messageEl.classList.add('upload-complete');
            
            // WebSocket will handle showing the final file message
            // Remove the progress message after a delay
            setTimeout(() => messageEl.remove(), 2000);
            
        } else if (status === 'failed') {
            progressFill.style.width = '0%';
            statusEl.textContent = `Upload failed: ${error}`;
            messageEl.classList.add('upload-failed');
        }
    }
    
    renderFileMessage(fileData) {
        const messageHtml = `
            <div class="chat-message ${fileData.uploader === 'user' ? 'user-message' : 'agent-message'}">
                <div class="file-message">
                    <div class="file-icon">${this.getFileIcon(fileData.mime_type)}</div>
                    <div class="file-details">
                        <div class="file-name">${fileData.name}</div>
                        <div class="file-meta">
                            ${this.formatFileSize(fileData.size)} • 
                            ${fileData.uploader === 'user' ? 'You' : 'Agent'} • 
                            ${this.formatTime(fileData.created_at)}
                        </div>
                    </div>
                    <div class="file-actions">
                        <a href="${fileData.url}" target="_blank" class="download-btn">📥</a>
                        ${this.isImage(fileData.mime_type) ? 
                            `<button onclick="this.showImagePreview('${fileData.url}')" class="preview-btn">👁️</button>` : ''}
                    </div>
                </div>
            </div>
        `;
        
        this.appendMessage(messageHtml);
    }
    
    renderExistingFiles(files) {
        files.forEach(file => this.renderFileMessage(file));
    }
    
    requestFileList() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'request_file_list',
                session_id: this.config.sessionId,
                company_id: this.config.companyId
            }));
        }
    }
    
    // Utility methods
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
    
    getFileIcon(mimeType) {
        if (mimeType.startsWith('image/')) return '🖼️';
        if (mimeType === 'application/pdf') return '📄';
        if (mimeType.includes('word')) return '📝';
        if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
        return '📎';
    }
    
    isImage(mimeType) {
        return mimeType.startsWith('image/');
    }
    
    appendMessage(html) {
        const chatMessages = document.querySelector('.chat-messages') || document.body;
        chatMessages.insertAdjacentHTML('beforeend', html);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    showError(message) {
        console.error('File upload error:', message);
        // Customize error display based on your UI
        alert(message);
    }
    
    showImagePreview(url) {
        // Simple image preview modal
        const modal = document.createElement('div');
        modal.className = 'image-preview-modal';
        modal.innerHTML = `
            <div class="modal-backdrop" onclick="this.parentElement.remove()">
                <img src="${url}" alt="Preview" style="max-width: 90%; max-height: 90%;">
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Export for use
window.ChatbotFileUpload = ChatbotFileUpload;
