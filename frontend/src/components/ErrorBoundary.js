import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * ErrorBoundary: previne ecranul alb in cazul erorilor React necaptate.
 * Afiseaza un mesaj prietenos cu buton de reincarcare.
 * Util in special in modul offline unde pierderea conexiunii cu backend-ul
 * poate cauza crash-uri neasteptate.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorCount: 0 };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Eroare captata:', error, errorInfo);
    // Incrementeaza contorul de erori in localStorage (pentru debug)
    try {
      const count = parseInt(localStorage.getItem('andrepau_error_count') || '0', 10) + 1;
      localStorage.setItem('andrepau_error_count', String(count));
      localStorage.setItem('andrepau_last_error', JSON.stringify({
        message: error?.message || 'Unknown',
        stack: error?.stack?.substring(0, 500) || '',
        at: new Date().toISOString()
      }));
    } catch { /* localStorage might be full */ }

    // Auto-reload dupa 3 secunde daca e prima eroare in ultima ora
    try {
      const lastReload = parseInt(localStorage.getItem('andrepau_last_auto_reload') || '0', 10);
      const now = Date.now();
      if (now - lastReload > 3600000) { // 1 hour cooldown
        localStorage.setItem('andrepau_last_auto_reload', String(now));
        setTimeout(() => {
          window.location.reload();
        }, 3000);
      }
    } catch { /* ignore */ }
  }

  handleReload = () => {
    // Clear potential bad state
    try {
      localStorage.removeItem('andrepau_pos_cart');
    } catch { /* ignore */ }
    window.location.reload();
  };

  handleHardReset = () => {
    // Clear all local data (except token)
    try {
      const token = localStorage.getItem('andrepau_token');
      localStorage.clear();
      if (token) localStorage.setItem('andrepau_token', token);
    } catch { /* ignore */ }
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-6" data-testid="error-boundary">
          <div className="max-w-md w-full bg-card border border-destructive/30 rounded-lg p-6 space-y-4">
            <div className="flex items-center gap-3 text-destructive">
              <AlertTriangle className="w-8 h-8" />
              <h1 className="font-heading text-2xl uppercase">Eroare aplicatie</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Aplicatia a intampinat o problema. Aplicatia se reincarca automat in cateva secunde.
            </p>
            {this.state.error?.message && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded text-xs font-mono text-destructive/80 break-all max-h-24 overflow-auto">
                {this.state.error.message}
              </div>
            )}
            <div className="flex flex-col gap-2">
              <button
                onClick={this.handleReload}
                className="w-full h-12 bg-primary text-primary-foreground font-bold rounded flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors"
                data-testid="error-reload-btn"
              >
                <RefreshCw className="w-5 h-5" />
                Reincarca aplicatia
              </button>
              <button
                onClick={this.handleHardReset}
                className="w-full h-10 bg-secondary text-secondary-foreground text-sm rounded hover:bg-secondary/80 transition-colors"
                data-testid="error-hard-reset-btn"
              >
                Reset complet (pastreaza login-ul)
              </button>
            </div>
            <p className="text-xs text-muted-foreground text-center">
              Daca problema persista, reporneste aplicatia din meniul Windows (ANDREPAU.bat).
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
