  import { message } from "antd";
import  { createContext,useContext } from 'react';

   type MessageContextType = {
  messageApi: ReturnType<typeof message.useMessage>[0];
  contextHolder: React.ReactElement;
};

const MessageContext = createContext<MessageContextType | null>(null);
export const useMessageContext = () => {
  const context = useContext(MessageContext);
  if (!context) {
    throw new Error("useMessageContext must be used within a MessageProvider");
  }
  return context;
};

export const MessageProvider = ({children}:{children:React.ReactNode}) => {
      const [messageApi, contextHolder] = message.useMessage();
  return (
        <MessageContext.Provider value={{ messageApi, contextHolder }}>
      {contextHolder}
      {children}
    </MessageContext.Provider>

  )
}