import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ScrollArea } from '../components/ui/scroll-area';
import { formatCurrency, formatNumber, getStockStatus } from '../lib/utils';
import { Plus, Search, Edit, Trash2, Package, AlertTriangle, Barcode, ScanLine, Upload, Download, FileText, Check, X, Loader2, Percent } from 'lucide-react';
import { toast } from 'sonner';

const UNITS = [
  { value: 'buc', label: 'Bucăți' },
  { value: 'sac', label: 'Saci' },
  { value: 'kg', label: 'Kilograme' },
  { value: 'metru', label: 'Metri' },
  { value: 'litru', label: 'Litri' },
  { value: 'rola', label: 'Role' }
];

const CATEGORIES = [
  'Materiale Construcții',
  'Scule Electrice',
  'Scule Manuale',
  'Feronerie',
  'Instalații Sanitare',
  'Electrice',
  'Vopsele',
  'Consumabile'
];

const emptyProduct = {
  nume: '',
  categorie: '',
  furnizor_id: '',
  cod_bare: '',
  pret_achizitie: '',
  pret_vanzare: '',
  tva: '19',
  unitate: 'buc',
  stoc: '',
  stoc_minim: '5',
  descriere: ''
};

export default function ProductsPage() {
  const { token, API_URL, isAdmin } = useAuth();
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [showLowStock, setShowLowStock] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const ITEMS_PER_PAGE = 50;
  
  const [showDialog, setShowDialog] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState(emptyProduct);
  const [saving, setSaving] = useState(false);
  
  // Barcode scanning state
  const [showNotFoundDialog, setShowNotFoundDialog] = useState(false);
  const [scannedBarcode, setScannedBarcode] = useState('');
  const [lastScannedProduct, setLastScannedProduct] = useState(null);
  const searchRef = useRef(null);

  // CSV Import state
  const [showCsvDialog, setShowCsvDialog] = useState(false);
  const [csvParsing, setCsvParsing] = useState(false);
  const [csvResult, setCsvResult] = useState(null);
  const [csvItems, setCsvItems] = useState([]);
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvPage, setCsvPage] = useState(1);
  const CSV_PAGE_SIZE = 100;
  const csvFileRef = useRef(null);

  // Delete all & TVA bulk
  const [showDeleteAll, setShowDeleteAll] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deletingAll, setDeletingAll] = useState(false);
  const [showTvaBulk, setShowTvaBulk] = useState(false);
  const [newTva, setNewTva] = useState('');
  const [updatingTva, setUpdatingTva] = useState(false);

  const fetchProducts = useCallback(async () => {
    try {
      let url = `${API_URL}/products?page=${currentPage}&limit=${ITEMS_PER_PAGE}&`;
      if (searchQuery) url += `search=${encodeURIComponent(searchQuery)}&`;
      if (filterCategory) url += `categorie=${encodeURIComponent(filterCategory)}&`;
      if (showLowStock) url += `low_stock=true&`;
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setProducts(data.products || []);
      setTotalPages(data.pages || 1);
      setTotalProducts(data.total || 0);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  }, [API_URL, token, searchQuery, filterCategory, showLowStock, currentPage]);

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

  const fetchCategories = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(await response.json());
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  }, [API_URL, token]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchProducts(), fetchSuppliers(), fetchCategories()]);
      setLoading(false);
    };
    init();
  }, [fetchProducts, fetchSuppliers, fetchCategories]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterCategory, showLowStock]);

  useEffect(() => {
    fetchProducts();
  }, [currentPage, fetchProducts]);

  // Barcode scanner handler - detectează scanarea rapidă
  useEffect(() => {
    let barcodeBuffer = '';
    let lastKeyTime = 0;
    let barcodeTimeout;

    const handleKeyPress = async (e) => {
      const currentTime = Date.now();
      const timeDiff = currentTime - lastKeyTime;
      lastKeyTime = currentTime;

      // Skip if in an input field that's not the search field
      const activeElement = document.activeElement;
      const isSearchField = activeElement === searchRef.current;
      const isOtherInput = activeElement.tagName === 'INPUT' && !isSearchField;
      
      if (isOtherInput) {
        return;
      }

      // Clear buffer after 150ms of no input (barcode scanners are fast)
      clearTimeout(barcodeTimeout);
      barcodeTimeout = setTimeout(() => {
        barcodeBuffer = '';
      }, 150);

      // If typing is fast (< 50ms between keys) or it's a digit, add to buffer
      const isFastTyping = timeDiff < 50;
      const isDigit = /^\d$/.test(e.key);
      
      if (e.key === 'Enter' && barcodeBuffer.length > 5) {
        e.preventDefault();
        const barcode = barcodeBuffer;
        barcodeBuffer = '';
        
        // Clear search field if it contains the barcode
        if (isSearchField && searchRef.current) {
          searchRef.current.value = '';
          setSearchQuery('');
        }
        
        // Lookup product by barcode
        try {
          const response = await fetch(`${API_URL}/products/barcode/${barcode}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          if (response.ok) {
            const product = await response.json();
            setLastScannedProduct(product);
            setSearchQuery(barcode);
            toast.success(`Produs găsit: ${product.nume}`, {
              description: `Stoc: ${product.stoc} ${product.unitate} | Preț: ${product.pret_vanzare} RON`
            });
          } else {
            // Product not found - ask to add
            setScannedBarcode(barcode);
            setShowNotFoundDialog(true);
          }
        } catch (error) {
          console.error('Barcode lookup error:', error);
          setScannedBarcode(barcode);
          setShowNotFoundDialog(true);
        }
      } else if (e.key.length === 1 && (isFastTyping || isDigit || barcodeBuffer.length > 0)) {
        barcodeBuffer += e.key;
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [API_URL, token]);

  // Function to open create dialog with scanned barcode
  const openCreateDialogWithBarcode = (barcode) => {
    setEditingProduct(null);
    setFormData({
      ...emptyProduct,
      cod_bare: barcode
    });
    setShowNotFoundDialog(false);
    setShowDialog(true);
    toast.info('Completați datele produsului nou');
  };

  const openCreateDialog = () => {
    setEditingProduct(null);
    setFormData(emptyProduct);
    setShowDialog(true);
  };

  const openEditDialog = (product) => {
    setEditingProduct(product);
    setFormData({
      nume: product.nume,
      categorie: product.categorie,
      furnizor_id: product.furnizor_id || '',
      cod_bare: product.cod_bare || '',
      pret_achizitie: product.pret_achizitie.toString(),
      pret_vanzare: product.pret_vanzare.toString(),
      tva: product.tva.toString(),
      unitate: product.unitate,
      stoc: product.stoc.toString(),
      stoc_minim: product.stoc_minim.toString(),
      descriere: product.descriere || ''
    });
    setShowDialog(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      ...formData,
      pret_achizitie: formData.pret_achizitie ? parseFloat(formData.pret_achizitie) : 0,
      pret_vanzare: parseFloat(formData.pret_vanzare),
      tva: parseFloat(formData.tva),
      stoc: parseFloat(formData.stoc),
      stoc_minim: parseFloat(formData.stoc_minim),
      furnizor_id: formData.furnizor_id || null
    };

    try {
      const url = editingProduct 
        ? `${API_URL}/products/${editingProduct.id}`
        : `${API_URL}/products`;
      
      const response = await fetch(url, {
        method: editingProduct ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        toast.success(editingProduct ? 'Produs actualizat' : 'Produs creat');
        setShowDialog(false);
        fetchProducts();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Eroare la salvare');
      }
    } catch (error) {
      toast.error('Eroare la salvare');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (product) => {
    if (!window.confirm(`Sigur doriți să ștergeți "${product.nume}"?`)) return;

    try {
      const response = await fetch(`${API_URL}/products/${product.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Produs șters');
        fetchProducts();
      } else {
        toast.error('Eroare la ștergere');
      }
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const getSupplierName = (supplierId) => {
    const supplier = suppliers.find(s => s.id === supplierId);
    return supplier ? supplier.nume : '-';
  };

  // CSV Import functions
  const handleCsvUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    const ext = file.name.toLowerCase();
    if (!ext.endsWith('.csv') && !ext.endsWith('.xlsx') && !ext.endsWith('.xls')) {
      toast.error('Fișierul trebuie să fie .xlsx sau .csv');
      return;
    }

    setCsvParsing(true);
    setCsvResult(null);
    setCsvItems([]);
    setCsvPage(1);
    setShowCsvDialog(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/products/import-csv`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setCsvResult(data);
        setCsvItems(data.items.map((item, idx) => ({ ...item, enabled: true, idx })));

        if (data.items.length === 0) {
          toast.warning('Nu s-au găsit produse în CSV');
        } else {
          toast.success(`${data.items.length} produse găsite (${data.total_create} noi, ${data.total_update} actualizări)`);
        }
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Eroare la parsare CSV');
        setShowCsvDialog(false);
      }
    } catch (error) {
      toast.error('Eroare la încărcare CSV');
      setShowCsvDialog(false);
    } finally {
      setCsvParsing(false);
    }
  };

  const toggleCsvItem = (idx) => {
    setCsvItems(prev => prev.map(item =>
      item.idx === idx ? { ...item, enabled: !item.enabled } : item
    ));
  };

  const confirmCsvImport = async () => {
    const enabledItems = csvItems.filter(i => i.enabled);
    if (enabledItems.length === 0) {
      toast.error('Selectați cel puțin un produs');
      return;
    }

    setCsvImporting(true);
    try {
      // Process in batches of 500 to avoid timeout
      const BATCH_SIZE = 500;
      let totalCreated = 0;
      let totalUpdated = 0;
      let totalErrors = [];
      const totalBatches = Math.ceil(enabledItems.length / BATCH_SIZE);

      for (let i = 0; i < enabledItems.length; i += BATCH_SIZE) {
        const batch = enabledItems.slice(i, i + BATCH_SIZE);
        const batchNum = Math.floor(i / BATCH_SIZE) + 1;
        
        if (totalBatches > 1) {
          toast.info(`Se importă lot ${batchNum} din ${totalBatches}...`);
        }

        const response = await fetch(`${API_URL}/products/import-csv/confirm`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ items: batch })
        });

        if (response.ok) {
          const result = await response.json();
          totalCreated += result.created;
          totalUpdated += result.updated;
          if (result.errors) totalErrors.push(...result.errors);
        } else {
          const err = await response.json();
          toast.error(err.detail || `Eroare la lotul ${batchNum}`);
          break;
        }
      }

      toast.success(`Import finalizat: ${totalCreated} create, ${totalUpdated} actualizate`);
      if (totalErrors.length > 0) {
        toast.warning(`${totalErrors.length} erori la import`);
      }
      setShowCsvDialog(false);
      setCsvResult(null);
      setCsvItems([]);
      fetchProducts();
    } catch (error) {
      toast.error('Eroare la import');
    } finally {
      setCsvImporting(false);
    }
  };

  const downloadCsvTemplate = async () => {
    try {
      const response = await fetch(`${API_URL}/products/csv-template`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'template_import_produse.xlsx';
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      toast.error('Eroare la descărcare template');
    }
  };

  const handleDeleteAll = async () => {
    if (deleteConfirmText !== 'STERGE TOATE') return;
    setDeletingAll(true);
    try {
      const response = await fetch(`${API_URL}/products-all/delete`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        setShowDeleteAll(false);
        setDeleteConfirmText('');
        fetchProducts();
      } else {
        toast.error('Eroare la ștergere');
      }
    } catch {
      toast.error('Eroare la ștergere');
    } finally {
      setDeletingAll(false);
    }
  };

  const handleBulkTva = async () => {
    const tvaVal = parseFloat(newTva);
    if (isNaN(tvaVal) || tvaVal < 0 || tvaVal > 100) {
      toast.error('Introduceți o cotă TVA validă (0-100)');
      return;
    }
    setUpdatingTva(true);
    try {
      const response = await fetch(`${API_URL}/products-all/bulk-tva`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ tva: tvaVal })
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        setShowTvaBulk(false);
        setNewTva('');
        fetchProducts();
      } else {
        toast.error('Eroare la actualizare TVA');
      }
    } catch {
      toast.error('Eroare la actualizare TVA');
    } finally {
      setUpdatingTva(false);
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="products-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl uppercase tracking-tight text-foreground">
            Gestiune Produse
          </h1>
          <p className="text-muted-foreground mt-1">
            {totalProducts} produse în baza de date (pagina {currentPage} din {totalPages})
          </p>
        </div>
        
        {isAdmin && (
          <div className="flex gap-3 flex-wrap">
            <input
              ref={csvFileRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={handleCsvUpload}
              data-testid="csv-file-input"
            />
            <Button
              data-testid="download-csv-template-btn"
              onClick={downloadCsvTemplate}
              variant="outline"
              className="h-12 px-4 border-border text-muted-foreground"
            >
              <Download className="w-5 h-5 mr-2" />
              Template Excel
            </Button>
            <Button
              data-testid="import-csv-btn"
              onClick={() => csvFileRef.current?.click()}
              variant="outline"
              className="h-12 px-4 border-border text-foreground"
            >
              <Upload className="w-5 h-5 mr-2" />
              Import Excel/CSV
            </Button>
            <Button
              data-testid="bulk-tva-btn"
              onClick={() => setShowTvaBulk(true)}
              variant="outline"
              className="h-12 px-4 border-border text-foreground"
            >
              <Percent className="w-5 h-5 mr-2" />
              Schimbă TVA
            </Button>
            <Button
              data-testid="delete-all-btn"
              onClick={() => setShowDeleteAll(true)}
              variant="outline"
              className="h-12 px-4 border-red-500/50 text-red-500 hover:bg-red-500/10"
            >
              <Trash2 className="w-5 h-5 mr-2" />
              Șterge Toate
            </Button>
            <Button
              data-testid="add-product-btn"
              onClick={openCreateDialog}
              className="h-12 px-6 bg-primary text-primary-foreground"
            >
              <Plus className="w-5 h-5 mr-2" />
              Adaugă Produs
            </Button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            ref={searchRef}
            data-testid="search-products"
            type="text"
            placeholder="Caută după nume sau scanează codul de bare..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-12 pl-10 pr-12 bg-card border-border text-foreground"
          />
          <Barcode className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        </div>
        
        <Select value={filterCategory || "all"} onValueChange={(v) => setFilterCategory(v === "all" ? "" : v)}>
          <SelectTrigger data-testid="filter-category" className="w-full md:w-64 h-12 bg-card border-border text-foreground">
            <SelectValue placeholder="Toate categoriile" />
          </SelectTrigger>
          <SelectContent className="bg-card border-border">
            <SelectItem value="all">Toate categoriile</SelectItem>
            {[...new Set([...CATEGORIES, ...categories])].filter(cat => cat && cat.trim() !== '').map(cat => (
              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button
          variant={showLowStock ? 'default' : 'outline'}
          data-testid="filter-low-stock"
          onClick={() => setShowLowStock(!showLowStock)}
          className={`h-12 ${showLowStock ? 'bg-destructive text-white' : 'border-border text-foreground'}`}
        >
          <AlertTriangle className="w-5 h-5 mr-2" />
          Stoc Scăzut
        </Button>
      </div>

      {/* Products Table */}
      <div className="bg-card border border-border rounded-sm">
        <ScrollArea className="h-[calc(100vh-320px)]">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="spinner" />
            </div>
          ) : products.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Package className="w-16 h-16 mb-4 opacity-50" />
              <p>Niciun produs găsit</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-muted-foreground">Produs</TableHead>
                  <TableHead className="text-muted-foreground">Categorie</TableHead>
                  <TableHead className="text-muted-foreground">Cod Bare</TableHead>
                  <TableHead className="text-muted-foreground text-right">Preț Achiziție</TableHead>
                  <TableHead className="text-muted-foreground text-right">Preț Vânzare</TableHead>
                  <TableHead className="text-muted-foreground text-right">Stoc</TableHead>
                  <TableHead className="text-muted-foreground">Furnizor</TableHead>
                  {isAdmin && <TableHead className="text-muted-foreground text-right">Acțiuni</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map(product => {
                  const stockStatus = getStockStatus(product.stoc, product.stoc_minim);
                  return (
                    <TableRow 
                      key={product.id} 
                      data-testid={`product-row-${product.id}`}
                      className="border-border hover:bg-secondary/30"
                    >
                      <TableCell>
                        <div>
                          <p className="font-medium text-foreground">{product.nume}</p>
                          <p className="text-xs text-muted-foreground">{product.unitate}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-foreground">{product.categorie}</TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        {product.cod_bare || '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono text-foreground">
                        {formatCurrency(product.pret_achizitie)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-primary font-bold">
                        {formatCurrency(product.pret_vanzare)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={`font-mono ${stockStatus.className}`}>
                          {formatNumber(product.stoc, 1)}
                        </span>
                        {product.stoc <= product.stoc_minim && (
                          <AlertTriangle className="w-4 h-4 text-yellow-500 inline ml-2" />
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {getSupplierName(product.furnizor_id)}
                      </TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              data-testid={`edit-product-${product.id}`}
                              onClick={() => openEditDialog(product)}
                              className="h-9 px-3 text-foreground hover:text-primary"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              data-testid={`delete-product-${product.id}`}
                              onClick={() => handleDelete(product)}
                              className="h-9 px-3 text-destructive hover:bg-destructive/10"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </ScrollArea>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-muted-foreground">
              Afișare {((currentPage - 1) * ITEMS_PER_PAGE) + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, totalProducts)} din {totalProducts}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="h-10 px-3 border-border text-foreground"
              >
                ««
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="h-10 px-4 border-border text-foreground"
              >
                « Înapoi
              </Button>
              <span className="px-4 text-foreground font-medium">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="h-10 px-4 border-border text-foreground"
              >
                Înainte »
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="h-10 px-3 border-border text-foreground"
              >
                »»
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="bg-card border-border max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="product-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground">
              {editingProduct ? 'Editare Produs' : 'Adăugare Produs Nou'}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label className="text-muted-foreground">Nume Produs *</Label>
                <Input
                  data-testid="input-nume"
                  value={formData.nume}
                  onChange={(e) => setFormData({...formData, nume: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground"
                  required
                />
              </div>

              <div>
                <Label className="text-muted-foreground">Categorie *</Label>
                <Select 
                  value={formData.categorie || "_none_"} 
                  onValueChange={(v) => setFormData({...formData, categorie: v === "_none_" ? "" : v})}
                >
                  <SelectTrigger data-testid="input-categorie" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue placeholder="Selectați categoria" />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    <SelectItem value="_none_">Selectați categoria</SelectItem>
                    {CATEGORIES.map(cat => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-muted-foreground">Furnizor</Label>
                <Select 
                  value={formData.furnizor_id || "_none_"} 
                  onValueChange={(v) => setFormData({...formData, furnizor_id: v === "_none_" ? "" : v})}
                >
                  <SelectTrigger data-testid="input-furnizor" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue placeholder="Selectați furnizorul" />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    <SelectItem value="_none_">Fără furnizor</SelectItem>
                    {suppliers.filter(sup => sup && sup.id).map(sup => (
                      <SelectItem key={sup.id} value={sup.id}>{sup.nume}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-muted-foreground">Cod de Bare</Label>
                <Input
                  data-testid="input-cod-bare"
                  value={formData.cod_bare}
                  onChange={(e) => setFormData({...formData, cod_bare: e.target.value})}
                  className={`h-12 mt-1 bg-background border-border text-foreground font-mono ${formData.cod_bare && !editingProduct ? 'border-primary bg-primary/5' : ''}`}
                  readOnly={!!formData.cod_bare && !editingProduct}
                />
                {formData.cod_bare && !editingProduct && (
                  <p className="text-xs text-primary mt-1">✓ Cod de bare scanat automat</p>
                )}
              </div>

              <div>
                <Label className="text-muted-foreground">Unitate Măsură *</Label>
                <Select 
                  value={formData.unitate} 
                  onValueChange={(v) => setFormData({...formData, unitate: v})}
                >
                  <SelectTrigger data-testid="input-unitate" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    {UNITS.map(u => (
                      <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-muted-foreground">Preț Achiziție (RON)</Label>
                <Input
                  data-testid="input-pret-achizitie"
                  type="number"
                  step="0.01"
                  value={formData.pret_achizitie}
                  onChange={(e) => setFormData({...formData, pret_achizitie: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                  placeholder="Opțional"
                />
              </div>

              <div>
                <Label className="text-muted-foreground">Preț Vânzare (RON) *</Label>
                <Input
                  data-testid="input-pret-vanzare"
                  type="number"
                  step="0.01"
                  value={formData.pret_vanzare}
                  onChange={(e) => setFormData({...formData, pret_vanzare: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                  required
                />
              </div>

              <div>
                <Label className="text-muted-foreground">TVA (%)</Label>
                <Input
                  data-testid="input-tva"
                  type="number"
                  value={formData.tva}
                  onChange={(e) => setFormData({...formData, tva: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                />
              </div>

              <div>
                <Label className="text-muted-foreground">Stoc Disponibil *</Label>
                <Input
                  data-testid="input-stoc"
                  type="number"
                  step="0.01"
                  value={formData.stoc}
                  onChange={(e) => setFormData({...formData, stoc: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                  required
                />
              </div>

              <div>
                <Label className="text-muted-foreground">Stoc Minim Alertă</Label>
                <Input
                  data-testid="input-stoc-minim"
                  type="number"
                  step="0.01"
                  value={formData.stoc_minim}
                  onChange={(e) => setFormData({...formData, stoc_minim: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                />
              </div>

              <div className="col-span-2">
                <Label className="text-muted-foreground">Descriere</Label>
                <Input
                  data-testid="input-descriere"
                  value={formData.descriere}
                  onChange={(e) => setFormData({...formData, descriere: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground"
                />
              </div>
            </div>

            <DialogFooter className="gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                className="h-12 px-6 border-border text-foreground"
              >
                Anulează
              </Button>
              <Button
                type="submit"
                data-testid="save-product"
                disabled={saving}
                className="h-12 px-6 bg-primary text-primary-foreground"
              >
                {saving ? 'Se salvează...' : (editingProduct ? 'Actualizează' : 'Creează')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Barcode Not Found Dialog */}
      <Dialog open={showNotFoundDialog} onOpenChange={setShowNotFoundDialog}>
        <DialogContent className="bg-card border-border" data-testid="barcode-not-found-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground flex items-center gap-3">
              <ScanLine className="w-6 h-6 text-yellow-500" />
              Produs Negăsit
            </DialogTitle>
          </DialogHeader>

          <div className="py-6">
            <div className="text-center space-y-4">
              <div className="w-20 h-20 mx-auto bg-yellow-500/10 rounded-full flex items-center justify-center">
                <Barcode className="w-10 h-10 text-yellow-500" />
              </div>
              
              <div>
                <p className="text-muted-foreground">Codul de bare scanat:</p>
                <p className="font-mono text-2xl font-bold text-primary mt-2">
                  {scannedBarcode}
                </p>
              </div>
              
              <p className="text-foreground">
                Nu există niciun produs cu acest cod de bare în baza de date.
              </p>
              
              {isAdmin && (
                <p className="text-muted-foreground text-sm">
                  Doriți să adăugați un produs nou cu acest cod?
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setShowNotFoundDialog(false)}
              className="h-12 px-6 border-border text-foreground"
            >
              Anulează
            </Button>
            {isAdmin && (
              <Button
                data-testid="add-product-with-barcode"
                onClick={() => openCreateDialogWithBarcode(scannedBarcode)}
                className="h-12 px-6 bg-primary text-primary-foreground"
              >
                <Plus className="w-5 h-5 mr-2" />
                Adaugă Produs Nou
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* CSV Import Dialog */}
      <Dialog open={showCsvDialog} onOpenChange={(open) => { if (!csvParsing && !csvImporting) setShowCsvDialog(open); }}>
        <DialogContent className="bg-card border-border max-w-5xl max-h-[90vh] overflow-y-auto" data-testid="csv-import-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground flex items-center gap-3">
              <Upload className="w-6 h-6 text-primary" />
              Import Produse
            </DialogTitle>
          </DialogHeader>

          {csvParsing ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
              <p className="text-muted-foreground">Se procesează fișierul CSV...</p>
            </div>
          ) : csvResult ? (
            <div className="space-y-6">
              {/* Summary */}
              <div className="flex gap-4 p-4 bg-secondary/30 rounded-sm">
                <div className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
                  <span className="text-sm text-foreground font-medium">
                    {csvItems.filter(i => i.enabled && i.action === 'create').length} produse noi
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
                  <span className="text-sm text-foreground font-medium">
                    {csvItems.filter(i => i.enabled && i.action === 'update').length} actualizări
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 rounded-full bg-muted-foreground"></span>
                  <span className="text-sm text-muted-foreground">
                    {csvItems.filter(i => !i.enabled).length} ignorate
                  </span>
                </div>
              </div>

              {/* Errors */}
              {csvResult.errors.length > 0 && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-sm">
                  <p className="text-sm font-medium text-destructive mb-2">Erori la parsare:</p>
                  {csvResult.errors.slice(0, 5).map((err, idx) => (
                    <p key={idx} className="text-xs text-destructive/80">{err}</p>
                  ))}
                  {csvResult.errors.length > 5 && (
                    <p className="text-xs text-destructive/60 mt-1">...și alte {csvResult.errors.length - 5} erori</p>
                  )}
                </div>
              )}

              {/* Select all controls */}
              <div className="flex items-center justify-between">
                <h4 className="font-heading text-sm uppercase text-muted-foreground">
                  Produse ({csvItems.filter(i => i.enabled).length} selectate din {csvItems.length})
                </h4>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCsvItems(prev => prev.map(i => ({ ...i, enabled: true })))}
                    className="text-xs text-muted-foreground"
                  >
                    Selectează toate
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCsvItems(prev => prev.map(i => ({ ...i, enabled: false })))}
                    className="text-xs text-muted-foreground"
                  >
                    Deselectează toate
                  </Button>
                </div>
              </div>

              {/* Items table - paginated */}
              {(() => {
                const csvTotalPages = Math.ceil(csvItems.length / CSV_PAGE_SIZE);
                const paginatedItems = csvItems.slice((csvPage - 1) * CSV_PAGE_SIZE, csvPage * CSV_PAGE_SIZE);
                return (
                  <>
                    {csvItems.length > CSV_PAGE_SIZE && (
                      <div className="flex items-center justify-between px-1 py-2 text-sm text-muted-foreground">
                        <span>Pagina {csvPage} din {csvTotalPages} ({csvItems.length} produse total)</span>
                        <div className="flex gap-1">
                          <Button variant="outline" size="sm" disabled={csvPage <= 1} onClick={() => setCsvPage(p => p - 1)} className="h-7 px-2 text-xs border-border">Anterior</Button>
                          <Button variant="outline" size="sm" disabled={csvPage >= csvTotalPages} onClick={() => setCsvPage(p => p + 1)} className="h-7 px-2 text-xs border-border">Următor</Button>
                        </div>
                      </div>
                    )}
                    <ScrollArea className="h-[400px]">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-border">
                            <TableHead className="w-10"></TableHead>
                            <TableHead className="text-muted-foreground">Denumire</TableHead>
                            <TableHead className="text-muted-foreground">Categorie</TableHead>
                            <TableHead className="text-muted-foreground text-right">Preț Achiziție</TableHead>
                            <TableHead className="text-muted-foreground text-right">Preț Vânzare</TableHead>
                            <TableHead className="text-muted-foreground text-right">Stoc</TableHead>
                            <TableHead className="text-muted-foreground text-center">Acțiune</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {paginatedItems.map(item => (
                            <TableRow 
                              key={item.idx} 
                              className={`border-border ${!item.enabled ? 'opacity-40' : ''}`}
                              data-testid={`csv-item-${item.idx}`}
                            >
                              <TableCell>
                                <button
                                  onClick={() => toggleCsvItem(item.idx)}
                                  className={`w-6 h-6 rounded-sm border flex items-center justify-center transition-colors ${
                                    item.enabled 
                                      ? 'bg-primary border-primary text-primary-foreground' 
                                      : 'border-border text-transparent'
                                  }`}
                                  data-testid={`csv-toggle-${item.idx}`}
                                >
                                  <Check className="w-4 h-4" />
                                </button>
                              </TableCell>
                              <TableCell>
                                <p className="text-foreground font-medium">{item.nume}</p>
                                {item.cod_bare && (
                                  <p className="text-xs font-mono text-muted-foreground">{item.cod_bare}</p>
                                )}
                              </TableCell>
                              <TableCell className="text-muted-foreground text-sm">{item.categorie}</TableCell>
                              <TableCell className="text-right font-mono text-foreground">
                                {item.pret_achizitie.toFixed(2)} RON
                              </TableCell>
                              <TableCell className="text-right font-mono font-bold text-primary">
                                {item.pret_vanzare.toFixed(2)} RON
                              </TableCell>
                              <TableCell className="text-right font-mono text-foreground">
                                {item.stoc} {item.unitate}
                              </TableCell>
                              <TableCell className="text-center">
                                {item.action === 'create' ? (
                                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-green-500/10 text-green-500">
                                    <Plus className="w-3 h-3 mr-1" /> Nou
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-blue-500/10 text-blue-500">
                                    <Edit className="w-3 h-3 mr-1" /> Actualizare
                                  </span>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ScrollArea>
                    {csvItems.length > CSV_PAGE_SIZE && (
                      <div className="flex items-center justify-center gap-1 py-2">
                        <Button variant="outline" size="sm" disabled={csvPage <= 1} onClick={() => setCsvPage(p => p - 1)} className="h-7 px-2 text-xs border-border">Anterior</Button>
                        <span className="text-xs text-muted-foreground px-2">{csvPage} / {csvTotalPages}</span>
                        <Button variant="outline" size="sm" disabled={csvPage >= csvTotalPages} onClick={() => setCsvPage(p => p + 1)} className="h-7 px-2 text-xs border-border">Următor</Button>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          ) : null}

          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowCsvDialog(false)}
              disabled={csvParsing || csvImporting}
              className="h-12 px-6 border-border text-foreground"
            >
              Anulează
            </Button>
            {csvResult && csvItems.length > 0 && (
              <Button
                data-testid="confirm-csv-import"
                onClick={confirmCsvImport}
                disabled={csvImporting || csvItems.filter(i => i.enabled).length === 0}
                className="h-12 px-6 bg-primary text-primary-foreground"
              >
                {csvImporting ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Se importă...</>
                ) : (
                  <>Importă {csvItems.filter(i => i.enabled).length} produse</>
                )}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete All Products Dialog */}
      <Dialog open={showDeleteAll} onOpenChange={setShowDeleteAll}>
        <DialogContent className="bg-card border-border max-w-md">
          <DialogHeader>
            <DialogTitle className="text-foreground flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-red-500" />
              Șterge TOATE Produsele
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-sm">
              <p className="text-sm text-red-400 font-medium">ATENȚIE! Această acțiune este ireversibilă!</p>
              <p className="text-sm text-red-400/70 mt-1">Toate cele {totalProducts} produse vor fi șterse definitiv din baza de date.</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Pentru confirmare, scrieți <span className="font-mono font-bold text-foreground">STERGE TOATE</span> mai jos:
              </p>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="STERGE TOATE"
                className="w-full h-12 px-4 rounded-md border border-border bg-background text-foreground font-mono text-center tracking-widest"
                data-testid="delete-all-confirm-input"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setShowDeleteAll(false); setDeleteConfirmText(''); }} className="h-12 border-border">
              Anulează
            </Button>
            <Button
              onClick={handleDeleteAll}
              disabled={deleteConfirmText !== 'STERGE TOATE' || deletingAll}
              className="h-12 bg-red-600 hover:bg-red-700 text-white"
              data-testid="delete-all-confirm-btn"
            >
              {deletingAll ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Se șterg...</> : 'Confirmă Ștergerea'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk TVA Dialog */}
      <Dialog open={showTvaBulk} onOpenChange={setShowTvaBulk}>
        <DialogContent className="bg-card border-border max-w-md">
          <DialogHeader>
            <DialogTitle className="text-foreground flex items-center gap-2">
              <Percent className="w-6 h-6 text-primary" />
              Schimbă Cota TVA la Toate Produsele
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-muted-foreground">
              Cota TVA nouă va fi aplicată la <span className="font-bold text-foreground">{totalProducts}</span> produse.
            </p>
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Noua cotă TVA (%)</label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={newTva}
                  onChange={(e) => setNewTva(e.target.value)}
                  placeholder="Ex: 19, 25..."
                  className="flex-1 h-12 px-4 rounded-md border border-border bg-background text-foreground text-lg font-mono text-center"
                  data-testid="bulk-tva-input"
                  autoFocus
                />
                <span className="text-2xl font-bold text-muted-foreground">%</span>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {[9, 19, 21, 25].map(val => (
                <button
                  key={val}
                  onClick={() => setNewTva(String(val))}
                  className={`px-4 py-2 rounded-md border text-sm font-medium transition-colors ${
                    newTva === String(val) 
                      ? 'border-primary bg-primary/10 text-primary' 
                      : 'border-border text-muted-foreground hover:text-foreground'
                  }`}
                  data-testid={`tva-preset-${val}`}
                >
                  {val}%
                </button>
              ))}
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setShowTvaBulk(false); setNewTva(''); }} className="h-12 border-border">
              Anulează
            </Button>
            <Button
              onClick={handleBulkTva}
              disabled={!newTva || updatingTva}
              className="h-12 bg-primary text-primary-foreground"
              data-testid="bulk-tva-confirm-btn"
            >
              {updatingTva ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Se actualizează...</> : `Schimbă la ${newTva || '?'}%`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
