import { Button, Result } from "antd"
import React from "react"

interface ErrorBoundaryProps {
  children: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

function logErrorToMyService(error: Error, errorInfo: React.ErrorInfo) {
  console.error('Logged to service:', error, errorInfo)
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logErrorToMyService(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="A client-side error has occurred"
          subTitle="Please try refreshing the page."
          extra={
            <Button type="primary" className="!bg-yellow" onClick={() => window.location.reload()}>
              Try Again
            </Button>
          }
        />
      )
    }

    return this.props.children
  }
}