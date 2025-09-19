import React from "react";
import {
  DownloadOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  FileZipOutlined,
  FileOutlined,
} from "@ant-design/icons";
import { Button, Typography, Image, Tooltip } from "antd";

const { Text } = Typography;

interface FileMessageProps {
  file_url?: string;
  file_name?: string;
  file_type?: string;
  file_size?: number;
  message_type: "user" | "agent" | "bot";
  className?: string;
}

const FileMessage: React.FC<FileMessageProps> = ({
  file_url,
  file_name,
  file_type,
  file_size,
  message_type,
  className = "",
}) => {
  // Get base URL for file downloads and images
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "https://bot.spell.com.np/api";
  const baseUrl = apiBaseUrl.replace("/api", ""); // Remove /api suffix to get base URL
  if (!file_url || !file_name) return null;

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case "image":
        return <FileImageOutlined style={{ color: "#52c41a" }} />;
      case "document":
        if (file_name?.toLowerCase().endsWith(".pdf")) {
          return <FilePdfOutlined style={{ color: "#ff4d4f" }} />;
        }
        return <FileTextOutlined style={{ color: "#1890ff" }} />;
      case "archive":
        return <FileZipOutlined style={{ color: "#722ed1" }} />;
      default:
        return <FileOutlined style={{ color: "#8c8c8c" }} />;
    }
  };

  const isImage =
    file_type === "image" ||
    ["jpg", "jpeg", "png", "gif", "bmp", "webp"].some((ext) =>
      file_name.toLowerCase().endsWith(`.${ext}`)
    );

  const handleDownload = () => {
    // Create a temporary anchor element for download
    const link = document.createElement("a");
    const downloadUrl = file_url?.startsWith('http') ? file_url : `${baseUrl}${file_url}`;
    link.href = downloadUrl;
    link.download = file_name || 'download';
    link.target = "_blank";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      className={`file-message ${className}`}
      style={{
        border: "1px solid #d9d9d9",
        borderRadius: "8px",
        padding: "12px",
        margin: "8px 0",
        backgroundColor: message_type === "user" ? "#f0f8ff" : "#f6ffed",
        maxWidth: "300px",
      }}
    >
      {isImage ? (
        // Image preview with download option
        <div style={{ backgroundColor: "#f9f9f9", borderRadius: "8px", padding: "12px" }}>
          <div style={{ marginBottom: "8px" }}>
            <Image
              src={file_url?.startsWith('http') ? file_url : `${baseUrl}${file_url}`}
              alt={file_name}
              style={{
                maxWidth: "250px",
                maxHeight: "200px",
                borderRadius: "6px",
                cursor: "pointer",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              }}
              preview={false}
              onClick={handleDownload}
              fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            />
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              {getFileIcon(file_type || "")}
              <Text
                ellipsis={{ tooltip: file_name }}
                style={{ maxWidth: "150px" }}
              >
                {file_name}
              </Text>
            </div>
            <Tooltip title="Download">
              <Button
                type="text"
                size="small"
                icon={<DownloadOutlined />}
                onClick={handleDownload}
              />
            </Tooltip>
          </div>
          {file_size && (
            <Text type="secondary" style={{ fontSize: "12px" }}>
              {formatFileSize(file_size)}
            </Text>
          )}
        </div>
      ) : (
        // Non-image file display
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginBottom: "8px",
            }}
          >
            {getFileIcon(file_type || "")}
            <div style={{ flex: 1, minWidth: 0 }}>
              <Text
                ellipsis={{ tooltip: file_name }}
                style={{ fontWeight: 500 }}
              >
                {file_name}
              </Text>
              {file_size && (
                <div>
                  <Text type="secondary" style={{ fontSize: "12px" }}>
                    {formatFileSize(file_size)}
                  </Text>
                </div>
              )}
            </div>
          </div>
          <Button
            type="primary"
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleDownload}
            style={{ width: "100%" }}
          >
            Download
          </Button>
        </div>
      )}
    </div>
  );
};

export default FileMessage;
