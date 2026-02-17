import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ScrollArea } from '../components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { formatDate } from '../lib/utils';
import { Plus, Edit, Trash2, Truck, Phone, Mail, MapPin } from 'lucide-react';
import { toast } from 'sonner';

export default function SuppliersPage() {
  const { token, API_URL, isAdmin } = useAuth();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [showDialog, setShowDialog] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [formData, setFormData] = useState({ nume: '', telefon: '', email: '', adresa: '' });
  const [saving, setSaving] = useState(false);

  const fetchSuppliers = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/suppliers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuppliers(await response.json());
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchSuppliers();
  }, [fetchSuppliers]);

  const openCreateDialog = () => {
    setEditingSupplier(null);
    setFormData({ nume: '', telefon: '', email: '', adresa: '' });
    setShowDialog(true);
  };

  const openEditDialog = (supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      nume: supplier.nume,
      telefon: supplier.telefon || '',
      email: supplier.email || '',
      adresa: supplier.adresa || ''
    });
    setShowDialog(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nume.trim()) {
      toast.error('Numele furnizorului este obligatoriu');
      return;
    }

    setSaving(true);

    try {
      const url = editingSupplier 
        ? `${API_URL}/suppliers/${editingSupplier.id}`
        : `${API_URL}/suppliers`;
      
      const response = await fetch(url, {
        method: editingSupplier ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        toast.success(editingSupplier ? 'Furnizor actualizat' : 'Furnizor creat');
        setShowDialog(false);
        fetchSuppliers();
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

  const handleDelete = async (supplier) => {
    if (!window.confirm(`Sigur doriți să ștergeți furnizorul "${supplier.nume}"?`)) return;

    try {
      const response = await fetch(`${API_URL}/suppliers/${supplier.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Furnizor șters');
        fetchSuppliers();
      } else {
        toast.error('Eroare la ștergere');
      }
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="suppliers-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl uppercase tracking-tight text-foreground">
            Furnizori
          </h1>
          <p className="text-muted-foreground mt-1">
            {suppliers.length} furnizori înregistrați
          </p>
        </div>
        
        {isAdmin && (
          <Button
            data-testid="add-supplier-btn"
            onClick={openCreateDialog}
            className="h-12 px-6 bg-primary text-primary-foreground"
          >
            <Plus className="w-5 h-5 mr-2" />
            Adaugă Furnizor
          </Button>
        )}
      </div>

      {/* Suppliers Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      ) : suppliers.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Truck className="w-16 h-16 mb-4 opacity-50" />
            <p>Niciun furnizor înregistrat</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suppliers.map(supplier => (
            <Card key={supplier.id} data-testid={`supplier-card-${supplier.id}`} className="bg-card border-border">
              <CardHeader className="flex flex-row items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-primary/10 rounded-sm flex items-center justify-center">
                    <Truck className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-foreground">{supplier.nume}</CardTitle>
                    <p className="text-xs text-muted-foreground">
                      Înregistrat: {formatDate(supplier.created_at)}
                    </p>
                  </div>
                </div>
                {isAdmin && (
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      data-testid={`edit-supplier-${supplier.id}`}
                      onClick={() => openEditDialog(supplier)}
                      className="h-8 w-8 p-0 text-foreground hover:text-primary"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      data-testid={`delete-supplier-${supplier.id}`}
                      onClick={() => handleDelete(supplier)}
                      className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {supplier.telefon && (
                  <div className="flex items-center gap-2 text-sm">
                    <Phone className="w-4 h-4 text-muted-foreground" />
                    <span className="text-foreground">{supplier.telefon}</span>
                  </div>
                )}
                {supplier.email && (
                  <div className="flex items-center gap-2 text-sm">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <span className="text-foreground">{supplier.email}</span>
                  </div>
                )}
                {supplier.adresa && (
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span className="text-foreground">{supplier.adresa}</span>
                  </div>
                )}
                {!supplier.telefon && !supplier.email && !supplier.adresa && (
                  <p className="text-sm text-muted-foreground italic">
                    Fără informații de contact
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="bg-card border-border" data-testid="supplier-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground">
              {editingSupplier ? 'Editare Furnizor' : 'Adăugare Furnizor Nou'}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-muted-foreground">Nume Firmă *</Label>
              <Input
                data-testid="input-nume"
                value={formData.nume}
                onChange={(e) => setFormData({...formData, nume: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                required
                autoFocus
              />
            </div>

            <div>
              <Label className="text-muted-foreground">Telefon</Label>
              <Input
                data-testid="input-telefon"
                value={formData.telefon}
                onChange={(e) => setFormData({...formData, telefon: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                placeholder="0721 000 000"
              />
            </div>

            <div>
              <Label className="text-muted-foreground">Email</Label>
              <Input
                data-testid="input-email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                placeholder="contact@firma.ro"
              />
            </div>

            <div>
              <Label className="text-muted-foreground">Adresă</Label>
              <Input
                data-testid="input-adresa"
                value={formData.adresa}
                onChange={(e) => setFormData({...formData, adresa: e.target.value})}
                className="h-12 mt-1 bg-background border-border text-foreground"
                placeholder="Oraș, Strada, Nr."
              />
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
                data-testid="save-supplier"
                disabled={saving}
                className="h-12 px-6 bg-primary text-primary-foreground"
              >
                {saving ? 'Se salvează...' : (editingSupplier ? 'Actualizează' : 'Creează')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
