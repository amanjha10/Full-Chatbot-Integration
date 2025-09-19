import {
  Checkbox,
  ColorPicker,
  // type CheckboxProps,
  Button,
  Input,
  Switch,
  message,
} from "antd";
import { useState, useEffect } from "react";
import { AiOutlineLike } from "react-icons/ai";
import { FaBars } from "react-icons/fa6";
import { MdAttachFile } from "react-icons/md";
import { RxCross2 } from "react-icons/rx";
import { axiosClient } from "../config/axiosConfig";
import ChatbotEmbedCode from "../components/admin/ChatbotEmbedCode";
import { useCompany } from "../context-provider/CompanyProvider";

interface ChatbotConfig {
  id?: number;
  primary_color: string;
  secondary_color: string;
  position: string;
  iframe_width: number;
  iframe_height: number;
  welcome_message: string;
  company_name: string;
  company_logo_url?: string;
  enable_file_upload: boolean;
  enable_voice_messages: boolean;
  enable_typing_indicator: boolean;
}

export default function Settings() {
  const [messageApi, contextHolder] = message.useMessage();
  const [loading, setLoading] = useState(false);
  const { companyId } = useCompany(); // Get company ID from context for proper isolation

  const [config, setConfig] = useState<ChatbotConfig>({
    primary_color: "#f7941d",
    secondary_color: "#652d90",
    position: "bottom-right",
    iframe_width: 400,
    iframe_height: 600,
    welcome_message: "Hello! How can I help you today?",
    company_name: "SpellBot Assistant",
    company_logo_url: "",
    enable_file_upload: true,
    enable_voice_messages: false,
    enable_typing_indicator: true,
  });

  // Load current configuration
  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      // Get user's company_id from localStorage or context
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      const company_id = user.company_id || "TEST001";

      const response = await axiosClient.get(
        `/chatbot/configuration/?company_id=${company_id}`
      );
      if (response.data) {
        setConfig(response.data);
      }
    } catch (error) {
      console.error("Failed to load configuration:", error);
      messageApi.error("Failed to load chatbot configuration");
    }
  };

  const saveConfiguration = async () => {
    setLoading(true);
    try {
      // Clean the config data to avoid null values
      const cleanConfig = {
        primary_color: config.primary_color || "#f7941d",
        secondary_color: config.secondary_color || "#652d90",
        position: config.position || "bottom-right",
        iframe_width: Number(config.iframe_width) || 400,
        iframe_height: Number(config.iframe_height) || 600,
        welcome_message: config.welcome_message || "",
        company_name: config.company_name || "",
        company_logo_url: config.company_logo_url || "",
        enable_file_upload: Boolean(config.enable_file_upload),
        enable_voice_messages: Boolean(config.enable_voice_messages),
        enable_typing_indicator: Boolean(config.enable_typing_indicator),
        company_id: companyId || "UNKNOWN", // Use company ID from context
      };

      console.log("Sending config data:", cleanConfig);

      // Update both the main chatbot configuration and the embed configuration
      await Promise.all([
        axiosClient.put("/chatbot/configuration/update/", cleanConfig),
        axiosClient.post("/chatbot/update-chatbot-config/", {
          company_id: companyId,
          primary_color: cleanConfig.primary_color,
          secondary_color: cleanConfig.secondary_color,
          position: cleanConfig.position,
          welcome_message: cleanConfig.welcome_message,
          iframe_width: cleanConfig.iframe_width,
          iframe_height: cleanConfig.iframe_height,
          enable_file_upload: cleanConfig.enable_file_upload
        })
      ]);

      messageApi.success("Chatbot configuration updated successfully!");
      // Reload configuration to get updated data
      await loadConfiguration();
    } catch (error: any) {
      console.error("Save configuration error:", error);
      console.error("Error response data:", error?.response?.data);
      messageApi.error(
        error?.response?.data?.error || "Failed to update configuration"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleColorChange = (
    field: "primary_color" | "secondary_color",
    color: any
  ) => {
    setConfig((prev) => ({
      ...prev,
      [field]: typeof color === "string" ? color : color.toHexString(),
    }));
  };

  const handlePositionChange = (vertical: string, horizontal: string) => {
    setConfig((prev) => ({
      ...prev,
      position: `${vertical}-${horizontal}`,
    }));
  };

  const [vertical, horizontal] = config.position.split("-");

  return (
    <>
      {contextHolder}
      <div className="mt-4 space-y-6">
        <div className="flex justify-between items-center">
          <h3 className="font-bold text-2xl">Chatbot Configuration</h3>
          <Button
            type="primary"
            loading={loading}
            onClick={saveConfiguration}
            size="large"
          >
            Save Changes
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuration Panel */}
          <div className="space-y-6">
            {/* Colors */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h4 className="font-semibold text-lg mb-4">Colors</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-3">
                    Primary Color
                  </label>
                  <div className="flex gap-4 items-center p-3 bg-gray-50 rounded-lg border">
                    <ColorPicker
                      value={config.primary_color}
                      onChange={(color) =>
                        handleColorChange("primary_color", color)
                      }
                      showText
                      size="large"
                      className="flex-shrink-0"
                    />
                    <Input
                      value={config.primary_color}
                      onChange={(e) =>
                        handleColorChange("primary_color", e.target.value)
                      }
                      placeholder="#f7941d"
                      className="w-36 font-mono text-sm"
                      style={{ fontFamily: "monospace" }}
                    />
                    <div
                      className="w-8 h-8 rounded border-2 border-gray-300 flex-shrink-0"
                      style={{ backgroundColor: config.primary_color }}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-3">
                    Secondary Color
                  </label>
                  <div className="flex gap-4 items-center p-3 bg-gray-50 rounded-lg border">
                    <ColorPicker
                      value={config.secondary_color}
                      onChange={(color) =>
                        handleColorChange("secondary_color", color)
                      }
                      showText
                      size="large"
                      className="flex-shrink-0"
                    />
                    <Input
                      value={config.secondary_color}
                      onChange={(e) =>
                        handleColorChange("secondary_color", e.target.value)
                      }
                      placeholder="#652d90"
                      className="w-36 font-mono text-sm"
                      style={{ fontFamily: "monospace" }}
                    />
                    <div
                      className="w-8 h-8 rounded border-2 border-gray-300 flex-shrink-0"
                      style={{ backgroundColor: config.secondary_color }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Position */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h4 className="font-semibold text-lg mb-4">Position</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Vertical Position
                  </label>
                  <div className="flex gap-4">
                    <Checkbox
                      checked={vertical === "top"}
                      onChange={() => handlePositionChange("top", horizontal)}
                    >
                      Top
                    </Checkbox>
                    <Checkbox
                      checked={vertical === "bottom"}
                      onChange={() =>
                        handlePositionChange("bottom", horizontal)
                      }
                    >
                      Bottom
                    </Checkbox>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Horizontal Position
                  </label>
                  <div className="flex gap-4">
                    <Checkbox
                      checked={horizontal === "left"}
                      onChange={() => handlePositionChange(vertical, "left")}
                    >
                      Left
                    </Checkbox>
                    <Checkbox
                      checked={horizontal === "right"}
                      onChange={() => handlePositionChange(vertical, "right")}
                    >
                      Right
                    </Checkbox>
                  </div>
                </div>
              </div>
            </div>
            {/* Dimensions */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h4 className="font-semibold text-lg mb-4">Dimensions</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Width (px)
                  </label>
                  <Input
                    type="number"
                    value={config.iframe_width}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        iframe_width: parseInt(e.target.value) || 400,
                      }))
                    }
                    min={300}
                    max={600}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Height (px)
                  </label>
                  <Input
                    type="number"
                    value={config.iframe_height}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        iframe_height: parseInt(e.target.value) || 600,
                      }))
                    }
                    min={400}
                    max={800}
                  />
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h4 className="font-semibold text-lg mb-4">
                Messages & Branding
              </h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Welcome Message
                  </label>
                  <Input.TextArea
                    value={config.welcome_message}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        welcome_message: e.target.value,
                      }))
                    }
                    placeholder="Hello! How can I help you today?"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Company Name
                  </label>
                  <Input
                    value={config.company_name}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        company_name: e.target.value,
                      }))
                    }
                    placeholder="Your Company Name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Company Logo URL (Optional)
                  </label>
                  <Input
                    value={config.company_logo_url}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        company_logo_url: e.target.value,
                      }))
                    }
                    placeholder="https://example.com/logo.png"
                  />
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h4 className="font-semibold text-lg mb-4">Features</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">File Upload</span>
                  <Switch
                    checked={config.enable_file_upload}
                    onChange={(checked) =>
                      setConfig((prev) => ({
                        ...prev,
                        enable_file_upload: checked,
                      }))
                    }
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Voice Messages</span>
                  <Switch
                    checked={config.enable_voice_messages}
                    onChange={(checked) =>
                      setConfig((prev) => ({
                        ...prev,
                        enable_voice_messages: checked,
                      }))
                    }
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Typing Indicator</span>
                  <Switch
                    checked={config.enable_typing_indicator}
                    onChange={(checked) =>
                      setConfig((prev) => ({
                        ...prev,
                        enable_typing_indicator: checked,
                      }))
                    }
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h4 className="font-semibold text-lg mb-4">Preview</h4>
            <div className="relative">
              <div
                className="h-[60px] rounded-t-md px-5 pt-4"
                style={{ backgroundColor: config.primary_color }}
              >
                <div className="flex justify-between items-center">
                  <span className="text-white font-medium">
                    {config.company_name}
                  </span>
                  <div className="flex gap-3 items-center">
                    <FaBars className="text-white text-xl" />
                    <RxCross2 className="text-white text-xl" />
                  </div>
                </div>
              </div>
              <div className="h-[400px] rounded-b-md border border-gray-300 flex flex-col justify-end px-3 pb-3 bg-gray-50">
                <div className="mb-4">
                  <div
                    className="text-white rounded-lg px-3 py-2 w-fit max-w-[80%] mb-2"
                    style={{ backgroundColor: config.secondary_color }}
                  >
                    {config.welcome_message}
                  </div>
                  <div className="flex justify-end mb-2">
                    <div
                      className="rounded-lg px-3 py-2 w-fit max-w-[80%] border"
                      style={{
                        color: config.primary_color,
                        borderColor: config.primary_color,
                      }}
                    >
                      I have a question
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <div
                      className="rounded-lg px-3 py-2 w-fit max-w-[80%] border"
                      style={{
                        color: config.primary_color,
                        borderColor: config.primary_color,
                      }}
                    >
                      Tell me more
                    </div>
                  </div>
                </div>
                <div className="border-t border-gray-300 pt-3">
                  <div className="flex justify-between items-center">
                    <input
                      type="text"
                      placeholder="Type a message..."
                      className="flex-1 rounded-lg px-3 py-2 border border-gray-300 outline-none text-sm"
                      disabled
                    />
                    <div className="flex gap-2 ml-2">
                      {config.enable_file_upload && (
                        <MdAttachFile className="text-gray-400 text-xl" />
                      )}
                      <AiOutlineLike className="text-gray-400 text-xl" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Dynamic Chatbot Embed Code */}
            <div className="mt-6">
              <ChatbotEmbedCode />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
