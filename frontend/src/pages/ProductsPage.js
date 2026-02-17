import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ScrollArea } from '../components/ui/scroll-area';
import { formatCurrency, formatNumber, getStockStatus } from '../lib/utils';
import { Plus, Search, Edit, Trash2, Package, AlertTriangle } from 'lucide-react';
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
  
  const [showDialog, setShowDialog] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState(emptyProduct);
  const [saving, setSaving] = useState(false);

  const fetchProducts = useCallback(async () => {
    try {
      let url = `${API_URL}/products?`;
      if (searchQuery) url += `search=${searchQuery}&`;
      if (filterCategory) url += `categorie=${filterCategory}&`;
      if (showLowStock) url += `low_stock=true&`;
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  }, [API_URL, token, searchQuery, filterCategory, showLowStock]);

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

  useEffect(() => {
    fetchProducts();
  }, [searchQuery, filterCategory, showLowStock, fetchProducts]);

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
      pret_achizitie: parseFloat(formData.pret_achizitie),
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

  return (
    <div className="p-6 space-y-6" data-testid="products-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl uppercase tracking-tight text-foreground">
            Gestiune Produse
          </h1>
          <p className="text-muted-foreground mt-1">
            {products.length} produse în baza de date
          </p>
        </div>
        
        {isAdmin && (
          <Button
            data-testid="add-product-btn"
            onClick={openCreateDialog}
            className="h-12 px-6 bg-primary text-primary-foreground"
          >
            <Plus className="w-5 h-5 mr-2" />
            Adaugă Produs
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            data-testid="search-products"
            type="text"
            placeholder="Caută după nume sau cod de bare..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-12 pl-10 bg-card border-border text-foreground"
          />
        </div>
        
        <Select value={filterCategory || "all"} onValueChange={(v) => setFilterCategory(v === "all" ? "" : v)}>
          <SelectTrigger data-testid="filter-category" className="w-full md:w-64 h-12 bg-card border-border text-foreground">
            <SelectValue placeholder="Toate categoriile" />
          </SelectTrigger>
          <SelectContent className="bg-card border-border">
            <SelectItem value="all">Toate categoriile</SelectItem>
            {[...new Set([...CATEGORIES, ...categories])].map(cat => (
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
                  value={formData.categorie} 
                  onValueChange={(v) => setFormData({...formData, categorie: v})}
                >
                  <SelectTrigger data-testid="input-categorie" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue placeholder="Selectați categoria" />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    {CATEGORIES.map(cat => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-muted-foreground">Furnizor</Label>
                <Select 
                  value={formData.furnizor_id} 
                  onValueChange={(v) => setFormData({...formData, furnizor_id: v})}
                >
                  <SelectTrigger data-testid="input-furnizor" className="h-12 mt-1 bg-background border-border text-foreground">
                    <SelectValue placeholder="Selectați furnizorul" />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    <SelectItem value="">Fără furnizor</SelectItem>
                    {suppliers.map(sup => (
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
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                />
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
                <Label className="text-muted-foreground">Preț Achiziție (RON) *</Label>
                <Input
                  data-testid="input-pret-achizitie"
                  type="number"
                  step="0.01"
                  value={formData.pret_achizitie}
                  onChange={(e) => setFormData({...formData, pret_achizitie: e.target.value})}
                  className="h-12 mt-1 bg-background border-border text-foreground font-mono"
                  required
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
    </div>
  );
}
