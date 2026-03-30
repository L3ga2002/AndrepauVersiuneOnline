import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { formatCurrency } from '../lib/utils';
import { 
  Banknote, Wifi, WifiOff, ShoppingCart, AlertTriangle, 
  Package, Clock, CheckCircle, ArrowRight, RefreshCw, Loader2
} from 'lucide-react';

export default function StartDayPage() {
  const { user, token, API_URL } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [soldManual, setSoldManual] = useState('');
  const [showSoldInput, setShowSoldInput] = useState(false);

  const fetchSummary = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    try {
      const resp = await fetch(`${API_URL}/daily/opening-summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.ok) setData(await resp.json());
    } catch (err) {
      console.error('Error fetching summary:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [API_URL, token]);

  useEffect(() => { fetchSummary(); }, [fetchSummary]);

  const startDay = async () => {
    // Save manual starting balance if provided
    if (soldManual && parseFloat(soldManual) > 0) {
      try {
        await fetch(`${API_URL}/cash/operation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ type: 'CASH_IN', amount: parseFloat(soldManual), description: 'Sold inceput de zi (manual)' })
        });
      } catch {}
    }
    navigate('/pos');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const bridgeOk = data?.bridge_connected;
  const hasAlerts = (data?.alerte_stoc || 0) > 0;
  const hasHold = (data?.comenzi_hold || 0) > 0;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4" data-testid="start-day-page">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="font-heading text-4xl uppercase tracking-tight text-foreground">
            ANDREPAU
          </h1>
          <p className="text-muted-foreground">
            {new Date().toLocaleDateString('ro-RO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
          <p className="text-lg text-foreground">
            Buna ziua, <span className="text-primary font-semibold">{user?.full_name}</span>
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-2 gap-4">
          {/* Cash Balance */}
          <Card className="bg-card border-border col-span-2">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <Banknote className="w-6 h-6 text-green-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Sold Casa (numerar)</p>
                    <p className="font-mono text-3xl font-bold text-foreground" data-testid="cash-balance">
                      {formatCurrency(data?.sold_casa || 0)}
                    </p>
                  </div>
                </div>
                <div className="text-right text-sm text-muted-foreground space-y-1">
                  {data?.numar_vanzari > 0 && (
                    <p>{data.numar_vanzari} vanzari ({formatCurrency(data.total_vanzari)})</p>
                  )}
                  {data?.cash_in > 0 && <p className="text-green-500">+{formatCurrency(data.cash_in)} intrare</p>}
                  {data?.cash_out > 0 && <p className="text-red-500">-{formatCurrency(data.cash_out)} iesire</p>}
                </div>
              </div>
              {/* Manual starting balance */}
              <div className="mt-4 pt-4 border-t border-border">
                {!showSoldInput ? (
                  <button
                    onClick={() => setShowSoldInput(true)}
                    className="text-sm text-primary hover:underline"
                    data-testid="set-manual-balance-btn"
                  >
                    Seteaza sold manual de inceput de zi (optional)
                  </button>
                ) : (
                  <div className="flex items-center gap-3">
                    <label className="text-sm text-muted-foreground whitespace-nowrap">Sold initial:</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={soldManual}
                      onChange={(e) => setSoldManual(e.target.value)}
                      placeholder="0.00 RON"
                      className="flex-1 h-10 px-3 rounded-md border border-border bg-background text-foreground text-sm"
                      data-testid="manual-balance-input"
                      autoFocus
                    />
                    <button onClick={() => { setShowSoldInput(false); setSoldManual(''); }} className="text-sm text-muted-foreground hover:text-foreground">
                      Anuleaza
                    </button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Bridge Status */}
          <Card className={`border-border ${bridgeOk ? 'bg-card' : 'bg-red-500/5 border-red-500/30'}`}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${bridgeOk ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                  {bridgeOk ? <Wifi className="w-5 h-5 text-green-500" /> : <WifiOff className="w-5 h-5 text-red-500" />}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Casa de Marcat</p>
                  <p className={`font-semibold ${bridgeOk ? 'text-green-500' : 'text-red-500'}`} data-testid="bridge-status">
                    {bridgeOk ? 'Conectata' : 'Deconectata'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Held Orders */}
          <Card className={`border-border ${hasHold ? 'bg-yellow-500/5 border-yellow-500/30' : 'bg-card'}`}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${hasHold ? 'bg-yellow-500/10' : 'bg-secondary'}`}>
                  <Clock className={`w-5 h-5 ${hasHold ? 'text-yellow-500' : 'text-muted-foreground'}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Comenzi Hold</p>
                  <p className={`font-semibold ${hasHold ? 'text-yellow-500' : 'text-foreground'}`} data-testid="hold-count">
                    {data?.comenzi_hold || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Stock Alerts */}
          <Card className={`border-border col-span-2 ${hasAlerts ? 'bg-card' : 'bg-card'}`}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${hasAlerts ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                    {hasAlerts ? <AlertTriangle className="w-5 h-5 text-red-500" /> : <Package className="w-5 h-5 text-green-500" />}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Stoc</p>
                    <p className={`font-semibold ${hasAlerts ? 'text-foreground' : 'text-green-500'}`} data-testid="stock-status">
                      {hasAlerts 
                        ? `${data.fara_stoc} fara stoc, ${data.alerte_stoc} alerte`
                        : 'Stoc OK'}
                    </p>
                  </div>
                </div>
                {hasAlerts && (
                  <Button variant="ghost" size="sm" onClick={() => navigate('/stock')} className="text-muted-foreground">
                    Vezi detalii
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => fetchSummary(true)}
            disabled={refreshing}
            className="h-14 px-6"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-5 h-5 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Actualizeaza
          </Button>
          <Button
            onClick={startDay}
            className="flex-1 h-14 text-lg font-bold bg-primary hover:bg-primary/90"
            data-testid="start-day-btn"
          >
            <ShoppingCart className="w-6 h-6 mr-3" />
            INCEPE ZIUA
            <ArrowRight className="w-5 h-5 ml-3" />
          </Button>
        </div>

        {/* Checklist */}
        <div className="bg-card border border-border rounded-lg p-4 space-y-2">
          <p className="text-sm font-medium text-muted-foreground mb-3">Checklist deschidere:</p>
          <CheckItem ok={bridgeOk} label="Casa de marcat conectata" warn={!bridgeOk ? "Porneste bridge-ul de pe PC" : null} />
          <CheckItem ok={!hasHold} label="Comenzi in asteptare verificate" warn={hasHold ? `${data.comenzi_hold} comenzi nerezolvate` : null} />
          <CheckItem ok={data?.fara_stoc === 0} label="Stoc fara probleme" warn={data?.fara_stoc > 0 ? `${data.fara_stoc} produse fara stoc` : null} />
        </div>
      </div>
    </div>
  );
}

function CheckItem({ ok, label, warn }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      {ok ? (
        <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
      ) : (
        <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0" />
      )}
      <span className={ok ? 'text-muted-foreground' : 'text-foreground'}>{label}</span>
      {warn && <span className="text-xs text-yellow-500 ml-auto">{warn}</span>}
    </div>
  );
}
