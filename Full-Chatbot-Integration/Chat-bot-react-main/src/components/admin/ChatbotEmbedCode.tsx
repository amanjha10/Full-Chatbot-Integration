import React, { useState, useEffect } from 'react';
import { Button, message, Alert, Spin } from 'antd';
import { CopyOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useCompany } from '../../context-provider/CompanyProvider';
import { axiosClient } from '../../config/axiosConfig';

interface ChatbotEmbedCodeProps {
  companyId?: string;
}

const ChatbotEmbedCode: React.FC<ChatbotEmbedCodeProps> = ({
  companyId: propCompanyId
}) => {
  // Get company ID from context (for proper multi-tenant isolation)
  const { companyId: contextCompanyId } = useCompany();
  const [fetchedCompanyId, setFetchedCompanyId] = useState<string | null>(null);

  // Fetch company ID directly from profile API if context doesn't have it
  useEffect(() => {
    const fetchCompanyIdFromProfile = async () => {
      if (!contextCompanyId && !propCompanyId) {
        try {
          const response = await axiosClient.get('/auth/profile/');
          const profileCompanyId = response.data.company_id;
          if (profileCompanyId) {
            setFetchedCompanyId(profileCompanyId);
            console.log('🔍 Fetched company_id from profile API:', profileCompanyId);
          }
        } catch (error) {
          console.error('Failed to fetch company_id from profile:', error);
        }
      }
    };

    fetchCompanyIdFromProfile();
  }, [contextCompanyId, propCompanyId]);

  // Generate a temporary company ID for admin users if none exists
  const generateTempCompanyId = () => {
    const username = localStorage.getItem("username") || "ADMIN";
    const prefix = username.substring(0, 3).toUpperCase().padEnd(3, 'X');
    const suffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `${prefix}${suffix}`;
  };

  const companyId = propCompanyId || contextCompanyId || fetchedCompanyId || generateTempCompanyId();

  // DEAD CODE REMOVED - Debug logging removed for production

  const [copied, setCopied] = useState(false);
  const [detectionStatus, setDetectionStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Check if using temporary company ID
  const isTemporaryCompanyId = !propCompanyId && !contextCompanyId && !fetchedCompanyId;

  // Generate embed code (development environment)
  const generateEmbedCode = () => {
    return `<script src="http://localhost:8001/static/chatbot.js" data-company="${companyId}"></script>`;
  };

  // Check for existing chatbot detection
  useEffect(() => {
    const checkDetectionStatus = async () => {
      try {
        setLoading(true);
        const response = await axiosClient.get(`/chatbot/detection-status/${companyId}/`);
        setDetectionStatus(response.data);
      } catch (error) {
        console.error('Failed to check detection status:', error);
        setDetectionStatus(null);
      } finally {
        setLoading(false);
      }
    };

    if (companyId && companyId !== "UNKNOWN") {
      checkDetectionStatus();

      // Check every 30 seconds for updates
      const interval = setInterval(checkDetectionStatus, 30000);
      return () => clearInterval(interval);
    }
  }, [companyId]);

  // Copy to clipboard
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      message.success('Embed code copied to clipboard!');
      
      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      message.error('Failed to copy to clipboard');
    }
  };

  const embedCode = generateEmbedCode();

  return (
    <div className="mt-6">
      <h5 className="font-medium mb-2">Integration Code</h5>

      {/* Temporary Company ID Warning */}
      {isTemporaryCompanyId && (
        <Alert
          message="⚠️ Using Temporary Company ID"
          description={
            <div>
              <p><strong>Company ID:</strong> {companyId} (temporary)</p>
              <p><strong>Note:</strong> This is a temporary company ID generated for testing. For production use, please ensure your admin account has a proper company ID assigned.</p>
            </div>
          }
          type="warning"
          showIcon
          className="mb-4"
        />
      )}

      {/* Detection Status */}
      {loading ? (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded flex items-center">
          <Spin size="small" className="mr-2" />
          <span className="text-blue-700">Checking for existing chatbot conflicts...</span>
        </div>
      ) : detectionStatus?.has_existing_chatbot ? (
        <Alert
          message="⚠️ Existing Chatbot Detected"
          description={
            <div>
              <p><strong>Issue:</strong> Your website already has a chatbot installed.</p>
              <p><strong>Location:</strong> {detectionStatus.page_url}</p>
              <p><strong>Last Detected:</strong> {new Date(detectionStatus.last_detected).toLocaleString()}</p>
              <p><strong>Solution:</strong> Please remove the existing chatbot elements from your website to avoid conflicts and duplication.</p>
              <p className="mt-2 text-sm text-gray-600">
                <strong>Detection Count:</strong> {detectionStatus.detection_count} times
              </p>
            </div>
          }
          type="warning"
          icon={<WarningOutlined />}
          showIcon
          className="mb-4"
        />
      ) : detectionStatus && !detectionStatus.has_existing_chatbot && detectionStatus.detection_count > 0 ? (
        <Alert
          message="✅ No Conflicts Detected"
          description="Your website is ready for chatbot integration. No existing chatbot conflicts found."
          type="success"
          icon={<CheckCircleOutlined />}
          showIcon
          className="mb-4"
        />
      ) : null}

      {/* Embed Code */}
      <div className="bg-gray-100 p-3 rounded text-sm font-mono relative">
        <code>
          {embedCode}
        </code>
        <Button
          type="primary"
          icon={<CopyOutlined />}
          onClick={() => copyToClipboard(embedCode)}
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 1
          }}
          size="small"
          disabled={detectionStatus?.has_existing_chatbot}
        >
          {copied ? 'Copied!' : 'Copy'}
        </Button>
      </div>

      {/* Warning for existing chatbot */}
      {detectionStatus?.has_existing_chatbot && (
        <div className="mt-2 text-sm text-red-600">
          <strong>Note:</strong> Copy button is disabled until existing chatbot conflicts are resolved.
        </div>
      )}
    </div>
  );
};

export default ChatbotEmbedCode;
