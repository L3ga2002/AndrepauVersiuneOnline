import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ScrollArea } from '../components/ui/scroll-area';
import { Button } from '../components/ui/button';
import { formatCurrency, formatNumber, formatDate } from '../lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { TrendingUp, ShoppingCart, CreditCard, Banknote, Receipt, Download, Calendar, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';

const COLORS = ['#f59e0b', '#3b82f6', '#22c55e', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export default function ReportsPage() {
  const { token, API_URL, isAdmin } = useAuth();
  const [period, setPeriod] = useState('today');
  const [salesReport, setSalesReport] = useState({ total_sales: 0, total_tva: 0, count: 0, cash: 0, card: 0 });
  const [profitReport, setProfitReport] = useState({ total_vanzari: 0, total_cost: 0, profit: 0, margin_percent: 0 });
  const [topProducts, setTopProducts] = useState([]);
  const [topCategories, setTopCategories] = useState([]);
  const [dailySales, setDailySales] = useState([]);
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedSale, setExpandedSale] = useState(null);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const [salesRes, profitRes, topProdRes, topCatRes, dailyRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/reports/sales?period=${period}`, { headers: { Authorization: `Bearer ${token}` } }),
        isAdmin ? fetch(`${API_URL}/reports/profit?period=${period}`, { headers: { Authorization: `Bearer ${token}` } }) : null,
        fetch(`${API_URL}/reports/top-products?limit=10`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/reports/top-categories`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/reports/daily-sales?days=30`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/sales`, { headers: { Authorization: `Bearer ${token}` } })
      ]);

      setSalesReport(await salesRes.json());
      if (profitRes) setProfitReport(await profitRes.json());
      setTopProducts(await topProdRes.json());
      setTopCategories(await topCatRes.json());
      setDailySales(await dailyRes.json());
      setSales(await historyRes.json());
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token, period, isAdmin]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const exportCSV = () => {
    const headers = ['Nr. Bon', 'Data', 'Total', 'TVA', 'Metoda Plată', 'Casier'];
    const rows = sales.map(s => [
      s.numar_bon,
      formatDate(s.created_at),
      s.total.toFixed(2),
      s.tva_total.toFixed(2),
      s.metoda_plata,
      s.casier_nume
    ]);
    
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `raport_vanzari_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    toast.success('Raport exportat cu succes');
  };

  const getPeriodLabel = () => {
    switch (period) {
      case 'today': return 'Astăzi';
      case 'week': return 'Ultima săptămână';
      case 'month': return 'Luna curentă';
      case 'year': return 'Anul curent';
      default: return '';
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="reports-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl uppercase tracking-tight text-foreground">
            Rapoarte
          </h1>
          <p className="text-muted-foreground mt-1">
            Statistici și analize vânzări
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger data-testid="period-select" className="w-48 h-12 bg-card border-border text-foreground">
              <Calendar className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-card border-border">
              <SelectItem value="today">Astăzi</SelectItem>
              <SelectItem value="week">Ultima săptămână</SelectItem>
              <SelectItem value="month">Luna curentă</SelectItem>
              <SelectItem value="year">Anul curent</SelectItem>
            </SelectContent>
          </Select>

          <Button
            data-testid="export-csv"
            onClick={exportCSV}
            variant="outline"
            className="h-12 border-border text-foreground"
          >
            <Download className="w-5 h-5 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Vânzări {getPeriodLabel()}
                </CardTitle>
                <TrendingUp className="w-5 h-5 text-primary" />
              </CardHeader>
              <CardContent>
                <p className="font-mono text-3xl font-bold text-foreground" data-testid="total-sales">
                  {formatCurrency(salesReport.total_sales)}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {salesReport.count} tranzacții
                </p>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Numerar</CardTitle>
                <Banknote className="w-5 h-5 text-green-500" />
              </CardHeader>
              <CardContent>
                <p className="font-mono text-3xl font-bold text-green-500" data-testid="cash-total">
                  {formatCurrency(salesReport.cash)}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Card</CardTitle>
                <CreditCard className="w-5 h-5 text-blue-500" />
              </CardHeader>
              <CardContent>
                <p className="font-mono text-3xl font-bold text-blue-500" data-testid="card-total">
                  {formatCurrency(salesReport.card)}
                </p>
              </CardContent>
            </Card>

            {isAdmin && (
              <Card className="bg-card border-border border-l-4 border-l-primary">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Profit</CardTitle>
                  <ShoppingCart className="w-5 h-5 text-primary" />
                </CardHeader>
                <CardContent>
                  <p className="font-mono text-3xl font-bold text-primary" data-testid="profit-total">
                    {formatCurrency(profitReport.profit)}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Marjă: {formatNumber(profitReport.margin_percent, 1)}%
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Daily Sales Chart */}
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-lg uppercase text-foreground">
                  Evoluție Vânzări (30 zile)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dailySales}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis 
                        dataKey="date" 
                        stroke="#a1a1aa"
                        tick={{ fill: '#a1a1aa', fontSize: 12 }}
                        tickFormatter={(v) => v.slice(5)}
                      />
                      <YAxis 
                        stroke="#a1a1aa"
                        tick={{ fill: '#a1a1aa', fontSize: 12 }}
                        tickFormatter={(v) => `${v} RON`}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '4px' }}
                        labelStyle={{ color: '#fafafa' }}
                        formatter={(value) => [formatCurrency(value), 'Vânzări']}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="total" 
                        stroke="#f59e0b" 
                        strokeWidth={2}
                        dot={{ fill: '#f59e0b', r: 3 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Categories Pie Chart */}
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-lg uppercase text-foreground">
                  Vânzări pe Categorii
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={topCategories}
                        dataKey="total_valoare"
                        nameKey="categorie"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={({ categorie, percent }) => `${categorie} (${(percent * 100).toFixed(0)}%)`}
                        labelLine={{ stroke: '#a1a1aa' }}
                      >
                        {topCategories.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '4px' }}
                        formatter={(value) => [formatCurrency(value), 'Valoare']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Products & Sales History */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Products */}
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-lg uppercase text-foreground">
                  Top 10 Produse Vândute
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={topProducts} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis 
                        type="number" 
                        stroke="#a1a1aa"
                        tick={{ fill: '#a1a1aa', fontSize: 12 }}
                      />
                      <YAxis 
                        type="category" 
                        dataKey="nume" 
                        stroke="#a1a1aa"
                        tick={{ fill: '#a1a1aa', fontSize: 11 }}
                        width={150}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '4px' }}
                        formatter={(value) => [formatCurrency(value), 'Valoare']}
                      />
                      <Bar dataKey="total_valoare" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Sales History */}
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-lg uppercase text-foreground">
                  Istoric Bonuri
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-80">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border">
                        <TableHead className="text-muted-foreground">Nr. Bon</TableHead>
                        <TableHead className="text-muted-foreground">Data</TableHead>
                        <TableHead className="text-muted-foreground text-right">Total</TableHead>
                        <TableHead className="text-muted-foreground">Plată</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sales.slice(0, 20).map(sale => (
                        <React.Fragment key={sale.id}>
                          <TableRow 
                            data-testid={`sale-row-${sale.id}`} 
                            className="border-border cursor-pointer hover:bg-secondary/30 transition-colors"
                            onClick={() => setExpandedSale(expandedSale === sale.id ? null : sale.id)}
                          >
                            <TableCell className="font-mono text-sm text-foreground">
                              <div className="flex items-center gap-2">
                                {expandedSale === sale.id ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                                {sale.numar_bon}
                              </div>
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {formatDate(sale.created_at)}
                            </TableCell>
                            <TableCell className="text-right font-mono font-bold text-primary">
                              {formatCurrency(sale.total)}
                            </TableCell>
                            <TableCell>
                              <span className={`text-xs uppercase font-medium ${
                                sale.metoda_plata === 'numerar' ? 'text-green-500' :
                                sale.metoda_plata === 'card' ? 'text-blue-500' : 'text-purple-500'
                              }`}>
                                {sale.metoda_plata}
                              </span>
                            </TableCell>
                          </TableRow>
                          {expandedSale === sale.id && (
                            <TableRow className="border-border bg-secondary/20">
                              <TableCell colSpan={4} className="p-0">
                                <div className="px-8 py-3 space-y-1" data-testid={`sale-details-${sale.id}`}>
                                  <p className="text-xs text-muted-foreground uppercase mb-2 font-semibold">
                                    Produse pe bon ({sale.items?.length || 0} articole) | Casier: {sale.casier_nume}
                                  </p>
                                  {sale.items?.map((item, idx) => (
                                    <div key={idx} className="flex items-center justify-between py-1 text-sm border-b border-border/50 last:border-0">
                                      <span className="text-foreground flex-1">{item.nume}</span>
                                      <span className="text-muted-foreground font-mono w-20 text-right">{item.cantitate} x</span>
                                      <span className="text-foreground font-mono w-24 text-right">{formatCurrency(item.pret_unitar)}</span>
                                      <span className="text-primary font-mono font-bold w-28 text-right">{formatCurrency(item.cantitate * item.pret_unitar)}</span>
                                    </div>
                                  ))}
                                  <div className="flex justify-between pt-2 text-xs text-muted-foreground">
                                    <span>TVA: {formatCurrency(sale.tva_total)}</span>
                                    {sale.discount_percent > 0 && <span>Discount: {sale.discount_percent}%</span>}
                                    {sale.fiscal_number && <span>Nr. fiscal: {sale.fiscal_number}</span>}
                                  </div>
                                </div>
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
