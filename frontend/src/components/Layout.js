import React, { useState, useEffect } from 'react';
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
  Wrench
} from 'lucide-react';
import { cn } from '../lib/utils';

const navigation = [
  { name: 'POS / Vânzare', href: '/pos', icon: ShoppingCart, roles: ['admin', 'casier'] },
  { name: 'Produse', href: '/products', icon: Package, roles: ['admin', 'casier'] },
  { name: 'Stoc & Inventar', href: '/stock', icon: Archive, roles: ['admin', 'casier'] },
  { name: 'Rapoarte', href: '/reports', icon: BarChart3, roles: ['admin', 'casier'] },
  { name: 'Furnizori', href: '/suppliers', icon: Truck, roles: ['admin'] },
  { name: 'Setări', href: '/settings', icon: Settings, roles: ['admin'] },
];

export default function Layout() {
  const { user, logout, token, API_URL } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [stockAlerts, setStockAlerts] = useState(0);

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
    const interval = setInterval(fetchAlerts, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [API_URL, token]);

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
