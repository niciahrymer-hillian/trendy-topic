// Catches render-time errors in the routed page so a crash shows a readable
// message in the content area instead of blanking the whole app to a black screen.

import { Component, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown) {
    // Surfaced in the terminal/devtools too, for good measure.
    console.error("Page crashed:", error, info);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div className="card" style={{ margin: 24 }}>
        <h2 style={{ color: "var(--danger)" }}>This page hit an error</h2>
        <pre style={{ whiteSpace: "pre-wrap", color: "var(--danger)", fontSize: 13 }}>{error.message}</pre>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 11, opacity: 0.7, overflow: "auto", maxHeight: 260 }}>{error.stack}</pre>
        <button className="primary" onClick={() => this.setState({ error: null })}>Retry</button>
      </div>
    );
  }
}
