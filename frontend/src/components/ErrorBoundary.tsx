import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertCircle, RotateCcw, Home } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error caught by ErrorBoundary:", error, errorInfo);
  }

  public handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[360px] flex items-center justify-center p-6" role="alert" aria-live="assertive">
          <div className="card w-full max-w-md p-6 text-center space-y-4 shadow-soft">
            <span className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-coral-soft text-coral-deep">
              <AlertCircle size={28} />
            </span>
            <h2 className="text-xl font-bold text-ink-900">Something went wrong</h2>
            <p className="text-sm text-ink-500 leading-relaxed">
              We couldn't load this section of the page. Your progress and data are safely saved on the server.
            </p>
            {import.meta.env.DEV && this.state.error && (
              <pre className="text-left bg-sage p-3 rounded-xl text-xs text-ink-700 overflow-x-auto max-h-32">
                {this.state.error.message}
              </pre>
            )}
            <div className="flex gap-2 justify-center pt-2">
              <button onClick={this.handleRetry} className="btn-primary flex items-center gap-1.5 text-xs">
                <RotateCcw size={14} /> Retry
              </button>
              <a href="/" className="btn-soft flex items-center gap-1.5 text-xs">
                <Home size={14} /> Return Home
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
