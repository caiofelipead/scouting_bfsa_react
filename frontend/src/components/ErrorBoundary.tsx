import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('[ErrorBoundary]', error, info.componentStack);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: '2rem',
          textAlign: 'center',
          color: '#e2e8f0',
        }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#f87171' }}>
            Algo deu errado
          </h2>
          <p style={{ marginBottom: '1.5rem', color: '#94a3b8', maxWidth: '400px' }}>
            Ocorreu um erro inesperado. Tente recarregar a pagina.
          </p>
          {import.meta.env.DEV && this.state.error && (
            <pre style={{
              background: '#1e293b',
              padding: '1rem',
              borderRadius: '0.5rem',
              fontSize: '0.75rem',
              maxWidth: '600px',
              overflow: 'auto',
              marginBottom: '1rem',
              color: '#fbbf24',
            }}>
              {this.state.error.message}
            </pre>
          )}
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={this.handleRetry}
              style={{
                padding: '0.5rem 1.5rem',
                borderRadius: '0.5rem',
                border: 'none',
                background: '#3b82f6',
                color: 'white',
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
            >
              Tentar novamente
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '0.5rem 1.5rem',
                borderRadius: '0.5rem',
                border: '1px solid #475569',
                background: 'transparent',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
            >
              Recarregar pagina
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
