import React from 'react'
import { ConfigProvider } from "antd";
import { SWRConfig, type SWRConfiguration } from 'swr'
import type { AxiosRequestConfig } from 'axios';
import { axiosClient } from '../config/axiosConfig';
import { MessageProvider } from '../context-provider/MessageProvider';
const fetcher=(resources:string,init:AxiosRequestConfig)=>{
  if(resources.includes("undefined")) return
  return axiosClient(resources,init).then((res)=>res?.data)
}
const refetchOptions: SWRConfiguration = {
  revalidateOnFocus: false,
  refreshWhenOffline: false,
  refreshWhenHidden: false,
  refreshInterval: 0,
  shouldRetryOnError: false
}
export default function AppProvider({children}:{children:React.ReactNode}) {
  return (
<ConfigProvider
theme={{
    token:{
         colorPrimary: '#f7941d',
    }
}}>
  <SWRConfig value={{fetcher,...refetchOptions}}>
    <MessageProvider>
{children}
    </MessageProvider>

  </SWRConfig>

</ConfigProvider>
  )
}
