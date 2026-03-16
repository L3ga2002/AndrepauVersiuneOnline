import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  FileText, FileCheck, ArrowDownCircle, ArrowUpCircle, 
  Wallet, History, AlertTriangle, CheckCircle, XCircle, 
  Loader2, RefreshCw, Settings2, Wifi, WifiOff, Download
} from 'lucide-react';
import { toast } from 'sonner';
import { formatCurrency } from '../lib/utils';

const DEFAULT_BRIDGE_URL = 'http://localhost:5555';

export default function CashOperationsPage() {
  const { user, token, API_URL } = useAuth();
  const [loading, setLoading] = useState(false);
  const [bridgeStatus, setBridgeStatus] = useState({ connected: false, status: 'CHECKING' });
  
  const [showCashIn, setShowCashIn] = useState(false);
  const [showCashOut, setShowCashOut] = useState(false);
  const [showReportZ, setShowReportZ] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  const [cashAmount, setCashAmount] = useState('');
  const [cashReason, setCashReason] = useState('');
  const [operations, setOperations] = useState([]);
  const [dailyStats, setDailyStats] = useState({
    totalCash: 0, totalCard: 0, totalVoucher: 0,
    cashIn: 0, cashOut: 0, receiptsCount: 0
  });

  // Bridge URL from localStorage
  const [bridgeUrl, setBridgeUrl] = useState(() => {
    return localStorage.getItem('andrepau_bridge_url') || DEFAULT_BRIDGE_URL;
  });
  const [bridgeUrlInput, setBridgeUrlInput] = useState(bridgeUrl);

  // Bridge status - check via cloud backend (not localhost)
  const checkBridgeStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/fiscal/bridge-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBridgeStatus({ 
          connected: data.connected, 
          status: data.connected ? 'CONNECTED' : 'DISCONNECTED',
          lastPoll: data.last_poll
        });
      } else {
        setBridgeStatus({ connected: false, status: 'ERROR' });
      }
    } catch {
      setBridgeStatus({ connected: false, status: 'DISCONNECTED' });
    }
  }, [API_URL, token]);

  const fetchDailyStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/cash-operations/daily-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) setDailyStats(await response.json());
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [API_URL, token]);

  useEffect(() => {
    checkBridgeStatus();
    fetchDailyStats();
    const interval = setInterval(checkBridgeStatus, 15000);
    return () => clearInterval(interval);
  }, [checkBridgeStatus, fetchDailyStats]);

  const fetchOperationsHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/cash-operations/history?limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setOperations(data.operations || []);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  // Fiscal operations via cloud backend (bridge polls from there)
  const callBridge = async (jobType, data = {}) => {
    try {
      const response = await fetch(`${API_URL}/fiscal/queue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ type: jobType, data })
      });
      
      if (!response.ok) throw new Error('Eroare trimitere comanda');
      const { job_id } = await response.json();
      
      // Poll for result (max 35 seconds)
      for (let i = 0; i < 35; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const statusResp = await fetch(`${API_URL}/fiscal/status/${job_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (statusResp.ok) {
          const job = await statusResp.json();
          if (job.status === 'completed' || job.status === 'failed') {
            return job.result || { success: job.status === 'completed', message: job.status };
          }
        }
      }
      return { success: false, message: 'Timeout - bridge-ul nu raspunde. Verificati ca e pornit!' };
    } catch (err) {
      return { success: false, message: `Eroare: ${err.message}` };
    }
  };

  const saveOperation = async (type, amount, description) => {
    try {
      await fetch(`${API_URL}/cash-operations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          type, amount, description,
          operator_id: user.id, operator_name: user.username
        })
      });
    } catch (error) {
      console.error('Error saving operation:', error);
    }
  };

  const handleReportX = async () => {
    if (!bridgeStatus.connected) {
      toast.error('Bridge-ul nu este conectat!');
      return;
    }
    setLoading(true);
    const result = await callBridge('report_x');
    if (result.success) {
      toast.success('Raport X printat cu succes');
      await saveOperation('REPORT_X', 0, 'Raport X zilnic');
    } else {
      toast.error(result.message || 'Eroare la Raport X');
    }
    setLoading(false);
  };

  const handleReportZ = async () => {
    if (!bridgeStatus.connected) {
      toast.error('Bridge-ul nu este conectat!');
      return;
    }
    setLoading(true);
    const result = await callBridge('report_z');
    if (result.success) {
      toast.success('Raport Z printat - Ziua fiscala inchisa!');
      await saveOperation('REPORT_Z', 0, 'Inchidere zi fiscala');
      fetchDailyStats();
    } else {
      toast.error(result.message || 'Eroare la Raport Z');
    }
    setLoading(false);
    setShowReportZ(false);
  };

  const handleCashIn = async () => {
    const amount = parseFloat(cashAmount);
    if (!amount || amount <= 0) { toast.error('Introduceti o suma valida'); return; }
    if (!bridgeStatus.connected) { toast.error('Bridge-ul nu este conectat!'); return; }
    
    setLoading(true);
    const result = await callBridge('cash_in', { amount, reason: cashReason || 'Intrare numerar' });
    if (result.success) {
      toast.success(`Intrare ${formatCurrency(amount)} inregistrata`);
      await saveOperation('CASH_IN', amount, cashReason || 'Intrare numerar');
      fetchDailyStats();
      setShowCashIn(false);
      setCashAmount('');
      setCashReason('');
    } else {
      toast.error(result.message || 'Eroare la intrare numerar');
    }
    setLoading(false);
  };

  const handleCashOut = async () => {
    const amount = parseFloat(cashAmount);
    if (!amount || amount <= 0) { toast.error('Introduceti o suma valida'); return; }
    if (!bridgeStatus.connected) { toast.error('Bridge-ul nu este conectat!'); return; }
    
    setLoading(true);
    const result = await callBridge('cash_out', { amount, reason: cashReason || 'Extragere numerar' });
    if (result.success) {
      toast.success(`Extragere ${formatCurrency(amount)} inregistrata`);
      await saveOperation('CASH_OUT', amount, cashReason || 'Extragere numerar');
      fetchDailyStats();
      setShowCashOut(false);
      setCashAmount('');
      setCashReason('');
    } else {
      toast.error(result.message || 'Eroare la extragere numerar');
    }
    setLoading(false);
  };

  const handleOpenDrawer = async () => {
    if (!bridgeStatus.connected) { toast.error('Bridge-ul nu este conectat!'); return; }
    const result = await callBridge('drawer');
    if (result.success) toast.success('Sertar deschis');
    else toast.error(result.message || 'Eroare la deschidere sertar');
  };

  const saveBridgeUrl = () => {
    const url = bridgeUrlInput.trim();
    if (!url) return;
    localStorage.setItem('andrepau_bridge_url', url);
    setBridgeUrl(url);
    setShowSettings(false);
    toast.success('URL Bridge salvat');
    setTimeout(checkBridgeStatus, 500);
  };

  const currentCashBalance = dailyStats.totalCash + dailyStats.cashIn - dailyStats.cashOut;

  return (
    <div className="p-4 md:p-6 space-y-6" data-testid="cash-operations-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-foreground">Operatiuni Casa</h1>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            className="text-xs"
            onClick={() => {
              const ts = Date.now();
              window.location.href = `${API_URL}/bridge/download-direct?token=${token}&v=${ts}`;
            }}
            data-testid="header-download-bridge-btn"
          >
            <Download className="w-4 h-4 mr-1" />
            Descarca Bridge
          </Button>
          <div 
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm cursor-pointer ${
              bridgeStatus.connected ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
            }`}
            onClick={checkBridgeStatus}
            data-testid="bridge-status"
          >
            {bridgeStatus.connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            {bridgeStatus.connected ? 'Casa conectata' : 'Casa deconectata'}
          </div>
          <Button variant="outline" size="icon" onClick={() => setShowSettings(true)} data-testid="bridge-settings-btn">
            <Settings2 className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={checkBridgeStatus} data-testid="refresh-status-btn">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Alerta deconectat */}
      {!bridgeStatus.connected && (
        <Card className="border-red-500/50 bg-red-500/10" data-testid="bridge-disconnected-alert">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-red-500">Bridge Service nu este pornit!</p>
              <p className="text-sm text-muted-foreground mt-1">Pe PC-ul din magazin:</p>
              <ol className="text-sm text-muted-foreground mt-1 list-decimal ml-4 space-y-0.5">
                <li>Descarcati fisierele Bridge (butonul de mai jos)</li>
                <li>Dezarhivati ZIP-ul pe Desktop</li>
                <li>Dublu-click pe <strong>install_bridge.bat</strong> (o singura data)</li>
                <li>Porniti <strong>SuccesDrv</strong> si apasati <strong>"Start procesare"</strong></li>
                <li>Dublu-click pe <strong>start_bridge.bat</strong></li>
                <li>Deschideti <strong>http://localhost:5555/test</strong> pentru verificare</li>
              </ol>
              <Button
                className="mt-3 bg-primary hover:bg-primary/90"
                onClick={() => {
                  const ts = Date.now();
                  window.location.href = `${API_URL}/bridge/download-direct?token=${token}&v=${ts}`;
                }}
                data-testid="download-bridge-btn"
              >
                <Download className="w-4 h-4 mr-2" />
                Descarca Bridge Service (ZIP)
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info bridge conectat */}
      {bridgeStatus.connected && bridgeStatus.path && (
        <Card className="border-green-500/30 bg-green-500/5">
          <CardContent className="p-3 flex items-center gap-3 text-sm">
            <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
            <span className="text-muted-foreground flex-1">
              Bridge conectat | Cale: <code className="text-green-400">{bridgeStatus.path}</code>
              {bridgeStatus.exeFound ? ' | SuccesDrv.exe gasit' : ''}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const ts = Date.now();
                window.location.href = `${API_URL}/bridge/download-direct?token=${token}&v=${ts}`;
              }}
              data-testid="download-bridge-btn-connected"
            >
              <Download className="w-4 h-4 mr-1" />
              Actualizare Bridge
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Statistici zilnice */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-green-500/10 border-green-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Wallet className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Sold Casa</p>
                <p className="text-2xl font-bold text-green-500" data-testid="cash-balance">
                  {formatCurrency(currentCashBalance)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-500/10 border-blue-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <ArrowDownCircle className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">Incasari Cash</p>
                <p className="text-2xl font-bold text-blue-500" data-testid="total-cash">
                  {formatCurrency(dailyStats.totalCash)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-purple-500/10 border-purple-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <ArrowUpCircle className="w-8 h-8 text-purple-500" />
              <div>
                <p className="text-sm text-muted-foreground">Incasari Card</p>
                <p className="text-2xl font-bold text-purple-500" data-testid="total-card">
                  {formatCurrency(dailyStats.totalCard)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-orange-500/10 border-orange-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-orange-500" />
              <div>
                <p className="text-sm text-muted-foreground">Bonuri Azi</p>
                <p className="text-2xl font-bold text-orange-500" data-testid="receipts-count">
                  {dailyStats.receiptsCount}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Butoane operatiuni */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card 
          className={`cursor-pointer transition-colors ${bridgeStatus.connected ? 'hover:bg-secondary/50' : 'opacity-60'}`}
          onClick={handleReportX}
          data-testid="report-x-btn"
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center">
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="font-semibold text-lg">Raport X</h3>
            <p className="text-sm text-muted-foreground text-center">Raport fara inchidere zi</p>
            {loading && <Loader2 className="w-5 h-5 animate-spin" />}
          </CardContent>
        </Card>

        <Card 
          className={`cursor-pointer transition-colors border-red-500/30 ${bridgeStatus.connected ? 'hover:bg-secondary/50' : 'opacity-60'}`}
          onClick={() => bridgeStatus.connected && setShowReportZ(true)}
          data-testid="report-z-btn"
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
              <FileCheck className="w-8 h-8 text-red-500" />
            </div>
            <h3 className="font-semibold text-lg text-red-500">Raport Z</h3>
            <p className="text-sm text-muted-foreground text-center">Inchide ziua fiscala</p>
          </CardContent>
        </Card>

        <Card 
          className={`cursor-pointer transition-colors ${bridgeStatus.connected ? 'hover:bg-secondary/50' : 'opacity-60'}`}
          onClick={() => bridgeStatus.connected && setShowCashIn(true)}
          data-testid="cash-in-btn"
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center">
              <ArrowDownCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="font-semibold text-lg">Intrare Bani</h3>
            <p className="text-sm text-muted-foreground text-center">Adauga numerar in casa</p>
          </CardContent>
        </Card>

        <Card 
          className={`cursor-pointer transition-colors ${bridgeStatus.connected ? 'hover:bg-secondary/50' : 'opacity-60'}`}
          onClick={() => bridgeStatus.connected && setShowCashOut(true)}
          data-testid="cash-out-btn"
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center">
              <ArrowUpCircle className="w-8 h-8 text-orange-500" />
            </div>
            <h3 className="font-semibold text-lg">Extragere Bani</h3>
            <p className="text-sm text-muted-foreground text-center">Scoate numerar din casa</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors"
          onClick={() => { fetchOperationsHistory(); setShowHistory(true); }}
          data-testid="history-btn"
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center">
              <History className="w-8 h-8 text-purple-500" />
            </div>
            <h3 className="font-semibold text-lg">Istoric</h3>
            <p className="text-sm text-muted-foreground text-center">Vezi operatiunile</p>
          </CardContent>
        </Card>

        <Card 
          className={`cursor-pointer transition-colors ${bridgeStatus.connected ? 'hover:bg-secondary/50' : 'opacity-60'}`}
          onClick={handleOpenDrawer}
          data-testid="open-drawer-btn"
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-gray-500/20 flex items-center justify-center">
              <Wallet className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="font-semibold text-lg">Deschide Sertar</h3>
            <p className="text-sm text-muted-foreground text-center">Deschide sertarul de bani</p>
          </CardContent>
        </Card>
      </div>

      {/* Dialog Confirmare Raport Z */}
      <Dialog open={showReportZ} onOpenChange={setShowReportZ}>
        <DialogContent className="bg-card border-red-500">
          <DialogHeader>
            <DialogTitle className="text-red-500 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6" />
              Confirmare Raport Z
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-lg font-medium text-foreground mb-2">
              Aceasta actiune va inchide ziua fiscala!
            </p>
            <p className="text-muted-foreground">
              Raportul Z reseteaza toate totalurile zilnice si nu poate fi anulat.
              Asigurati-va ca ati terminat toate vanzarile pentru azi.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowReportZ(false)}>Anuleaza</Button>
            <Button className="bg-red-600 hover:bg-red-700" onClick={handleReportZ} disabled={loading} data-testid="confirm-report-z">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <FileCheck className="w-5 h-5 mr-2" />}
              Confirm - Inchide Ziua
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Intrare Bani */}
      <Dialog open={showCashIn} onOpenChange={setShowCashIn}>
        <DialogContent className="bg-card">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-500">
              <ArrowDownCircle className="w-6 h-6" />
              Intrare Bani in Casa
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm text-muted-foreground">Suma (RON) *</label>
              <Input type="number" step="0.01" value={cashAmount} onChange={(e) => setCashAmount(e.target.value)}
                className="h-14 text-2xl font-mono text-center mt-1" placeholder="0.00" autoFocus data-testid="cash-in-amount" />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Motiv (optional)</label>
              <Input value={cashReason} onChange={(e) => setCashReason(e.target.value)}
                className="h-12 mt-1" placeholder="Ex: Sold initial, Rest de la banca..." data-testid="cash-in-reason" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCashIn(false)}>Anuleaza</Button>
            <Button className="bg-green-600 hover:bg-green-700" onClick={handleCashIn} disabled={loading || !cashAmount} data-testid="confirm-cash-in">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <ArrowDownCircle className="w-5 h-5 mr-2" />}
              Inregistreaza Intrare
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Extragere Bani */}
      <Dialog open={showCashOut} onOpenChange={setShowCashOut}>
        <DialogContent className="bg-card">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-orange-500">
              <ArrowUpCircle className="w-6 h-6" />
              Extragere Bani din Casa
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-3 bg-secondary/50 rounded-lg">
              <p className="text-sm text-muted-foreground">Sold curent casa:</p>
              <p className="text-xl font-bold text-green-500">{formatCurrency(currentCashBalance)}</p>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Suma de extras (RON) *</label>
              <Input type="number" step="0.01" value={cashAmount} onChange={(e) => setCashAmount(e.target.value)}
                className="h-14 text-2xl font-mono text-center mt-1" placeholder="0.00" autoFocus data-testid="cash-out-amount" />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Motiv (optional)</label>
              <Input value={cashReason} onChange={(e) => setCashReason(e.target.value)}
                className="h-12 mt-1" placeholder="Ex: Depunere banca, Plata furnizor..." data-testid="cash-out-reason" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCashOut(false)}>Anuleaza</Button>
            <Button className="bg-orange-600 hover:bg-orange-700" onClick={handleCashOut} disabled={loading || !cashAmount} data-testid="confirm-cash-out">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <ArrowUpCircle className="w-5 h-5 mr-2" />}
              Inregistreaza Extragere
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Istoric */}
      <Dialog open={showHistory} onOpenChange={setShowHistory}>
        <DialogContent className="bg-card max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="w-6 h-6 text-purple-500" />
              Istoric Operatiuni
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-96">
            <div className="space-y-2">
              {operations.length === 0 ? (
                <p className="text-center text-muted-foreground py-8" data-testid="no-operations">
                  Nu exista operatiuni inregistrate
                </p>
              ) : (
                operations.map((op, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg" data-testid={`operation-${idx}`}>
                    <div className="flex items-center gap-3">
                      {op.type === 'CASH_IN' && <ArrowDownCircle className="w-5 h-5 text-green-500" />}
                      {op.type === 'CASH_OUT' && <ArrowUpCircle className="w-5 h-5 text-orange-500" />}
                      {op.type === 'REPORT_X' && <FileText className="w-5 h-5 text-blue-500" />}
                      {op.type === 'REPORT_Z' && <FileCheck className="w-5 h-5 text-red-500" />}
                      <div>
                        <p className="font-medium">{op.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(op.timestamp).toLocaleString('ro-RO')} {op.operator_name && `| ${op.operator_name}`}
                        </p>
                      </div>
                    </div>
                    {op.amount > 0 && (
                      <span className={`font-bold ${op.type === 'CASH_IN' ? 'text-green-500' : op.type === 'CASH_OUT' ? 'text-orange-500' : ''}`}>
                        {op.type === 'CASH_OUT' ? '-' : '+'}{formatCurrency(op.amount)}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHistory(false)}>Inchide</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Setari Bridge */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="bg-card">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings2 className="w-6 h-6 text-primary" />
              Setari Bridge Service
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm text-muted-foreground">URL Bridge Service</label>
              <Input value={bridgeUrlInput} onChange={(e) => setBridgeUrlInput(e.target.value)}
                className="h-12 mt-1 font-mono" placeholder="http://localhost:5555" data-testid="bridge-url-input" />
              <p className="text-xs text-muted-foreground mt-1">
                De obicei: http://localhost:5555 (rulat pe acelasi PC)
              </p>
            </div>
            <div className="p-3 bg-secondary/30 rounded-lg text-sm space-y-1">
              <p className="font-medium text-foreground">Status conexiune:</p>
              <p className="flex items-center gap-2">
                {bridgeStatus.connected ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                {bridgeStatus.connected ? 'Conectat' : 'Deconectat'}
              </p>
              {bridgeStatus.path && <p className="text-muted-foreground">Cale: {bridgeStatus.path}</p>}
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowSettings(false)}>Anuleaza</Button>
            <Button onClick={saveBridgeUrl} className="bg-primary" data-testid="save-bridge-url">Salveaza</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
