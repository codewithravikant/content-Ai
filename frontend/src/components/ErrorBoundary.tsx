import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[#020617]">
          <div className="space-y-4 max-w-md text-center">
            <h2 className="text-2xl font-black text-red-500 uppercase tracking-tighter">
              Something went wrong
            </h2>
            <p className="text-slate-400 text-sm">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button 
              onClick={this.handleReset}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-bold rounded-xl hover:from-cyan-400 hover:to-indigo-500 transition-all uppercase tracking-wider text-sm"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
