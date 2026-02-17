import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { formatCurrency, formatNumber, getStockStatus, getUnitLabel } from '../lib/utils';
import { Search, Barcode, X, Plus, Minus, Trash2, CreditCard, Banknote, Percent, Receipt, Check, AlertTriangle, Package } from 'lucide-react';
import { toast } from 'sonner';

export default function POSPage() {
  const { user, token, API_URL } = useAuth();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [discount, setDiscount] = useState(0);
  const [loading, setLoading] = useState(true);
  
  // Payment modal
  const [showPayment, setShowPayment] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [cashAmount, setCashAmount] = useState('');
  const [cardAmount, setCardAmount] = useState('');
  
  // Receipt modal
  const [showReceipt, setShowReceipt] = useState(false);
  const [lastSale, setLastSale] = useState(null);
  
  // Quantity edit modal
  const [editingItem, setEditingItem] = useState(null);
  const [editQuantity, setEditQuantity] = useState('');
  const [editPrice, setEditPrice] = useState('');
  
  // Discount modal
  const [showDiscount, setShowDiscount] = useState(false);
  const [discountInput, setDiscountInput] = useState('');
  
  const searchRef = useRef(null);

  const fetchProducts = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/products?search=${searchQuery}&categorie=${selectedCategory}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  }, [API_URL, token, searchQuery, selectedCategory]);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  }, [API_URL, token]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchProducts(), fetchCategories()]);
      setLoading(false);
    };
    init();
  }, [fetchProducts, fetchCategories]);

  useEffect(() => {
    fetchProducts();
  }, [searchQuery, selectedCategory, fetchProducts]);

  // Focus search on load
  useEffect(() => {
    if (searchRef.current) {
      searchRef.current.focus();
    }
  }, []);

  // Barcode scanner handler
  useEffect(() => {
    let barcodeBuffer = '';
    let barcodeTimeout;

    const handleKeyPress = async (e) => {
      // Only capture if not in an input field (except search)
      if (document.activeElement.tagName === 'INPUT' && document.activeElement !== searchRef.current) {
        return;
      }

      // Clear buffer after 100ms of no input (barcode scanners are fast)
      clearTimeout(barcodeTimeout);
      barcodeTimeout = setTimeout(() => {
        barcodeBuffer = '';
      }, 100);

      // Build barcode string
      if (e.key === 'Enter' && barcodeBuffer.length > 5) {
        // Lookup product by barcode
        try {
          const response = await fetch(`${API_URL}/products/barcode/${barcodeBuffer}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (response.ok) {
            const product = await response.json();
            addToCart(product);
            toast.success(`${product.nume} adăugat în coș`);
          } else {
            toast.error('Produs negăsit');
          }
        } catch (error) {
          console.error('Barcode lookup error:', error);
        }
        barcodeBuffer = '';
      } else if (e.key.length === 1) {
        barcodeBuffer += e.key;
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [API_URL, token]);

  const addToCart = (product) => {
    if (product.stoc <= 0) {
      toast.error('Produsul nu este în stoc');
      return;
    }

    setCart(prev => {
      const existing = prev.find(item => item.product_id === product.id);
      if (existing) {
        if (existing.cantitate >= product.stoc) {
          toast.error('Cantitate insuficientă în stoc');
          return prev;
        }
        return prev.map(item =>
          item.product_id === product.id
            ? { ...item, cantitate: item.cantitate + 1 }
            : item
        );
      }
      return [...prev, {
        product_id: product.id,
        nume: product.nume,
        cantitate: 1,
        pret_unitar: product.pret_vanzare,
        tva: product.tva,
        unitate: product.unitate,
        stoc_disponibil: product.stoc
      }];
    });
  };

  const updateQuantity = (productId, newQty) => {
    if (newQty <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart(prev => prev.map(item =>
      item.product_id === productId
        ? { ...item, cantitate: Math.min(newQty, item.stoc_disponibil) }
        : item
    ));
  };

  const removeFromCart = (productId) => {
    setCart(prev => prev.filter(item => item.product_id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setDiscount(0);
  };

  // Calculate totals
  const subtotal = cart.reduce((sum, item) => sum + (item.cantitate * item.pret_unitar), 0);
  const discountAmount = subtotal * (discount / 100);
  const subtotalAfterDiscount = subtotal - discountAmount;
  const tvaTotal = cart.reduce((sum, item) => {
    const itemTotal = item.cantitate * item.pret_unitar * (1 - discount / 100);
    return sum + (itemTotal * item.tva / (100 + item.tva));
  }, 0);
  const total = subtotalAfterDiscount;

  const handlePayment = async () => {
    if (cart.length === 0) return;

    let sumaCash = 0;
    let sumaCard = 0;

    if (paymentMethod === 'numerar') {
      sumaCash = total;
    } else if (paymentMethod === 'card') {
      sumaCard = total;
    } else if (paymentMethod === 'combinat') {
      sumaCash = parseFloat(cashAmount) || 0;
      sumaCard = parseFloat(cardAmount) || 0;
      if (sumaCash + sumaCard < total) {
        toast.error('Suma totală este insuficientă');
        return;
      }
    }

    try {
      const saleData = {
        items: cart.map(item => ({
          product_id: item.product_id,
          nume: item.nume,
          cantitate: item.cantitate,
          pret_unitar: item.pret_unitar,
          tva: item.tva
        })),
        subtotal: subtotal,
        tva_total: tvaTotal,
        total: total,
        discount_percent: discount,
        metoda_plata: paymentMethod,
        suma_numerar: sumaCash,
        suma_card: sumaCard,
        casier_id: user.id
      };

      const response = await fetch(`${API_URL}/sales`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(saleData)
      });

      if (response.ok) {
        const sale = await response.json();
        setLastSale(sale);
        setShowPayment(false);
        setShowReceipt(true);
        clearCart();
        fetchProducts(); // Refresh stock
        toast.success('Vânzare finalizată cu succes');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Eroare la procesarea vânzării');
      }
    } catch (error) {
      console.error('Payment error:', error);
      toast.error('Eroare la procesarea plății');
    }
  };

  const printReceipt = () => {
    window.print();
  };

  const applyDiscount = () => {
    const value = parseFloat(discountInput);
    if (value >= 0 && value <= 100) {
      setDiscount(value);
      setShowDiscount(false);
      setDiscountInput('');
      toast.success(`Reducere de ${value}% aplicată`);
    } else {
      toast.error('Introduceți o valoare între 0 și 100');
    }
  };

  const saveEditedItem = () => {
    if (!editingItem) return;
    const qty = parseFloat(editQuantity);
    const price = parseFloat(editPrice);
    
    if (qty > 0 && price > 0) {
      setCart(prev => prev.map(item =>
        item.product_id === editingItem.product_id
          ? { ...item, cantitate: qty, pret_unitar: price }
          : item
      ));
      setEditingItem(null);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background" data-testid="pos-page">
      {/* Left Panel - Products */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Search & Categories */}
        <div className="p-4 border-b border-border space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              ref={searchRef}
              data-testid="pos-search"
              type="text"
              placeholder="Caută produs sau scanează codul de bare..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-14 pl-12 pr-12 text-lg bg-card border-border placeholder:text-muted-foreground"
            />
            <Barcode className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          </div>

          {/* Categories */}
          <ScrollArea className="w-full whitespace-nowrap">
            <div className="flex gap-2 pb-2">
              <button
                data-testid="category-all"
                onClick={() => setSelectedCategory('')}
                className={`category-tag ${!selectedCategory ? 'active' : ''}`}
              >
                Toate
              </button>
              {categories.map(cat => (
                <button
                  key={cat}
                  data-testid={`category-${cat}`}
                  onClick={() => setSelectedCategory(cat)}
                  className={`category-tag ${selectedCategory === cat ? 'active' : ''}`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Products Grid */}
        <ScrollArea className="flex-1 p-4">
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
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {products.map(product => {
                const stockStatus = getStockStatus(product.stoc, product.stoc_minim);
                return (
                  <button
                    key={product.id}
                    data-testid={`product-${product.id}`}
                    onClick={() => addToCart(product)}
                    disabled={product.stoc <= 0}
                    className={`product-card text-left ${product.stoc <= 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <h3 className="font-medium text-foreground line-clamp-2 mb-2 min-h-[48px]">
                      {product.nume}
                    </h3>
                    <p className="font-mono text-2xl font-bold text-primary mb-1">
                      {formatCurrency(product.pret_vanzare)}
                    </p>
                    <div className="flex items-center justify-between text-sm">
                      <span className={stockStatus.className}>
                        {formatNumber(product.stoc, 1)} {product.unitate}
                      </span>
                      {product.stoc <= product.stoc_minim && product.stoc > 0 && (
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Right Panel - Cart */}
      <div className="w-96 xl:w-[420px] border-l border-border bg-card flex flex-col h-full">
        {/* Cart Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="font-heading text-xl uppercase tracking-wide text-foreground">
            Coș de cumpărături
          </h2>
          {cart.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              data-testid="clear-cart"
              onClick={clearCart}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Golește
            </Button>
          )}
        </div>

        {/* Cart Items */}
        <ScrollArea className="flex-1">
          {cart.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Receipt className="w-16 h-16 mb-4 opacity-50" />
              <p>Coșul este gol</p>
              <p className="text-sm mt-2">Adăugați produse din stânga</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {cart.map(item => (
                <div key={item.product_id} className="cart-item" data-testid={`cart-item-${item.product_id}`}>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">{item.nume}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {formatCurrency(item.pret_unitar)} / {item.unitate}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      data-testid={`qty-decrease-${item.product_id}`}
                      onClick={() => updateQuantity(item.product_id, item.cantitate - 1)}
                      className="qty-btn"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        setEditingItem(item);
                        setEditQuantity(item.cantitate.toString());
                        setEditPrice(item.pret_unitar.toString());
                      }}
                      className="w-16 h-12 bg-background border border-border rounded-sm font-mono text-lg text-center text-foreground hover:border-primary"
                    >
                      {formatNumber(item.cantitate, item.unitate === 'buc' ? 0 : 2)}
                    </button>
                    <button
                      data-testid={`qty-increase-${item.product_id}`}
                      onClick={() => updateQuantity(item.product_id, item.cantitate + 1)}
                      className="qty-btn"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                    <button
                      data-testid={`remove-item-${item.product_id}`}
                      onClick={() => removeFromCart(item.product_id)}
                      className="ml-2 p-2 text-destructive hover:bg-destructive/10 rounded-sm"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  
                  <p className="font-mono font-bold text-lg ml-4 min-w-[100px] text-right text-foreground">
                    {formatCurrency(item.cantitate * item.pret_unitar)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Cart Summary & Actions */}
        <div className="p-4 border-t border-border space-y-4 bg-card">
          {/* Totals */}
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-muted-foreground">
              <span>Subtotal</span>
              <span className="font-mono">{formatCurrency(subtotal)}</span>
            </div>
            {discount > 0 && (
              <div className="flex justify-between text-green-500">
                <span>Reducere ({discount}%)</span>
                <span className="font-mono">-{formatCurrency(discountAmount)}</span>
              </div>
            )}
            <div className="flex justify-between text-muted-foreground">
              <span>TVA inclus</span>
              <span className="font-mono">{formatCurrency(tvaTotal)}</span>
            </div>
            <div className="flex justify-between text-xl font-bold pt-2 border-t border-border text-foreground">
              <span>TOTAL</span>
              <span className="font-mono text-primary">{formatCurrency(total)}</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              data-testid="btn-discount"
              onClick={() => setShowDiscount(true)}
              className="h-14 border-border text-foreground hover:bg-secondary"
            >
              <Percent className="w-5 h-5 mr-2" />
              Reducere
            </Button>
            <Button
              variant="destructive"
              data-testid="btn-cancel"
              onClick={clearCart}
              className="h-14"
            >
              <X className="w-5 h-5 mr-2" />
              Anulează
            </Button>
          </div>

          {/* Payment Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              data-testid="btn-pay-cash"
              onClick={() => {
                setPaymentMethod('numerar');
                setShowPayment(true);
              }}
              disabled={cart.length === 0}
              className="payment-btn bg-green-600 hover:bg-green-700 text-white"
            >
              <Banknote className="w-6 h-6 mr-2" />
              NUMERAR
            </Button>
            <Button
              data-testid="btn-pay-card"
              onClick={() => {
                setPaymentMethod('card');
                setShowPayment(true);
              }}
              disabled={cart.length === 0}
              className="payment-btn bg-blue-600 hover:bg-blue-700 text-white"
            >
              <CreditCard className="w-6 h-6 mr-2" />
              CARD
            </Button>
          </div>
          <Button
            data-testid="btn-pay-combined"
            onClick={() => {
              setPaymentMethod('combinat');
              setCashAmount('');
              setCardAmount('');
              setShowPayment(true);
            }}
            disabled={cart.length === 0}
            className="w-full h-20 text-2xl font-bold uppercase bg-primary hover:bg-primary/90 text-primary-foreground animate-pulse-glow"
          >
            <Receipt className="w-8 h-8 mr-3" />
            PLATĂ COMBINATĂ
          </Button>
        </div>
      </div>

      {/* Payment Modal */}
      <Dialog open={showPayment} onOpenChange={setShowPayment}>
        <DialogContent className="bg-card border-border" data-testid="payment-modal">
          <DialogHeader>
            <DialogTitle className="font-heading text-2xl uppercase text-foreground">
              {paymentMethod === 'numerar' ? 'Plată Numerar' : 
               paymentMethod === 'card' ? 'Plată Card' : 'Plată Combinată'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-4">
            <div className="text-center">
              <p className="text-muted-foreground">Total de plată</p>
              <p className="font-mono text-4xl font-bold text-primary mt-2">
                {formatCurrency(total)}
              </p>
            </div>

            {paymentMethod === 'combinat' && (
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-muted-foreground">Suma numerar</label>
                  <Input
                    data-testid="cash-input"
                    type="number"
                    value={cashAmount}
                    onChange={(e) => setCashAmount(e.target.value)}
                    className="h-14 text-xl font-mono mt-1 bg-background border-border text-foreground"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Suma card</label>
                  <Input
                    data-testid="card-input"
                    type="number"
                    value={cardAmount}
                    onChange={(e) => setCardAmount(e.target.value)}
                    className="h-14 text-xl font-mono mt-1 bg-background border-border text-foreground"
                    placeholder="0.00"
                  />
                </div>
                <div className="flex justify-between text-lg font-medium text-foreground">
                  <span>Total introdus:</span>
                  <span className="font-mono">
                    {formatCurrency((parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0))}
                  </span>
                </div>
              </div>
            )}

            {paymentMethod === 'numerar' && (
              <div className="p-4 bg-secondary/50 rounded-sm">
                <p className="text-center text-muted-foreground">
                  Confirmați plata în numerar?
                </p>
              </div>
            )}

            {paymentMethod === 'card' && (
              <div className="p-4 bg-secondary/50 rounded-sm">
                <p className="text-center text-muted-foreground">
                  Procesați plata la terminal
                </p>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setShowPayment(false)}
              className="h-14 px-8 border-border text-foreground"
            >
              Anulează
            </Button>
            <Button
              data-testid="confirm-payment"
              onClick={handlePayment}
              className="h-14 px-8 bg-primary text-primary-foreground"
            >
              <Check className="w-5 h-5 mr-2" />
              Confirmă Plata
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Receipt Modal */}
      <Dialog open={showReceipt} onOpenChange={setShowReceipt}>
        <DialogContent className="bg-card border-border max-w-md" data-testid="receipt-modal">
          <DialogHeader>
            <DialogTitle className="font-heading text-2xl uppercase text-center text-foreground">
              Bon Fiscal
            </DialogTitle>
          </DialogHeader>

          {lastSale && (
            <div className="receipt p-4 bg-background rounded-sm receipt-printable">
              <div className="receipt-header">
                <h3 className="font-heading text-xl text-foreground">ANDREPAU</h3>
                <p className="text-muted-foreground text-xs">Materiale Construcții</p>
                <p className="text-muted-foreground text-xs mt-2">
                  {new Date(lastSale.created_at).toLocaleString('ro-RO')}
                </p>
                <p className="text-muted-foreground text-xs">Nr: {lastSale.numar_bon}</p>
              </div>

              <div className="space-y-1">
                {lastSale.items.map((item, idx) => (
                  <div key={idx} className="receipt-item text-foreground">
                    <span className="flex-1">{item.nume}</span>
                    <span className="text-right ml-2">
                      {formatNumber(item.cantitate)} x {formatCurrency(item.pret_unitar)}
                    </span>
                  </div>
                ))}
              </div>

              {lastSale.discount_percent > 0 && (
                <div className="receipt-item text-green-500 border-t border-dashed border-border mt-2 pt-2">
                  <span>Reducere ({lastSale.discount_percent}%)</span>
                  <span>-{formatCurrency(lastSale.subtotal * lastSale.discount_percent / 100)}</span>
                </div>
              )}

              <div className="receipt-total">
                <div className="receipt-item text-foreground">
                  <span>TVA inclus:</span>
                  <span>{formatCurrency(lastSale.tva_total)}</span>
                </div>
                <div className="receipt-item text-xl text-foreground">
                  <span>TOTAL:</span>
                  <span className="text-primary">{formatCurrency(lastSale.total)}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-dashed border-border text-center text-muted-foreground text-xs">
                <p>Plată: {lastSale.metoda_plata.toUpperCase()}</p>
                <p>Casier: {lastSale.casier_nume}</p>
                <p className="mt-2">Vă mulțumim!</p>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setShowReceipt(false)}
              className="h-12 border-border text-foreground"
            >
              Închide
            </Button>
            <Button
              data-testid="print-receipt"
              onClick={printReceipt}
              className="h-12 bg-primary text-primary-foreground"
            >
              <Receipt className="w-5 h-5 mr-2" />
              Printează Bon
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Discount Modal */}
      <Dialog open={showDiscount} onOpenChange={setShowDiscount}>
        <DialogContent className="bg-card border-border" data-testid="discount-modal">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground">
              Aplică Reducere
            </DialogTitle>
          </DialogHeader>

          <div className="py-4">
            <label className="text-sm text-muted-foreground">Procent reducere (%)</label>
            <Input
              data-testid="discount-input"
              type="number"
              value={discountInput}
              onChange={(e) => setDiscountInput(e.target.value)}
              className="h-14 text-xl font-mono mt-2 bg-background border-border text-foreground"
              placeholder="0"
              min="0"
              max="100"
              autoFocus
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDiscount(false)}
              className="border-border text-foreground"
            >
              Anulează
            </Button>
            <Button
              data-testid="apply-discount"
              onClick={applyDiscount}
              className="bg-primary text-primary-foreground"
            >
              Aplică
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Item Modal */}
      <Dialog open={!!editingItem} onOpenChange={() => setEditingItem(null)}>
        <DialogContent className="bg-card border-border" data-testid="edit-item-modal">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl uppercase text-foreground">
              Modifică Articol
            </DialogTitle>
          </DialogHeader>

          {editingItem && (
            <div className="py-4 space-y-4">
              <p className="font-medium text-foreground">{editingItem.nume}</p>
              
              <div>
                <label className="text-sm text-muted-foreground">
                  Cantitate ({getUnitLabel(editingItem.unitate)})
                </label>
                <Input
                  data-testid="edit-quantity"
                  type="number"
                  value={editQuantity}
                  onChange={(e) => setEditQuantity(e.target.value)}
                  className="h-14 text-xl font-mono mt-1 bg-background border-border text-foreground"
                  step="0.01"
                  min="0"
                />
              </div>
              
              <div>
                <label className="text-sm text-muted-foreground">Preț unitar (RON)</label>
                <Input
                  data-testid="edit-price"
                  type="number"
                  value={editPrice}
                  onChange={(e) => setEditPrice(e.target.value)}
                  className="h-14 text-xl font-mono mt-1 bg-background border-border text-foreground"
                  step="0.01"
                  min="0"
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditingItem(null)}
              className="border-border text-foreground"
            >
              Anulează
            </Button>
            <Button
              data-testid="save-edit"
              onClick={saveEditedItem}
              className="bg-primary text-primary-foreground"
            >
              Salvează
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
