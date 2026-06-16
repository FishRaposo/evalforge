"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string;
}

/**
 * Catches render-time errors in the dashboard subtree and shows a recoverable
 * fallback instead of a blank white screen.
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("Dashboard ErrorBoundary caught:", error, info);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, message: "" });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div
          role="alert"
          className="m-6 rounded-xl border border-rose-500/30 bg-rose-900/10 p-6 text-rose-300"
        >
          <h2 className="text-lg font-bold mb-2">Something went wrong</h2>
          <p className="text-sm text-rose-200/80 mb-4">
            The dashboard hit an unexpected error while rendering.
            {this.state.message ? ` (${this.state.message})` : ""}
          </p>
          <button
            type="button"
            onClick={this.handleReset}
            className="rounded bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-500"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
