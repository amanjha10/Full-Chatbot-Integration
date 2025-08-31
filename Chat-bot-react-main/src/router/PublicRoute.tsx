import React from 'react'
import { Navigate } from 'react-router-dom'

export default function PublicRoute({children}:{children:React.ReactNode}) {
     const isAuthenticated=localStorage.getItem("isAuth")=="true"
  return !isAuthenticated ?(<div>{children}</div>):<Navigate to="/app/dashboard" replace/>
}
