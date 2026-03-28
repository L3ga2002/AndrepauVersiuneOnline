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
import { Package, AlertTriangle, TrendingDown, Archive, Plus, Trash2, FileText, Upload, FileUp, Check, X, Loader2, ScanLine } from 'lucide-react';
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

  // PDF Import state
  const [showPdfDialog, setShowPdfDialog] = useState(false);
  const [pdfParsing, setPdfParsing] = useState(false);
  const [pdfResult, setPdfResult] = useState(null);
  const [pdfItems, setPdfItems] = useState([]);
  const [pdfInvoiceNumber, setPdfInvoiceNumber] = useState('');
  const [pdfSupplierId, setPdfSupplierId] = useState('');
  const [savingPdfNir, setSavingPdfNir] = useState(false);

  // Post-NIR Barcode state
  const [showBarcodeDialog, setShowBarcodeDialog] = useState(false);
  const [barcodeItems, setBarcodeItems] = useState([]);
  const [savingBarcodes, setSavingBarcodes] = useState(false);

  // Test invoices
  const [testInvoices, setTestInvoices] = useState([]);
  const [showTestInvoices, setShowTestInvoices] = useState(false);

  const fetchTestInvoices = async () => {
    try {
      const res = await fetch(`${API_URL}/nir/test-invoices`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTestInvoices(data.invoices || []);
      }
    } catch {}
  };

  const downloadTestInvoice = async (filename) => {
    try {
      const res = await fetch(`${API_URL}/nir/test-invoices/${filename}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        toast.success(`Descărcat: ${filename}`);
      }
    } catch { toast.error('Eroare la descărcare'); }
  };

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
        // Open barcode dialog with the items from this NIR
        const nirItems = nirForm.items.map(item => ({
          product_id: item.product_id,
          nume: item.nume,
          cod_bare: ''
        }));
        setBarcodeItems(nirItems);
        setShowBarcodeDialog(true);
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

  // PDF Import functions
  const handlePdfUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    setPdfParsing(true);
    setPdfResult(null);
    setPdfItems([]);
    setShowPdfDialog(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/nir/parse-pdf`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setPdfResult(data);
        setPdfInvoiceNumber(data.invoice_number || '');
        setPdfItems(data.items.map((item, idx) => ({
          ...item,
          enabled: true,
          idx
        })));

        // Try to auto-match supplier
        if (data.supplier_name) {
          const matched = suppliers.find(s => 
            s.nume.toLowerCase().includes(data.supplier_name.toLowerCase()) ||
            data.supplier_name.toLowerCase().includes(s.nume.toLowerCase())
          );
          if (matched) setPdfSupplierId(matched.id);
        }

        if (data.items.length === 0) {
          toast.warning('Nu am putut extrage produse din PDF. Verificați manual.');
        } else {
          toast.success(`${data.items.length} produse extrase din PDF`);
        }
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Eroare la parsare PDF');
        setShowPdfDialog(false);
      }
    } catch (error) {
      toast.error('Eroare la încărcare PDF');
      setShowPdfDialog(false);
    } finally {
      setPdfParsing(false);
    }
  };

  const togglePdfItem = (idx) => {
    setPdfItems(prev => prev.map(item => 
      item.idx === idx ? { ...item, enabled: !item.enabled } : item
    ));
  };

  const updatePdfItem = (idx, field, value) => {
    setPdfItems(prev => prev.map(item => {
      if (item.idx !== idx) return item;
      const updated = { ...item, [field]: value };
      if (field === 'cantitate' || field === 'pret_unitar') {
        updated.valoare = parseFloat(updated.cantitate || 0) * parseFloat(updated.pret_unitar || 0);
      }
      return updated;
    }));
  };

  const submitPdfNir = async () => {
    const enabledItems = pdfItems.filter(i => i.enabled);
    if (!pdfSupplierId) {
      toast.error('Selectați furnizorul');
      return;
    }
    if (!pdfInvoiceNumber) {
      toast.error('Introduceți numărul facturii');
      return;
    }
    if (enabledItems.length === 0) {
      toast.error('Selectați cel puțin un produs');
      return;
    }

    setSavingPdfNir(true);
    try {
      const nirPayload = {
        furnizor_id: pdfSupplierId,
        numar_factura: pdfInvoiceNumber,
        items: enabledItems.map(item => ({
          product_id: item.product_id || null,
          denumire: item.product_nume || item.denumire_pdf,
          cantitate: parseFloat(item.cantitate),
          pret_achizitie: parseFloat(item.pret_unitar),
          um: item.um || 'buc'
        }))
      };

      const response = await fetch(`${API_URL}/nir/from-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(nirPayload)
      });

      if (response.ok) {
        const result = await response.json();
        const newCount = result.products_created_count || 0;
        const updCount = result.products_updated_count || 0;
        toast.success(`NIR creat! ${newCount} produse noi create, ${updCount} actualizate`);
        setShowPdfDialog(false);
        // Open barcode dialog with ALL items
        const nirItems = (result.created_products || []).map(p => ({
          product_id: p.product_id,
          nume: p.nume,
          cod_bare: p.cod_bare || ''
        }));
        if (nirItems.length > 0) {
          setBarcodeItems(nirItems);
          setShowBarcodeDialog(true);
        }
        setPdfResult(null);
        setPdfItems([]);
        fetchNirs();
        fetchDashboard();
        fetchAlerts();
        fetchProducts();
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Eroare la creare NIR');
      }
    } catch (error) {
      toast.error('Eroare la creare NIR');
    } finally {
      setSavingPdfNir(false);
    }
  };

  const pdfFileRef = React.useRef(null);

  // Barcode update functions
  const updateBarcodeItem = (idx, value) => {
    setBarcodeItems(prev => prev.map((item, i) => 
      i === idx ? { ...item, cod_bare: value } : item
    ));
  };

  const saveBarcodes = async () => {
    const toUpdate = barcodeItems.filter(i => i.cod_bare.trim());
    if (toUpdate.length === 0) {
      setShowBarcodeDialog(false);
      return;
    }

    setSavingBarcodes(true);
    try {
      const response = await fetch(`${API_URL}/products/bulk-barcode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          updates: toUpdate.map(i => ({
            product_id: i.product_id,
            cod_bare: i.cod_bare.trim()
          }))
        })
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(`${result.updated} coduri de bare actualizate`);
        fetchProducts();
      } else {
        toast.error('Eroare la salvare coduri de bare');
      }
    } catch (error) {
      toast.error('Eroare la salvare coduri de bare');
    } finally {
      setSavingBarcodes(false);
      setShowBarcodeDialog(false);
    }
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
          <div className="flex gap-3 items-center">
            <input
              ref={pdfFileRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handlePdfUpload}
              data-testid="pdf-file-input"
            />
            <div className="relative">
              <Button
                data-testid="test-invoices-btn"
                onClick={() => { fetchTestInvoices(); setShowTestInvoices(!showTestInvoices); }}
                variant="ghost"
                className="h-12 px-4 text-muted-foreground hover:text-foreground"
              >
                <FileText className="w-5 h-5 mr-2" />
                Facturi Test
              </Button>
              {showTestInvoices && testInvoices.length > 0 && (
                <div className="absolute right-0 top-14 z-50 bg-card border border-border rounded-sm shadow-lg p-2 min-w-[280px]">
                  <p className="text-xs text-muted-foreground px-2 pb-2">Descarcă o factură de test:</p>
                  {testInvoices.map(f => (
                    <button
                      key={f}
                      onClick={() => { downloadTestInvoice(f); setShowTestInvoices(false); }}
                      className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-secondary/50 rounded-sm transition-colors"
                    >
                      {f.replace('.pdf', '').replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <Button
              data-testid="import-pdf-btn"
              onClick={() => pdfFileRef.current?.click()}
              variant="outline"
              className="h-12 px-6 border-border text-foreground"
            >
              <FileUp className="w-5 h-5 mr-2" />
              Import din PDF
            </Button>
            <Button
              data-testid="create-nir-btn"
              onClick={openNirDialog}
              className="h-12 px-6 bg-primary text-primary-foreground"
            >
              <Plus className="w-5 h-5 mr-2" />
              Intrare Marfă (NIR)
            </Button>
          </div>
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
              <CardTitle className="font-heading text-xl uppercase text-foreground flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
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
                  <p>Toate produsele sunt in stoc</p>
                </div>
              ) : (
                <>
                  {/* Summary bar */}
                  <div className="flex gap-4 mb-4 p-3 bg-secondary rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="inline-block w-3 h-3 rounded-full bg-red-500"></span>
                      <span className="text-sm text-foreground font-medium">
                        {alerts.filter(a => a.severity === 'critical' || a.stoc <= 0).length} fara stoc
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="inline-block w-3 h-3 rounded-full bg-yellow-500"></span>
                      <span className="text-sm text-foreground font-medium">
                        {alerts.filter(a => a.severity === 'warning' || (a.stoc > 0 && a.stoc <= a.stoc_minim)).length} stoc scazut
                      </span>
                    </div>
                  </div>
                  <ScrollArea className="h-[400px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-border">
                          <TableHead className="text-muted-foreground w-8">!</TableHead>
                          <TableHead className="text-muted-foreground">Produs</TableHead>
                          <TableHead className="text-muted-foreground">Categorie</TableHead>
                          <TableHead className="text-muted-foreground text-right">Stoc Actual</TableHead>
                          <TableHead className="text-muted-foreground text-right">Stoc Minim</TableHead>
                          <TableHead className="text-muted-foreground text-right">Deficit</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {alerts.map(product => {
                          const isCritical = product.stoc <= 0;
                          const deficit = (product.stoc_minim || 0) - product.stoc;
                          return (
                            <TableRow key={product.id} className={`border-border ${isCritical ? 'bg-red-500/5' : ''}`} data-testid={`stock-alert-${product.id}`}>
                              <TableCell>
                                {isCritical ? (
                                  <AlertTriangle className="w-4 h-4 text-red-500" />
                                ) : (
                                  <TrendingDown className="w-4 h-4 text-yellow-500" />
                                )}
                              </TableCell>
                              <TableCell className="font-medium text-foreground">{product.nume}</TableCell>
                              <TableCell className="text-muted-foreground">{product.categorie}</TableCell>
                              <TableCell className={`text-right font-mono font-bold ${isCritical ? 'text-red-500' : 'text-yellow-500'}`}>
                                {formatNumber(product.stoc, 1)} {product.unitate}
                              </TableCell>
                              <TableCell className="text-right font-mono text-muted-foreground">
                                {formatNumber(product.stoc_minim, 1)} {product.unitate}
                              </TableCell>
                              <TableCell className="text-right font-mono font-bold text-red-400">
                                -{formatNumber(deficit, 1)}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </>
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
                  value={nirForm.furnizor_id || "_none_"} 
                  onValueChange={(v) => setNirForm({...nirForm, furnizor_id: v === "_none_" ? "" : v})}
                >
                  <SelectTrigger data-testid="nir-furnizor" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue placeholder="Selectați furnizorul" />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    <SelectItem value="_none_">Selectați furnizorul</SelectItem>
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
                    value={nirItem.product_id || "_none_"} 
                    onValueChange={(v) => {
                      if (v === "_none_") {
                        setNirItem({...nirItem, product_id: '', pret_achizitie: ''});
                        return;
                      }
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
                      <SelectItem value="_none_">Selectați produsul</SelectItem>
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

      {/* PDF Import Dialog */}
      <Dialog open={showPdfDialog} onOpenChange={(open) => { if (!pdfParsing && !savingPdfNir) setShowPdfDialog(open); }}>
        <DialogContent className="bg-card border-border max-w-6xl max-h-[90vh] overflow-y-auto" data-testid="pdf-import-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground flex items-center gap-3">
              <FileUp className="w-6 h-6 text-primary" />
              Import NIR din PDF
            </DialogTitle>
          </DialogHeader>

          {pdfParsing ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
              <p className="text-muted-foreground">Se parsează PDF-ul...</p>
            </div>
          ) : pdfResult ? (
            <div className="space-y-6">
              {/* Invoice info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">Furnizor *</Label>
                  <Select 
                    value={pdfSupplierId || "_none_"} 
                    onValueChange={(v) => setPdfSupplierId(v === "_none_" ? "" : v)}
                  >
                    <SelectTrigger data-testid="pdf-furnizor" className="h-12 mt-1 bg-background border-border text-foreground">
                      <SelectValue placeholder="Selectați furnizorul" />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border">
                      <SelectItem value="_none_">Selectați furnizorul</SelectItem>
                      {suppliers.filter(sup => sup && sup.id).map(sup => (
                        <SelectItem key={sup.id} value={sup.id}>{sup.nume}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {pdfResult.supplier_name && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Detectat din PDF: <span className="text-primary">{pdfResult.supplier_name}</span>
                    </p>
                  )}
                </div>
                <div>
                  <Label className="text-muted-foreground">Număr Factură *</Label>
                  <Input
                    data-testid="pdf-factura"
                    value={pdfInvoiceNumber}
                    onChange={(e) => setPdfInvoiceNumber(e.target.value)}
                    className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                    placeholder="Ex: FV-001234"
                  />
                </div>
              </div>

              {/* Items table */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-heading text-sm uppercase text-muted-foreground">
                    Produse Extrase ({pdfItems.filter(i => i.enabled).length} selectate din {pdfItems.length})
                  </h4>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setPdfItems(prev => prev.map(i => ({ ...i, enabled: true })))}
                      className="text-xs text-muted-foreground"
                    >
                      Selectează toate
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setPdfItems(prev => prev.map(i => ({ ...i, enabled: false })))}
                      className="text-xs text-muted-foreground"
                    >
                      Deselectează toate
                    </Button>
                  </div>
                </div>

                {pdfItems.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-secondary/20 rounded-sm">
                    <FileText className="w-12 h-12 mb-3 opacity-50" />
                    <p className="font-medium">Nu s-au găsit produse în PDF</p>
                    <p className="text-sm mt-1">Încercați să creați NIR-ul manual</p>
                  </div>
                ) : (
                  <ScrollArea className="h-[350px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-border">
                          <TableHead className="w-10"></TableHead>
                          <TableHead className="text-muted-foreground w-[35%]">Denumire din PDF</TableHead>
                          <TableHead className="text-muted-foreground w-[25%]">Produs Potrivit</TableHead>
                          <TableHead className="text-muted-foreground text-center w-[12%]">Cantitate</TableHead>
                          <TableHead className="text-muted-foreground text-center w-[13%]">Preț Unit.</TableHead>
                          <TableHead className="text-muted-foreground text-right w-[15%]">Valoare</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pdfItems.map(item => (
                          <TableRow 
                            key={item.idx} 
                            className={`border-border ${!item.enabled ? 'opacity-40' : ''}`}
                            data-testid={`pdf-item-${item.idx}`}
                          >
                            <TableCell>
                              <button
                                onClick={() => togglePdfItem(item.idx)}
                                className={`w-6 h-6 rounded-sm border flex items-center justify-center transition-colors ${
                                  item.enabled 
                                    ? 'bg-primary border-primary text-primary-foreground' 
                                    : 'border-border text-transparent'
                                }`}
                                data-testid={`pdf-toggle-${item.idx}`}
                              >
                                <Check className="w-4 h-4" />
                              </button>
                            </TableCell>
                            <TableCell>
                              <p className="text-foreground text-sm font-medium">{item.denumire_pdf}</p>
                              <p className="text-xs text-muted-foreground mt-0.5">{item.um}</p>
                            </TableCell>
                            <TableCell>
                              <Select
                                value={item.product_id || "_new_"}
                                onValueChange={(v) => {
                                  if (v === "_new_") {
                                    setPdfItems(prev => prev.map(i => 
                                      i.idx === item.idx 
                                        ? { ...i, product_id: null, product_nume: null }
                                        : i
                                    ));
                                  } else {
                                    const prod = products.find(p => p.id === v);
                                    setPdfItems(prev => prev.map(i => 
                                      i.idx === item.idx 
                                        ? { ...i, product_id: v, product_nume: prod?.nume || null }
                                        : i
                                    ));
                                  }
                                }}
                              >
                                <SelectTrigger className={`h-9 text-sm bg-background border-border ${
                                  item.product_id ? 'text-foreground' : 'text-green-500'
                                }`}>
                                  <SelectValue placeholder="Produs Nou" />
                                </SelectTrigger>
                                <SelectContent className="bg-card border-border max-h-60">
                                  <SelectItem value="_new_">+ PRODUS NOU</SelectItem>
                                  {products.filter(p => p && p.id).map(p => (
                                    <SelectItem key={p.id} value={p.id}>{p.nume}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              {item.product_id && item.match_confidence >= 80 && (
                                <p className="text-xs text-blue-400 mt-0.5">Auto-potrivit</p>
                              )}
                              {!item.product_id && (
                                <p className="text-xs text-green-500 mt-0.5">Se creează automat</p>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <Input
                                type="number"
                                step="0.01"
                                value={item.cantitate}
                                onChange={(e) => updatePdfItem(item.idx, 'cantitate', e.target.value)}
                                className="h-9 w-24 text-right font-mono bg-background border-border text-foreground text-sm"
                              />
                            </TableCell>
                            <TableCell className="text-right">
                              <Input
                                type="number"
                                step="0.01"
                                value={item.pret_unitar}
                                onChange={(e) => updatePdfItem(item.idx, 'pret_unitar', e.target.value)}
                                className="h-9 w-28 text-right font-mono bg-background border-border text-foreground text-sm"
                              />
                            </TableCell>
                            <TableCell className="text-right font-mono text-sm text-primary font-bold">
                              {formatCurrency(parseFloat(item.cantitate || 0) * parseFloat(item.pret_unitar || 0))}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                )}
              </div>

              {/* Total */}
              {pdfItems.filter(i => i.enabled).length > 0 && (
                <div className="flex justify-between items-center pt-4 border-t border-border">
                  <div className="text-sm text-muted-foreground space-y-1">
                    {pdfItems.filter(i => i.enabled && !i.product_id).length > 0 && (
                      <span className="text-green-500 block">
                        {pdfItems.filter(i => i.enabled && !i.product_id).length} produse noi (vor fi create automat)
                      </span>
                    )}
                    {pdfItems.filter(i => i.enabled && i.product_id).length > 0 && (
                      <span className="text-blue-400 block">
                        {pdfItems.filter(i => i.enabled && i.product_id).length} produse existente (stoc actualizat)
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Total NIR</p>
                    <p className="font-mono text-2xl font-bold text-primary" data-testid="pdf-nir-total">
                      {formatCurrency(
                        pdfItems.filter(i => i.enabled)
                          .reduce((sum, i) => sum + (parseFloat(i.cantitate || 0) * parseFloat(i.pret_unitar || 0)), 0)
                      )}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : null}

          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowPdfDialog(false)}
              disabled={pdfParsing || savingPdfNir}
              className="h-12 px-6 border-border text-foreground"
            >
              Anulează
            </Button>
            {pdfResult && pdfItems.length > 0 && (
              <Button
                data-testid="save-pdf-nir"
                onClick={submitPdfNir}
                disabled={savingPdfNir || pdfItems.filter(i => i.enabled).length === 0}
                className="h-12 px-6 bg-primary text-primary-foreground"
              >
                {savingPdfNir ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Se salvează...</>
                ) : (
                  <>Salvează NIR ({pdfItems.filter(i => i.enabled).length} produse)</>
                )}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Post-NIR Barcode Dialog */}
      <Dialog open={showBarcodeDialog} onOpenChange={(open) => { if (!savingBarcodes) setShowBarcodeDialog(open); }}>
        <DialogContent className="bg-card border-border max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="barcode-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground flex items-center gap-3">
              <ScanLine className="w-6 h-6 text-primary" />
              Coduri de Bare - Produse din NIR
            </DialogTitle>
          </DialogHeader>

          <p className="text-sm text-muted-foreground">
            Scanați sau introduceți codurile de bare pentru produsele din acest NIR. Puteți sări peste produsele care au deja cod de bare.
          </p>

          <div className="space-y-3 mt-4">
            {barcodeItems.map((item, idx) => {
              const existingProduct = products.find(p => p.id === item.product_id);
              const hasExistingBarcode = existingProduct?.cod_bare;
              return (
                <div 
                  key={idx} 
                  className="flex items-center gap-3 p-3 bg-secondary/20 rounded-sm"
                  data-testid={`barcode-item-${idx}`}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground font-medium text-sm truncate">{item.nume}</p>
                    {hasExistingBarcode && (
                      <p className="text-xs text-muted-foreground font-mono">Actual: {existingProduct.cod_bare}</p>
                    )}
                  </div>
                  <div className="w-52">
                    <Input
                      data-testid={`barcode-input-${idx}`}
                      value={item.cod_bare}
                      onChange={(e) => updateBarcodeItem(idx, e.target.value)}
                      placeholder={hasExistingBarcode ? "Păstrează actual" : "Scanați cod bare"}
                      className="h-10 bg-background border-border text-foreground font-mono text-sm"
                      autoFocus={idx === 0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          // Focus next input
                          const nextInput = document.querySelector(`[data-testid="barcode-input-${idx + 1}"]`);
                          if (nextInput) nextInput.focus();
                          else saveBarcodes();
                        }
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowBarcodeDialog(false)}
              disabled={savingBarcodes}
              className="h-12 px-6 border-border text-foreground"
              data-testid="skip-barcodes-btn"
            >
              Sari peste
            </Button>
            <Button
              data-testid="save-barcodes-btn"
              onClick={saveBarcodes}
              disabled={savingBarcodes || barcodeItems.every(i => !i.cod_bare.trim())}
              className="h-12 px-6 bg-primary text-primary-foreground"
            >
              {savingBarcodes ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Se salvează...</>
              ) : (
                <>Salvează Coduri de Bare ({barcodeItems.filter(i => i.cod_bare.trim()).length})</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
