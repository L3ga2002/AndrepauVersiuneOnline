import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  FileText, 
  FileCheck, 
  ArrowDownCircle, 
  ArrowUpCircle, 
  Wallet, 
  History, 
  AlertTriangle,
  Printer,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { formatCurrency } from '../lib/utils';

// URL-ul Bridge Service (rulează local pe PC-ul din magazin)
const BRIDGE_URL = 'http://localhost:5555';

export default function CashOperationsPage() {
  const { user, token, API_URL } = useAuth();
  const [loading, setLoading] = useState(false);
  const [bridgeStatus, setBridgeStatus] = useState({ connected: false, status: 'CHECKING' });
  
  // Dialog states
  const [showCashIn, setShowCashIn] = useState(false);
  const [showCashOut, setShowCashOut] = useState(false);
  const [showReportZ, setShowReportZ] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  
  // Form states
  const [cashAmount, setCashAmount] = useState('');
  const [cashReason, setCashReason] = useState('');
  
  // History & Stats
  const [operations, setOperations] = useState([]);
  const [dailyStats, setDailyStats] = useState({
    totalCash: 0,
    totalCard: 0,
    totalVoucher: 0,
    cashIn: 0,
    cashOut: 0,
    receiptsCount: 0
  });

  // Check bridge connection on mount
  useEffect(() => {
    checkBridgeStatus();
    fetchDailyStats();
    const interval = setInterval(checkBridgeStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkBridgeStatus = async () => {
    try {
      const response = await fetch(`${BRIDGE_URL}/health`, {
        method: 'GET',
        timeout: 5000
      });
      
      if (response.ok) {
        const data = await response.json();
        setBridgeStatus({ connected: true, status: 'CONNECTED' });
      } else {
        setBridgeStatus({ connected: false, status: 'ERROR' });
      }
    } catch (error) {
      setBridgeStatus({ connected: false, status: 'DISCONNECTED' });
    }
  };

  const fetchDailyStats = async () => {
    try {
      const response = await fetch(`${API_URL}/cash-operations/daily-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDailyStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

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

  // ==================== FISCAL OPERATIONS ====================

  const handleReportX = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BRIDGE_URL}/fiscal/report/x`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success('Raport X printat cu succes');
        await saveOperation('REPORT_X', 0, 'Raport X zilnic');
      } else {
        toast.error(result.message || 'Eroare la printare Raport X');
      }
    } catch (error) {
      toast.error('Nu se poate comunica cu casa de marcat. Verificați Bridge Service.');
    } finally {
      setLoading(false);
    }
  };

  const handleReportZ = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BRIDGE_URL}/fiscal/report/z`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success('Raport Z printat - Ziua fiscală închisă!');
        await saveOperation('REPORT_Z', 0, 'Închidere zi fiscală');
        fetchDailyStats();
      } else {
        toast.error(result.message || 'Eroare la printare Raport Z');
      }
    } catch (error) {
      toast.error('Nu se poate comunica cu casa de marcat. Verificați Bridge Service.');
    } finally {
      setLoading(false);
      setShowReportZ(false);
    }
  };

  const handleCashIn = async () => {
    const amount = parseFloat(cashAmount);
    if (!amount || amount <= 0) {
      toast.error('Introduceți o sumă validă');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${BRIDGE_URL}/fiscal/cash/in`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: amount,
          reason: cashReason || 'Intrare numerar'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Intrare ${formatCurrency(amount)} înregistrată`);
        await saveOperation('CASH_IN', amount, cashReason || 'Intrare numerar');
        fetchDailyStats();
        setShowCashIn(false);
        setCashAmount('');
        setCashReason('');
      } else {
        toast.error(result.message || 'Eroare la înregistrare intrare');
      }
    } catch (error) {
      toast.error('Nu se poate comunica cu casa de marcat');
    } finally {
      setLoading(false);
    }
  };

  const handleCashOut = async () => {
    const amount = parseFloat(cashAmount);
    if (!amount || amount <= 0) {
      toast.error('Introduceți o sumă validă');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${BRIDGE_URL}/fiscal/cash/out`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: amount,
          reason: cashReason || 'Extragere numerar'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Extragere ${formatCurrency(amount)} înregistrată`);
        await saveOperation('CASH_OUT', amount, cashReason || 'Extragere numerar');
        fetchDailyStats();
        setShowCashOut(false);
        setCashAmount('');
        setCashReason('');
      } else {
        toast.error(result.message || 'Eroare la înregistrare extragere');
      }
    } catch (error) {
      toast.error('Nu se poate comunica cu casa de marcat');
    } finally {
      setLoading(false);
    }
  };

  const saveOperation = async (type, amount, description) => {
    try {
      await fetch(`${API_URL}/cash-operations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          type,
          amount,
          description,
          operator_id: user.id,
          operator_name: user.username
        })
      });
    } catch (error) {
      console.error('Error saving operation:', error);
    }
  };

  // Calculate current cash balance
  const currentCashBalance = dailyStats.totalCash + dailyStats.cashIn - dailyStats.cashOut;

  return (
    <div className="p-4 md:p-6 space-y-6" data-testid="cash-operations-page">
      {/* Header cu status conexiune */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Operațiuni Casă</h1>
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
            bridgeStatus.connected 
              ? 'bg-green-500/20 text-green-500' 
              : 'bg-red-500/20 text-red-500'
          }`}>
            {bridgeStatus.connected ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <XCircle className="w-4 h-4" />
            )}
            {bridgeStatus.connected ? 'Casa conectată' : 'Casa deconectată'}
          </div>
          <Button variant="outline" size="sm" onClick={checkBridgeStatus}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Alertă dacă bridge nu e conectat */}
      {!bridgeStatus.connected && (
        <Card className="border-red-500 bg-red-500/10">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-red-500" />
            <div>
              <p className="font-medium text-red-500">Bridge Service nu este pornit!</p>
              <p className="text-sm text-muted-foreground">
                Rulați fiscal_bridge.py pe PC-ul din magazin pentru a conecta casa de marcat.
              </p>
            </div>
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
                <p className="text-sm text-muted-foreground">Sold Casă</p>
                <p className="text-2xl font-bold text-green-500">
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
                <p className="text-sm text-muted-foreground">Încasări Cash</p>
                <p className="text-2xl font-bold text-blue-500">
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
                <p className="text-sm text-muted-foreground">Încasări Card</p>
                <p className="text-2xl font-bold text-purple-500">
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
                <p className="text-2xl font-bold text-orange-500">
                  {dailyStats.receiptsCount}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Butoane operațiuni */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {/* Raport X */}
        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors"
          onClick={handleReportX}
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center">
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="font-semibold text-lg">Raport X</h3>
            <p className="text-sm text-muted-foreground text-center">
              Raport fără închidere zi
            </p>
            {loading && <Loader2 className="w-5 h-5 animate-spin" />}
          </CardContent>
        </Card>

        {/* Raport Z */}
        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors border-red-500/30"
          onClick={() => setShowReportZ(true)}
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
              <FileCheck className="w-8 h-8 text-red-500" />
            </div>
            <h3 className="font-semibold text-lg text-red-500">Raport Z</h3>
            <p className="text-sm text-muted-foreground text-center">
              Închide ziua fiscală
            </p>
          </CardContent>
        </Card>

        {/* Intrare bani */}
        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors"
          onClick={() => setShowCashIn(true)}
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center">
              <ArrowDownCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="font-semibold text-lg">Intrare Bani</h3>
            <p className="text-sm text-muted-foreground text-center">
              Adaugă numerar în casă
            </p>
          </CardContent>
        </Card>

        {/* Extragere bani */}
        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors"
          onClick={() => setShowCashOut(true)}
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center">
              <ArrowUpCircle className="w-8 h-8 text-orange-500" />
            </div>
            <h3 className="font-semibold text-lg">Extragere Bani</h3>
            <p className="text-sm text-muted-foreground text-center">
              Scoate numerar din casă
            </p>
          </CardContent>
        </Card>

        {/* Istoric */}
        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors"
          onClick={() => {
            fetchOperationsHistory();
            setShowHistory(true);
          }}
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center">
              <History className="w-8 h-8 text-purple-500" />
            </div>
            <h3 className="font-semibold text-lg">Istoric</h3>
            <p className="text-sm text-muted-foreground text-center">
              Vezi operațiunile
            </p>
          </CardContent>
        </Card>

        {/* Deschide sertar */}
        <Card 
          className="cursor-pointer hover:bg-secondary/50 transition-colors"
          onClick={async () => {
            try {
              await fetch(`${BRIDGE_URL}/fiscal/drawer/open`, { method: 'POST' });
              toast.success('Sertar deschis');
            } catch (error) {
              toast.error('Eroare la deschidere sertar');
            }
          }}
        >
          <CardContent className="p-6 flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-gray-500/20 flex items-center justify-center">
              <Wallet className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="font-semibold text-lg">Deschide Sertar</h3>
            <p className="text-sm text-muted-foreground text-center">
              Deschide sertarul de bani
            </p>
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
              Atenție! Această acțiune va închide ziua fiscală!
            </p>
            <p className="text-muted-foreground">
              Raportul Z resetează toate totalurile zilnice și nu poate fi anulat.
              Asigurați-vă că ați terminat toate vânzările pentru azi.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowReportZ(false)}>
              Anulează
            </Button>
            <Button 
              className="bg-red-600 hover:bg-red-700"
              onClick={handleReportZ}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
              ) : (
                <FileCheck className="w-5 h-5 mr-2" />
              )}
              Confirm - Închide Ziua
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
              Intrare Bani în Casă
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm text-muted-foreground">Sumă (RON) *</label>
              <Input
                type="number"
                step="0.01"
                value={cashAmount}
                onChange={(e) => setCashAmount(e.target.value)}
                className="h-14 text-2xl font-mono text-center mt-1"
                placeholder="0.00"
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Motiv (opțional)</label>
              <Input
                value={cashReason}
                onChange={(e) => setCashReason(e.target.value)}
                className="h-12 mt-1"
                placeholder="Ex: Sold inițial, Rest de la bancă..."
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCashIn(false)}>
              Anulează
            </Button>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={handleCashIn}
              disabled={loading || !cashAmount}
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
              ) : (
                <ArrowDownCircle className="w-5 h-5 mr-2" />
              )}
              Înregistrează Intrare
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
              Extragere Bani din Casă
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-3 bg-secondary/50 rounded-lg">
              <p className="text-sm text-muted-foreground">Sold curent casă:</p>
              <p className="text-xl font-bold text-green-500">{formatCurrency(currentCashBalance)}</p>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Sumă de extras (RON) *</label>
              <Input
                type="number"
                step="0.01"
                value={cashAmount}
                onChange={(e) => setCashAmount(e.target.value)}
                className="h-14 text-2xl font-mono text-center mt-1"
                placeholder="0.00"
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Motiv (opțional)</label>
              <Input
                value={cashReason}
                onChange={(e) => setCashReason(e.target.value)}
                className="h-12 mt-1"
                placeholder="Ex: Depunere bancă, Plată furnizor..."
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCashOut(false)}>
              Anulează
            </Button>
            <Button 
              className="bg-orange-600 hover:bg-orange-700"
              onClick={handleCashOut}
              disabled={loading || !cashAmount}
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
              ) : (
                <ArrowUpCircle className="w-5 h-5 mr-2" />
              )}
              Înregistrează Extragere
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
              Istoric Operațiuni
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-96">
            <div className="space-y-2">
              {operations.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  Nu există operațiuni înregistrate
                </p>
              ) : (
                operations.map((op, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {op.type === 'CASH_IN' && <ArrowDownCircle className="w-5 h-5 text-green-500" />}
                      {op.type === 'CASH_OUT' && <ArrowUpCircle className="w-5 h-5 text-orange-500" />}
                      {op.type === 'REPORT_X' && <FileText className="w-5 h-5 text-blue-500" />}
                      {op.type === 'REPORT_Z' && <FileCheck className="w-5 h-5 text-red-500" />}
                      <div>
                        <p className="font-medium">{op.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(op.timestamp).toLocaleString('ro-RO')} • {op.operator_name}
                        </p>
                      </div>
                    </div>
                    {op.amount > 0 && (
                      <span className={`font-bold ${
                        op.type === 'CASH_IN' ? 'text-green-500' : 
                        op.type === 'CASH_OUT' ? 'text-orange-500' : ''
                      }`}>
                        {op.type === 'CASH_OUT' ? '-' : '+'}{formatCurrency(op.amount)}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHistory(false)}>
              Închide
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
