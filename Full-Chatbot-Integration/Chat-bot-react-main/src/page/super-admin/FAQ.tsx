import React, { useState, useEffect } from "react";
import {
  Button,
  Card,
  Form,
  Input,
  Select,
  Table,
  Modal,
  message,
  Tag,
  Popconfirm,
  Space,
  Tabs,
} from "antd";
import {
  FiPlus,
  FiEdit2,
  FiTrash2,
  FiRefreshCw,
  FiDatabase,
} from "react-icons/fi";
import useSWR from "swr";
import { axiosClient } from "../../config/axiosConfig";

const { TextArea } = Input;
const { Option } = Select;

interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  section: string;
  document: string;
  chunk_id: string;
  created_at?: string;
  updated_at?: string;
}

interface FAQCategory {
  key: string;
  label: string;
  subcategories?: string[];
}

const FAQ_CATEGORIES: FAQCategory[] = [
  {
    key: "general_queries",
    label: "General Queries",
    subcategories: [
      "study_abroad_basics",
      "visa_information", 
      "accommodation",
      "custom_entries"
    ]
  },
  {
    key: "language_requirements",
    label: "Language Requirements",
    subcategories: [
      "english_speaking_countries",
      "non_english_countries"
    ]
  },
  {
    key: "scholarships",
    label: "Scholarships",
    subcategories: [
      "global_opportunities",
      "country_specific"
    ]
  },
  {
    key: "career_prospects",
    label: "Career Prospects", 
    subcategories: [
      "post_study_work",
      "job_markets"
    ]
  }
];

export default function SuperAdminFAQ() {
  const [activeTab, setActiveTab] = useState("manage");
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedFAQ, setSelectedFAQ] = useState<FAQ | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [customCategory, setCustomCategory] = useState("");
  const [searchText, setSearchText] = useState("");
  const [filteredFAQs, setFilteredFAQs] = useState<FAQ[]>([]);

  // Fetch FAQs data
  const {
    data: faqData,
    isLoading: faqLoading,
    mutate: mutateFAQs,
  } = useSWR("/chatbot/superadmin/faqs/");

  const faqs: FAQ[] = faqData?.results || [];
  const total = faqData?.count || 0;

  // Filter FAQs based on search text
  useEffect(() => {
    if (!searchText.trim()) {
      setFilteredFAQs(faqs);
    } else {
      const filtered = faqs.filter(faq =>
        faq.question.toLowerCase().includes(searchText.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchText.toLowerCase()) ||
        faq.category?.toLowerCase().includes(searchText.toLowerCase()) ||
        faq.subcategory?.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredFAQs(filtered);
    }
  }, [faqs, searchText]);

  // Handle add FAQ
  const handleAddFAQ = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      const requestData = {
        question: values.question,
        answer: values.answer,
        category: customCategory || values.category,
        section: values.section || "Custom FAQ"
      };

      await axiosClient.post("/chatbot/superadmin/faqs/", requestData);
      
      message.success("FAQ added successfully!");
      setAddModalVisible(false);
      form.resetFields();
      setCustomCategory("");
      mutateFAQs();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Failed to add FAQ";
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle edit FAQ
  const handleEditFAQ = async () => {
    if (!selectedFAQ) return;
    
    try {
      setLoading(true);
      const values = await editForm.validateFields();
      
      const requestData = {
        question: values.question,
        answer: values.answer,
        category: values.category,
        section: values.section || "Custom FAQ"
      };

      await axiosClient.put(`/chatbot/superadmin/faqs/${selectedFAQ.id}/`, requestData);
      
      message.success("FAQ updated successfully!");
      setEditModalVisible(false);
      setSelectedFAQ(null);
      mutateFAQs();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Failed to update FAQ";
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle delete FAQ
  const handleDeleteFAQ = async (faq: FAQ) => {
    try {
      setLoading(true);
      await axiosClient.delete(`/chatbot/superadmin/faqs/${faq.id}/`);
      
      message.success("FAQ deleted successfully!");
      mutateFAQs();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Failed to delete FAQ";
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle refresh vector database
  const handleRefreshVectorDB = async () => {
    try {
      setLoading(true);
      await axiosClient.post("/chatbot/superadmin/faqs/refresh-vectors/");
      
      message.success("Vector database refreshed successfully!");
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Failed to refresh vector database";
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Open edit modal
  const openEditModal = (faq: FAQ) => {
    setSelectedFAQ(faq);
    editForm.setFieldsValue({
      question: faq.question,
      answer: faq.answer,
      category: faq.category,
      section: faq.section
    });
    setEditModalVisible(true);
  };

  // Table columns
  const columns = [
    {
      title: "Question",
      dataIndex: "question",
      key: "question",
      width: "30%",
      render: (text: string) => (
        <div className="max-w-xs">
          <p className="truncate" title={text}>{text}</p>
        </div>
      ),
    },
    {
      title: "Answer",
      dataIndex: "answer", 
      key: "answer",
      width: "35%",
      render: (text: string) => (
        <div className="max-w-sm">
          <p className="truncate" title={text}>{text}</p>
        </div>
      ),
    },
    {
      title: "Category",
      dataIndex: "category",
      key: "category",
      width: "15%",
      render: (category: string) => (
        <Tag color="blue">{category.replace(/_/g, " ").replace(/\./g, " - ")}</Tag>
      ),
    },
    {
      title: "Section",
      dataIndex: "section",
      key: "section",
      width: "10%",
    },
    {
      title: "Actions",
      key: "actions",
      width: "10%",
      render: (_: any, record: FAQ) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<FiEdit2 />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title="Delete FAQ"
            description="Are you sure you want to delete this FAQ?"
            onConfirm={() => handleDeleteFAQ(record)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<FiTrash2 />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">FAQ Management</h1>
        <p className="text-gray-600">
          Manage FAQ entries that will be automatically indexed in the vector database for real-time chatbot responses.
        </p>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: "manage",
            label: "Manage FAQs",
            children: (
              <Card>
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-4">
                    <h3 className="text-lg font-semibold">FAQ Entries ({total})</h3>
                    <Button
                      type="default"
                      icon={<FiRefreshCw />}
                      onClick={() => mutateFAQs()}
                      loading={faqLoading}
                    >
                      Refresh
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      type="default"
                      icon={<FiDatabase />}
                      onClick={handleRefreshVectorDB}
                      loading={loading}
                    >
                      Refresh Vector DB
                    </Button>
                    <Button
                      type="primary"
                      icon={<FiPlus />}
                      onClick={() => setAddModalVisible(true)}
                    >
                      Add FAQ
                    </Button>
                  </div>
                </div>

                <div className="mb-4">
                  <Input.Search
                    placeholder="Search FAQs by question, answer, or category..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    style={{ width: '100%', maxWidth: 500 }}
                    allowClear
                  />
                </div>

                <Table
                  dataSource={filteredFAQs}
                  columns={columns}
                  loading={faqLoading}
                  rowKey="chunk_id"
                  pagination={{
                    total: filteredFAQs.length,
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} of ${total} items`,
                  }}
                />
              </Card>
            )
          },
          {
            key: "categories",
            label: "Categories",
            children: (
              <Card>
                <h3 className="text-lg font-semibold mb-4">FAQ Categories</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {FAQ_CATEGORIES.map((category) => (
                    <Card key={category.key} size="small">
                      <h4 className="font-medium text-blue-600 mb-2">
                        {category.label}
                      </h4>
                      <div className="space-y-1">
                        {category.subcategories?.map((sub) => (
                          <Tag key={sub} className="mb-1">
                            {sub.replace(/_/g, " ")}
                          </Tag>
                        ))}
                      </div>
                    </Card>
                  ))}
                </div>
              </Card>
            )
          }
        ]}
      />

      {/* Add FAQ Modal */}
      <Modal
        title="Add New FAQ"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          form.resetFields();
          setCustomCategory("");
        }}
        footer={[
          <Button key="cancel" onClick={() => setAddModalVisible(false)}>
            Cancel
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={loading}
            onClick={handleAddFAQ}
          >
            Add FAQ
          </Button>,
        ]}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="question"
            label="Question"
            rules={[{ required: true, message: "Please enter the question" }]}
          >
            <Input placeholder="Type the student question..." />
          </Form.Item>

          <Form.Item
            name="answer"
            label="Answer"
            rules={[{ required: true, message: "Please enter the answer" }]}
          >
            <TextArea
              rows={4}
              placeholder="Type the answer..."
            />
          </Form.Item>

          <Form.Item
            name="category"
            label="Category"
            rules={[{ required: !customCategory, message: "Please select a category or enter custom" }]}
          >
            <Select
              placeholder="Select a category"
              allowClear
              onChange={(value) => {
                if (value !== "custom") {
                  setCustomCategory("");
                }
              }}
            >
              {FAQ_CATEGORIES.map((category) =>
                category.subcategories?.map((sub) => (
                  <Option key={`${category.key}.${sub}`} value={`${category.key}.${sub}`}>
                    {category.label} - {sub.replace(/_/g, " ")}
                  </Option>
                ))
              )}
              <Option value="custom">Custom Category</Option>
            </Select>
          </Form.Item>

          {(form.getFieldValue("category") === "custom" || customCategory) && (
            <Form.Item
              label="Custom Category"
              rules={[{ required: true, message: "Please enter custom category" }]}
            >
              <Input
                placeholder="Enter custom category (e.g., technical_support.api_issues)"
                value={customCategory}
                onChange={(e) => setCustomCategory(e.target.value)}
              />
            </Form.Item>
          )}

          <Form.Item
            name="section"
            label="Section"
          >
            <Input placeholder="Section name (optional)" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit FAQ Modal */}
      <Modal
        title="Edit FAQ"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedFAQ(null);
        }}
        footer={[
          <Button key="cancel" onClick={() => setEditModalVisible(false)}>
            Cancel
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={loading}
            onClick={handleEditFAQ}
          >
            Update FAQ
          </Button>,
        ]}
        width={700}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="question"
            label="Question"
            rules={[{ required: true, message: "Please enter the question" }]}
          >
            <Input placeholder="Type the student question..." />
          </Form.Item>

          <Form.Item
            name="answer"
            label="Answer"
            rules={[{ required: true, message: "Please enter the answer" }]}
          >
            <TextArea
              rows={4}
              placeholder="Type the answer..."
            />
          </Form.Item>

          <Form.Item
            name="category"
            label="Category"
            rules={[{ required: true, message: "Please select a category" }]}
          >
            <Select placeholder="Select a category">
              {FAQ_CATEGORIES.map((category) =>
                category.subcategories?.map((sub) => (
                  <Option key={`${category.key}.${sub}`} value={`${category.key}.${sub}`}>
                    {category.label} - {sub.replace(/_/g, " ")}
                  </Option>
                ))
              )}
            </Select>
          </Form.Item>

          <Form.Item
            name="section"
            label="Section"
          >
            <Input placeholder="Section name (optional)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
