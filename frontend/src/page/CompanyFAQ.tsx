import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  // message,
  Space,
  Popconfirm,
  Tag,
  Typography,
  Row,
  Col,
  Statistic,
  App
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  QuestionCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';
import { get } from '../api/get';
import { post } from '../api/post';
import { put } from '../api/Put';
import { del } from '../api/delete';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface CompanyFAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  section: string;
  document: string;
  created_at: string;
  updated_at: string;
}

interface CompanyFAQResponse {
  count: number;
  company_id: string;
  company_name: string;
  results: CompanyFAQ[];
}

const CompanyFAQPageContent: React.FC = () => {
  const { message } = App.useApp();
  const [faqs, setFaqs] = useState<CompanyFAQ[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFaq, setEditingFaq] = useState<CompanyFAQ | null>(null);
  const [form] = Form.useForm();
  const [companyInfo, setCompanyInfo] = useState({ company_id: '', company_name: '', count: 0 });
  const [refreshingVectors, setRefreshingVectors] = useState(false);

  // Load company FAQs
  const loadFAQs = async () => {
    setLoading(true);
    try {
      const response = await get<CompanyFAQResponse>('/chatbot/admin/company-faqs/');
      if (response.data) {
        setFaqs(response.data.results);
        setCompanyInfo({
          company_id: response.data.company_id,
          company_name: response.data.company_name,
          count: response.data.count
        });
      } else {
        message.error('Failed to load company FAQs');
      }
    } catch (error) {
      console.error('Error loading FAQs:', error);
      message.error('Failed to load company FAQs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFAQs();
  }, []);

  // Handle create/update FAQ
  const handleSubmit = async (values: any) => {
    try {
      // Process the form values
      const processedValues = {
        ...values,
        // Ensure category is a string, not an array
        category: Array.isArray(values.category) ? values.category[0] : values.category
      };

      console.log('Submitting FAQ data:', processedValues);

      if (editingFaq) {
        // Update existing FAQ
        const response = await put(`/chatbot/admin/company-faqs/${editingFaq.id}/`, processedValues);
        if (response.data) {
          message.success('FAQ updated successfully');
          loadFAQs();
        } else {
          message.error('Failed to update FAQ');
        }
      } else {
        // Create new FAQ
        const response = await post('/chatbot/admin/company-faqs/create/', processedValues);
        if (response.data) {
          message.success('FAQ created successfully');
          loadFAQs();
        } else {
          message.error('Failed to create FAQ');
        }
      }
      setModalVisible(false);
      setEditingFaq(null);
      form.resetFields();
    } catch (error) {
      console.error('Error saving FAQ:', error);
      console.error('Error details:', (error as any).response?.data);
      message.error(`Failed to save FAQ: ${(error as any).response?.data?.error || (error as any).message}`);
    }
  };

  // Handle delete FAQ
  const handleDelete = async (faqId: string) => {
    try {
      const response = await del(`/chatbot/admin/company-faqs/${faqId}/`);
      if (response.data || response.status === 200) {
        message.success('FAQ deleted successfully');
        loadFAQs();
      } else {
        message.error('Failed to delete FAQ');
      }
    } catch (error) {
      console.error('Error deleting FAQ:', error);
      message.error('Failed to delete FAQ');
    }
  };

  // Handle refresh vectors
  const handleRefreshVectors = async () => {
    setRefreshingVectors(true);
    try {
      const response = await post('/chatbot/admin/company-faqs/refresh-vectors/', {});
      if (response.data) {
        message.success('Company FAQ vectors refreshed successfully');
      } else {
        message.error('Failed to refresh vectors');
      }
    } catch (error) {
      console.error('Error refreshing vectors:', error);
      message.error('Failed to refresh vectors');
    } finally {
      setRefreshingVectors(false);
    }
  };

  // Open modal for create/edit
  const openModal = (faq?: CompanyFAQ) => {
    if (faq) {
      setEditingFaq(faq);
      form.setFieldsValue({
        question: faq.question,
        answer: faq.answer,
        category: faq.category
      });
    } else {
      setEditingFaq(null);
      form.resetFields();
    }
    setModalVisible(true);
  };

  // Table columns
  const columns = [
    {
      title: 'Question',
      dataIndex: 'question',
      key: 'question',
      width: '30%',
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 200 }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Answer',
      dataIndex: 'answer',
      key: 'answer',
      width: '40%',
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: '15%',
      render: (category: string) => (
        <Tag color="blue">{category}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: '15%',
      render: (_: any, record: CompanyFAQ) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => openModal(record)}
            size="small"
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this FAQ?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={18}>
          <Title level={2}>
            <BulbOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
            Company FAQ Management
          </Title>
          <Text type="secondary">
            Manage company-specific FAQs for {companyInfo.company_name} ({companyInfo.company_id})
          </Text>
        </Col>
        <Col span={6}>
          <Statistic
            title="Total FAQs"
            value={companyInfo.count}
            prefix={<QuestionCircleOutlined />}
          />
        </Col>
      </Row>

      {/* Action Buttons */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openModal()}
          >
            Add New FAQ
          </Button>
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadFAQs}
            loading={loading}
          >
            Refresh
          </Button>
        </Col>
        <Col>
          <Button
            type="dashed"
            icon={<BulbOutlined />}
            onClick={handleRefreshVectors}
            loading={refreshingVectors}
          >
            Refresh AI Vectors
          </Button>
        </Col>
      </Row>

      {/* FAQ Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={faqs}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} FAQs`,
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingFaq ? 'Edit Company FAQ' : 'Add New Company FAQ'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingFaq(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="question"
            label="Question"
            rules={[{ required: true, message: 'Please enter the question' }]}
          >
            <Input placeholder="Enter the FAQ question" />
          </Form.Item>

          <Form.Item
            name="answer"
            label="Answer"
            rules={[{ required: true, message: 'Please enter the answer' }]}
          >
            <TextArea
              rows={6}
              placeholder="Enter the detailed answer"
            />
          </Form.Item>

          <Form.Item
            name="category"
            label="Category"
            rules={[{ required: true, message: 'Please select a category' }]}
          >
            <Select
              placeholder="Select or enter a category"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              <Option value="General">General</Option>
              <Option value="Services">Services</Option>
              <Option value="Pricing">Pricing</Option>
              <Option value="Support">Support</Option>
              <Option value="Technical">Technical</Option>
              <Option value="Company Info">Company Info</Option>
              <Option value="Contact">Contact</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingFaq ? 'Update FAQ' : 'Create FAQ'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

const CompanyFAQPage: React.FC = () => {
  return (
    <App>
      <CompanyFAQPageContent />
    </App>
  );
};

export default CompanyFAQPage;
