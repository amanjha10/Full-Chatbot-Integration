import React, { useState, useRef, useCallback, useEffect } from 'react';
import { AiOutlineUpload, AiOutlineDownload } from 'react-icons/ai';
import { FaFileAlt, FaImage, FaFile } from 'react-icons/fa';

interface FileData {
  id: number;
  company_id: string;
  session_id: string;
  uploader: 'user' | 'agent';
  url: string;
  name: string;
  mime_type: string;
  size: number;
  thumbnail?: string;
  created_at: string;
}

interface FileUploadProps {
  companyId: string;
  sessionId: string;
  apiBaseUrl?: string;
  jwt?: string;
  onFileShared?: (file: FileData) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'failed';
  error?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  companyId,
  sessionId,
  apiBaseUrl = 'http://localhost:8000',
  jwt,
  onFileShared,
  onError,
  className = ''
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<Map<string, UploadProgress>>(new Map());
  const [files, setFiles] = useState<FileData[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const maxFileSize = 25 * 1024 * 1024; // 25MB
  const allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', 'text/csv'
  ];

  // WebSocket setup
  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/ws/chat/${companyId}/${sessionId}/`;
    const wsUrlWithAuth = jwt ? `${wsUrl}?token=${jwt}` : wsUrl;
    
    wsRef.current = new WebSocket(wsUrlWithAuth);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected for file sharing');
      requestFileList();
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          // Reconnect logic here
        }
      }, 3000);
    };
    
    return () => {
      wsRef.current?.close();
    };
  }, [companyId, sessionId, jwt]);

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'file_shared':
        const newFile: FileData = data;
        setFiles(prev => [newFile, ...prev.filter(f => f.id !== newFile.id)]);
        onFileShared?.(newFile);
        break;
        
      case 'file_list':
        setFiles(data.files || []);
        break;
        
      case 'error':
        onError?.(data.message);
        break;
    }
  };

  const requestFileList = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'request_file_list',
        session_id: sessionId,
        company_id: companyId
      }));
    }
  };

  const validateFile = (file: File): string | null => {
    if (file.size > maxFileSize) {
      return `File "${file.name}" is too large. Maximum size is 25MB.`;
    }
    
    if (!allowedTypes.includes(file.type)) {
      return `File type "${file.type}" is not allowed.`;
    }
    
    return null;
  };

  const uploadFile = async (file: File) => {
    const uploadId = `${Date.now()}-${Math.random()}`;
    
    // Add to uploads map
    setUploads(prev => new Map(prev.set(uploadId, {
      file,
      progress: 0,
      status: 'uploading'
    })));

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('company_id', companyId);
      formData.append('session_id', sessionId);
      formData.append('uploader', 'agent');
      formData.append('original_name', file.name);
      formData.append('mime_type', file.type);
      formData.append('size', file.size.toString());

      const headers: Record<string, string> = {};
      if (jwt) {
        headers['Authorization'] = `Bearer ${jwt}`;
      }

      const response = await fetch(`${apiBaseUrl}/api/chat/upload/`, {
        method: 'POST',
        body: formData,
        headers
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }

      await response.json();
      
      // Update upload status
      setUploads(prev => new Map(prev.set(uploadId, {
        file,
        progress: 100,
        status: 'completed'
      })));

      // Remove from uploads after delay
      setTimeout(() => {
        setUploads(prev => {
          const newMap = new Map(prev);
          newMap.delete(uploadId);
          return newMap;
        });
      }, 3000);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      
      setUploads(prev => new Map(prev.set(uploadId, {
        file,
        progress: 0,
        status: 'failed',
        error: errorMessage
      })));
      
      onError?.(errorMessage);
    }
  };

  const handleFileSelection = useCallback((selectedFiles: FileList | File[]) => {
    const fileArray = Array.from(selectedFiles);
    
    for (const file of fileArray) {
      const error = validateFile(file);
      if (error) {
        onError?.(error);
        continue;
      }
      
      uploadFile(file);
    }
  }, [companyId, sessionId, apiBaseUrl, jwt]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileSelection(droppedFiles);
    }
  }, [handleFileSelection]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      handleFileSelection(selectedFiles);
    }
    // Reset input value
    e.target.value = '';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return <FaImage className="w-5 h-5" />;
    if (mimeType === 'application/pdf') return <FaFileAlt className="w-5 h-5" />;
    return <FaFile className="w-5 h-5" />;
  };

  const formatTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className={`file-upload-container ${className}`}>
      {/* Upload Area */}
      <div
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <AiOutlineUpload className="w-8 h-8 text-gray-400 mb-2" />
        <p className="text-sm text-gray-600 mb-1">
          Click to upload or drag and drop files here
        </p>
        <p className="text-xs text-gray-400">
          Max 25MB • Images, PDFs, Documents
        </p>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileInputChange}
          accept={allowedTypes.join(',')}
        />
      </div>

      {/* Upload Progress */}
      {uploads.size > 0 && (
        <div className="upload-progress-container">
          {Array.from(uploads.entries()).map(([id, upload]) => (
            <div key={id} className="upload-progress-item">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium truncate">
                  {upload.file.name}
                </span>
                <span className="text-xs text-gray-500">
                  {formatFileSize(upload.file.size)}
                </span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    upload.status === 'completed' ? 'bg-green-500' :
                    upload.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${upload.progress}%` }}
                />
              </div>
              
              <div className="text-xs mt-1">
                {upload.status === 'uploading' && 'Uploading...'}
                {upload.status === 'completed' && 'Upload complete'}
                {upload.status === 'failed' && `Failed: ${upload.error}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="file-list">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Shared Files ({files.length})
          </h4>
          
          {files.map((file) => (
            <div key={file.id} className="file-item">
              <div className="flex items-center space-x-3">
                <div className="file-icon">
                  {getFileIcon(file.mime_type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)} • 
                    {file.uploader === 'agent' ? ' You' : ' User'} • 
                    {formatTime(file.created_at)}
                  </p>
                </div>
                
                <div className="flex items-center space-x-2">
                  <a
                    href={file.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-blue-600 hover:text-blue-800"
                    title="Download"
                  >
                    <AiOutlineDownload className="w-4 h-4" />
                  </a>

                  {file.mime_type.startsWith('image/') && (
                    <button
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = file.url;
                        link.download = file.name;
                        link.style.display = 'none';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                      }}
                      className="p-1 text-green-600 hover:text-green-800"
                      title="Download Image"
                    >
                      <AiOutlineDownload className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;

// CSS styles (add to your global CSS or styled-components)
export const fileUploadStyles = `
.file-upload-container {
  @apply space-y-4;
}

.upload-area {
  @apply border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer transition-colors duration-200 hover:border-blue-400 hover:bg-blue-50;
}

.upload-area.dragging {
  @apply border-blue-500 bg-blue-100;
}

.upload-progress-container {
  @apply space-y-3 p-4 bg-gray-50 rounded-lg;
}

.upload-progress-item {
  @apply space-y-2;
}

.file-list {
  @apply space-y-3;
}

.file-item {
  @apply p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow duration-200;
}

.file-icon {
  @apply text-gray-500;
}
`;
