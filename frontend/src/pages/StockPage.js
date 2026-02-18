import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ScrollArea } from '../components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatNumber, formatDate, getStockStatus } from '../lib/utils';
import { Package, AlertTriangle, TrendingDown, Archive, Plus, Trash2, FileText } from 'lucide-react';
import { toast } from 'sonner';

export default function StockPage() {
  const { token, API_URL, isAdmin } = useAuth();
  const [dashboard, setDashboard] = useState({ total_products: 0, low_stock: 0, out_of_stock: 0, total_value: 0 });
  const [alerts, setAlerts] = useState([]);
  const [nirs, setNirs] = useState([]);
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // NIR Form
  const [showNirDialog, setShowNirDialog] = useState(false);
  const [nirForm, setNirForm] = useState({
    furnizor_id: '',
    numar_factura: '',
    items: []
  });
  const [nirItem, setNirItem] = useState({ product_id: '', cantitate: '', pret_achizitie: '' });

  const fetchDashboard = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/stock/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboard(await response.json());
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    }
  }, [API_URL, token]);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/stock/alerts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(await response.json());
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  }, [API_URL, token]);

  const fetchNirs = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/nir`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNirs(await response.json());
    } catch (error) {
      console.error('Error fetching NIRs:', error);
    }
  }, [API_URL, token]);

  const fetchProducts = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setProducts(data.products || data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  }, [API_URL, token]);

  const fetchSuppliers = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/suppliers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuppliers(await response.json());
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    }
  }, [API_URL, token]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchDashboard(), fetchAlerts(), fetchNirs(), fetchProducts(), fetchSuppliers()]);
      setLoading(false);
    };
    init();
  }, [fetchDashboard, fetchAlerts, fetchNirs, fetchProducts, fetchSuppliers]);

  const addNirItem = () => {
    if (!nirItem.product_id || !nirItem.cantitate || !nirItem.pret_achizitie) {
      toast.error('Completați toate câmpurile');
      return;
    }

    const product = products.find(p => p.id === nirItem.product_id);
    if (!product) return;

    setNirForm({
      ...nirForm,
      items: [...nirForm.items, {
        product_id: nirItem.product_id,
        nume: product.nume,
        cantitate: parseFloat(nirItem.cantitate),
        pret_achizitie: parseFloat(nirItem.pret_achizitie)
      }]
    });
    setNirItem({ product_id: '', cantitate: '', pret_achizitie: '' });
  };

  const removeNirItem = (index) => {
    setNirForm({
      ...nirForm,
      items: nirForm.items.filter((_, i) => i !== index)
    });
  };

  const calculateNirTotal = () => {
    return nirForm.items.reduce((sum, item) => sum + (item.cantitate * item.pret_achizitie), 0);
  };

  const submitNir = async () => {
    if (!nirForm.furnizor_id || !nirForm.numar_factura || nirForm.items.length === 0) {
      toast.error('Completați toate câmpurile obligatorii');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/nir`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...nirForm,
          total: calculateNirTotal()
        })
      });

      if (response.ok) {
        toast.success('NIR creat cu succes');
        setShowNirDialog(false);
        setNirForm({ furnizor_id: '', numar_factura: '', items: [] });
        fetchNirs();
        fetchDashboard();
        fetchAlerts();
        fetchProducts();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Eroare la creare NIR');
      }
    } catch (error) {
      toast.error('Eroare la creare NIR');
    }
  };

  const openNirDialog = () => {
    setNirForm({ furnizor_id: '', numar_factura: '', items: [] });
    setNirItem({ product_id: '', cantitate: '', pret_achizitie: '' });
    setShowNirDialog(true);
  };

  return (
    <div className="p-6 space-y-6" data-testid="stock-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl uppercase tracking-tight text-foreground">
            Stoc & Inventar
          </h1>
          <p className="text-muted-foreground mt-1">
            Gestionare stoc și recepție marfă
          </p>
        </div>
        
        {isAdmin && (
          <Button
            data-testid="create-nir-btn"
            onClick={openNirDialog}
            className="h-12 px-6 bg-primary text-primary-foreground"
          >
            <Plus className="w-5 h-5 mr-2" />
            Intrare Marfă (NIR)
          </Button>
        )}
      </div>

      {/* Dashboard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Produse</CardTitle>
            <Package className="w-5 h-5 text-primary" />
          </CardHeader>
          <CardContent>
            <p className="font-mono text-3xl font-bold text-foreground" data-testid="total-products">
              {dashboard.total_products}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Valoare Stoc</CardTitle>
            <Archive className="w-5 h-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <p className="font-mono text-3xl font-bold text-foreground" data-testid="stock-value">
              {formatCurrency(dashboard.total_value)}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border border-l-4 border-l-yellow-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Stoc Scăzut</CardTitle>
            <TrendingDown className="w-5 h-5 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <p className="font-mono text-3xl font-bold text-yellow-500" data-testid="low-stock">
              {dashboard.low_stock}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border border-l-4 border-l-red-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Fără Stoc</CardTitle>
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <p className="font-mono text-3xl font-bold text-red-500" data-testid="out-of-stock">
              {dashboard.out_of_stock}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="alerts" className="space-y-4">
        <TabsList className="bg-secondary">
          <TabsTrigger value="alerts" data-testid="tab-alerts" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Alerte Stoc ({alerts.length})
          </TabsTrigger>
          <TabsTrigger value="nir" data-testid="tab-nir" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Intrări Marfă (NIR)
          </TabsTrigger>
        </TabsList>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="font-heading text-xl uppercase text-foreground">
                Produse Sub Stoc Minim
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="spinner" />
                </div>
              ) : alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                  <Package className="w-12 h-12 mb-2 opacity-50" />
                  <p>Toate produsele sunt în stoc</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border">
                        <TableHead className="text-muted-foreground">Produs</TableHead>
                        <TableHead className="text-muted-foreground">Categorie</TableHead>
                        <TableHead className="text-muted-foreground text-right">Stoc Actual</TableHead>
                        <TableHead className="text-muted-foreground text-right">Stoc Minim</TableHead>
                        <TableHead className="text-muted-foreground">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {alerts.map(product => {
                        const status = getStockStatus(product.stoc, product.stoc_minim);
                        return (
                          <TableRow key={product.id} className="border-border">
                            <TableCell className="font-medium text-foreground">{product.nume}</TableCell>
                            <TableCell className="text-muted-foreground">{product.categorie}</TableCell>
                            <TableCell className={`text-right font-mono ${status.className}`}>
                              {formatNumber(product.stoc, 1)} {product.unitate}
                            </TableCell>
                            <TableCell className="text-right font-mono text-muted-foreground">
                              {formatNumber(product.stoc_minim, 1)} {product.unitate}
                            </TableCell>
                            <TableCell>
                              <span className={`badge-${status.status === 'critical' ? 'danger' : 'warning'}`}>
                                {status.label}
                              </span>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* NIR Tab */}
        <TabsContent value="nir">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="font-heading text-xl uppercase text-foreground">
                Istoric Intrări Marfă (NIR)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="spinner" />
                </div>
              ) : nirs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                  <FileText className="w-12 h-12 mb-2 opacity-50" />
                  <p>Nicio intrare de marfă</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border">
                        <TableHead className="text-muted-foreground">Nr. NIR</TableHead>
                        <TableHead className="text-muted-foreground">Data</TableHead>
                        <TableHead className="text-muted-foreground">Furnizor</TableHead>
                        <TableHead className="text-muted-foreground">Nr. Factură</TableHead>
                        <TableHead className="text-muted-foreground text-right">Produse</TableHead>
                        <TableHead className="text-muted-foreground text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {nirs.map(nir => (
                        <TableRow key={nir.id} data-testid={`nir-row-${nir.id}`} className="border-border">
                          <TableCell className="font-mono text-foreground">{nir.numar_nir}</TableCell>
                          <TableCell className="text-muted-foreground">{formatDate(nir.created_at)}</TableCell>
                          <TableCell className="text-foreground">{nir.furnizor_nume}</TableCell>
                          <TableCell className="font-mono text-muted-foreground">{nir.numar_factura}</TableCell>
                          <TableCell className="text-right text-foreground">{nir.items.length}</TableCell>
                          <TableCell className="text-right font-mono font-bold text-primary">
                            {formatCurrency(nir.total)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* NIR Dialog */}
      <Dialog open={showNirDialog} onOpenChange={setShowNirDialog}>
        <DialogContent className="bg-card border-border max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="nir-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground">
              Notă de Intrare Recepție (NIR)
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Supplier & Invoice */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">Furnizor *</Label>
                <Select 
                  value={nirForm.furnizor_id || undefined} 
                  onValueChange={(v) => setNirForm({...nirForm, furnizor_id: v})}
                >
                  <SelectTrigger data-testid="nir-furnizor" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue placeholder="Selectați furnizorul" />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    {suppliers.filter(sup => sup && sup.id).map(sup => (
                      <SelectItem key={sup.id} value={sup.id}>{sup.nume}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-muted-foreground">Număr Factură *</Label>
                <Input
                  data-testid="nir-factura"
                  value={nirForm.numar_factura}
                  onChange={(e) => setNirForm({...nirForm, numar_factura: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                  placeholder="Ex: FV-001234"
                />
              </div>
            </div>

            {/* Add Item */}
            <div className="p-4 bg-secondary/30 rounded-sm space-y-4">
              <h4 className="font-heading text-sm uppercase text-muted-foreground">Adaugă Produs</h4>
              <div className="grid grid-cols-4 gap-4">
                <div className="col-span-2">
                  <Select 
                    value={nirItem.product_id || undefined} 
                    onValueChange={(v) => {
                      const product = products.find(p => p.id === v);
                      setNirItem({
                        ...nirItem, 
                        product_id: v,
                        pret_achizitie: product ? product.pret_achizitie.toString() : ''
                      });
                    }}
                  >
                    <SelectTrigger data-testid="nir-item-product" className="h-12 bg-background border-border text-foreground">
                      <SelectValue placeholder="Selectați produsul" />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border max-h-60">
                      {products.filter(p => p && p.id).map(p => (
                        <SelectItem key={p.id} value={p.id}>{p.nume}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Input
                    data-testid="nir-item-qty"
                    type="number"
                    step="0.01"
                    value={nirItem.cantitate}
                    onChange={(e) => setNirItem({...nirItem, cantitate: e.target.value})}
                    className="h-12 bg-background border-border text-foreground font-mono"
                    placeholder="Cantitate"
                  />
                </div>
                <div>
                  <Input
                    data-testid="nir-item-price"
                    type="number"
                    step="0.01"
                    value={nirItem.pret_achizitie}
                    onChange={(e) => setNirItem({...nirItem, pret_achizitie: e.target.value})}
                    className="h-12 bg-background border-border text-foreground font-mono"
                    placeholder="Preț"
                  />
                </div>
              </div>
              <Button
                type="button"
                data-testid="nir-add-item"
                onClick={addNirItem}
                variant="outline"
                className="h-10 border-border text-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                Adaugă în NIR
              </Button>
            </div>

            {/* Items List */}
            {nirForm.items.length > 0 && (
              <div>
                <h4 className="font-heading text-sm uppercase text-muted-foreground mb-2">Produse în NIR</h4>
                <Table>
                  <TableHeader>
                    <TableRow className="border-border">
                      <TableHead className="text-muted-foreground">Produs</TableHead>
                      <TableHead className="text-muted-foreground text-right">Cantitate</TableHead>
                      <TableHead className="text-muted-foreground text-right">Preț</TableHead>
                      <TableHead className="text-muted-foreground text-right">Total</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {nirForm.items.map((item, idx) => (
                      <TableRow key={idx} className="border-border">
                        <TableCell className="text-foreground">{item.nume}</TableCell>
                        <TableCell className="text-right font-mono text-foreground">
                          {formatNumber(item.cantitate)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-foreground">
                          {formatCurrency(item.pret_achizitie)}
                        </TableCell>
                        <TableCell className="text-right font-mono font-bold text-primary">
                          {formatCurrency(item.cantitate * item.pret_achizitie)}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeNirItem(idx)}
                            className="text-destructive hover:bg-destructive/10"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="flex justify-end mt-4 pt-4 border-t border-border">
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Total NIR</p>
                    <p className="font-mono text-2xl font-bold text-primary" data-testid="nir-total">
                      {formatCurrency(calculateNirTotal())}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowNirDialog(false)}
              className="h-12 px-6 border-border text-foreground"
            >
              Anulează
            </Button>
            <Button
              data-testid="save-nir"
              onClick={submitNir}
              disabled={nirForm.items.length === 0}
              className="h-12 px-6 bg-primary text-primary-foreground"
            >
              Salvează NIR
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
