import React, { useState, useEffect, useCallback } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  ShoppingCart, 
  Package, 
  Archive, 
  BarChart3, 
  Truck, 
  Settings, 
  LogOut, 
  Menu, 
  X,
  AlertTriangle,
  Wrench,
  Calculator,
  LayoutDashboard,
  Sun,
  Moon,
  Wifi,
  Monitor,
  RefreshCw,
  CloudUpload,
  Loader2
} from 'lucide-react';
import { cn } from '../lib/utils';
import { toast } from 'sonner';

const isLocalMode = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

const navigation = [
  { name: 'Deschidere Zi', href: '/start-day', icon: LayoutDashboard, roles: ['admin', 'casier'] },
  { name: 'POS / Vanzare', href: '/pos', icon: ShoppingCart, roles: ['admin', 'casier'] },
  { name: 'Produse', href: '/products', icon: Package, roles: ['admin', 'casier'] },
  { name: 'Stoc & Inventar', href: '/stock', icon: Archive, roles: ['admin', 'casier'] },
  { name: 'Rapoarte', href: '/reports', icon: BarChart3, roles: ['admin', 'casier'] },
  { name: 'Furnizori', href: '/suppliers', icon: Truck, roles: ['admin'] },
  { name: 'Operațiuni Casă', href: '/cash-operations', icon: Calculator, roles: ['admin'] },
  { name: 'Setări', href: '/settings', icon: Settings, roles: ['admin'] },
];

export default function Layout() {
  const { user, logout, token, API_URL } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [stockAlerts, setStockAlerts] = useState(0);
  const [lightMode, setLightMode] = useState(() => {
    return localStorage.getItem('andrepau_theme') === 'light';
  });

  // Sync state (only relevant in local mode)
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [vpsReachable, setVpsReachable] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (lightMode) {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
    localStorage.setItem('andrepau_theme', lightMode ? 'light' : 'dark');
  }, [lightMode]);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch(`${API_URL}/stock/alerts`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setStockAlerts(data.length);
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, [API_URL, token]);

  // Local mode: check pending sync count + VPS reachability
  const checkSyncStatus = useCallback(async () => {
    if (!isLocalMode || !token) return;

    // Check pending sales count
    try {
      const resp = await fetch(`${API_URL}/sync/pending-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setPendingSyncCount(data.pending || 0);
      }
    } catch {
      // Local backend not reachable
    }

    // Check VPS reachability
    const vpsUrl = localStorage.getItem('andrepau_vps_url');
    if (vpsUrl) {
      try {
        const ctrl = new AbortController();
        const timeout = setTimeout(() => ctrl.abort(), 5000);
        const resp = await fetch(`${vpsUrl}/api/sync/health`, { signal: ctrl.signal });
        clearTimeout(timeout);
        setVpsReachable(resp.ok);
      } catch {
        setVpsReachable(false);
      }
    }
  }, [API_URL, token]);

  useEffect(() => {
    if (!isLocalMode) return;
    checkSyncStatus();
    const interval = setInterval(checkSyncStatus, 30000);
    return () => clearInterval(interval);
  }, [checkSyncStatus]);

  // Sync handler
  const handleSync = async () => {
    const vpsUrl = localStorage.getItem('andrepau_vps_url');
    if (!vpsUrl) {
      toast.error('Configurati URL-ul VPS in Setari > Sincronizare');
      return;
    }

    setSyncing(true);
    try {
      // 1. Get pending sales from local
      const pendingResp = await fetch(`${API_URL}/sync/pending-sales`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!pendingResp.ok) throw new Error('Nu pot citi vanzarile locale');
      const { sales } = await pendingResp.json();

      if (!sales || sales.length === 0) {
        toast.info('Nu exista vanzari de sincronizat');
        setSyncing(false);
        return;
      }

      // 2. Send to VPS
      const syncSecret = localStorage.getItem('andrepau_sync_secret') || 'andrepau-sync-2026';
      const syncResp = await fetch(`${vpsUrl}/api/sync/receive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sync_secret: syncSecret, sales })
      });

      if (!syncResp.ok) throw new Error('VPS a refuzat sincronizarea');
      const syncResult = await syncResp.json();

      // 3. Mark as synced locally
      const saleIds = sales.map(s => s.id);
      await fetch(`${API_URL}/sync/mark-done`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ sale_ids: saleIds })
      });

      toast.success(`Sincronizare completa! ${syncResult.received} vanzari trimise la VPS`);
      setPendingSyncCount(0);
      checkSyncStatus();
    } catch (err) {
      toast.error(`Eroare sincronizare: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const filteredNav = navigation.filter(item => item.roles.includes(user?.role));

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-sm flex items-center justify-center">
                <Wrench className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="font-heading text-xl uppercase tracking-tight text-foreground">
                  ANDREPAU
                </h1>
                <p className="text-xs text-muted-foreground">POS System</p>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 text-muted-foreground hover:text-foreground"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Connection mode indicator */}
          <div className={cn(
            "mx-3 mt-3 px-3 py-2 rounded-sm flex items-center gap-2 text-xs font-medium",
            isLocalMode 
              ? "bg-blue-500/10 border border-blue-500/20 text-blue-400" 
              : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
          )} data-testid="connection-mode-indicator">
            {isLocalMode ? <Monitor className="w-3.5 h-3.5" /> : <Wifi className="w-3.5 h-3.5" />}
            <span>{isLocalMode ? 'MOD LOCAL (Offline)' : 'ONLINE (VPS)'}</span>
          </div>

          {/* Sync banner - only in local mode with pending sales */}
          {isLocalMode && pendingSyncCount > 0 && (
            <div className="mx-3 mt-2 px-3 py-2 rounded-sm bg-amber-500/10 border border-amber-500/20" data-testid="sync-banner">
              <div className="flex items-center gap-2 text-xs text-amber-400 font-medium">
                <CloudUpload className="w-3.5 h-3.5" />
                <span>{pendingSyncCount} vanzari nesincronizate</span>
              </div>
              {vpsReachable ? (
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  data-testid="sync-now-btn"
                  className="mt-1.5 w-full flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-sm bg-amber-500 text-black text-xs font-bold hover:bg-amber-400 transition-colors disabled:opacity-50"
                >
                  {syncing ? (
                    <><Loader2 className="w-3 h-3 animate-spin" /> Sincronizare...</>
                  ) : (
                    <><RefreshCw className="w-3 h-3" /> Sincronizeaza acum</>
                  )}
                </button>
              ) : (
                <p className="mt-1 text-[10px] text-amber-500/60">Asteptare internet pentru sincronizare...</p>
              )}
            </div>
          )}

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="px-2 space-y-1">
              {filteredNav.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  data-testid={`nav-${item.href.slice(1)}`}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => cn(
                    "nav-item",
                    isActive && "active"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="flex-1">{item.name}</span>
                  {item.href === '/stock' && stockAlerts > 0 && (
                    <span className="alert-badge">{stockAlerts}</span>
                  )}
                </NavLink>
              ))}
            </nav>
          </ScrollArea>

          {/* User info & Logout */}
          <div className="p-4 border-t border-border">
            {/* Theme Toggle */}
            <button
              onClick={() => setLightMode(!lightMode)}
              className="w-full flex items-center gap-3 px-3 py-2.5 mb-3 rounded-sm text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
              data-testid="theme-toggle-btn"
            >
              {lightMode ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              <span>{lightMode ? 'Mod Inchis' : 'Mod Deschis'}</span>
            </button>

            {stockAlerts > 0 && (
              <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-sm flex items-center gap-2 text-sm text-yellow-500">
                <AlertTriangle className="w-4 h-4" />
                <span>{stockAlerts} produse cu stoc scăzut</span>
              </div>
            )}
            
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-secondary rounded-sm flex items-center justify-center">
                <span className="text-lg font-bold text-foreground">
                  {user?.full_name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{user?.full_name}</p>
                <p className="text-xs text-muted-foreground uppercase">{user?.role}</p>
              </div>
            </div>
            
            <Button
              onClick={handleLogout}
              variant="outline"
              data-testid="logout-btn"
              className="w-full h-12 border-border text-foreground hover:bg-destructive/10 hover:text-destructive hover:border-destructive"
            >
              <LogOut className="w-5 h-5 mr-2" />
              Deconectare
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between h-16 px-4 border-b border-border bg-card">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 text-muted-foreground hover:text-foreground"
            data-testid="mobile-menu-btn"
          >
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="font-heading text-lg uppercase text-foreground">ANDREPAU</h1>
          <div className="w-10" /> {/* Spacer */}
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
