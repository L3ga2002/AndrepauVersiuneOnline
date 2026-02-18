import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { formatCurrency, formatNumber } from '../lib/utils';
import { Search, Barcode, X, Plus, Minus, Trash2, CreditCard, Banknote, Percent, Receipt, PauseCircle, FileText, Ticket, Clock, Loader2, CheckCircle, Building2, Split } from 'lucide-react';
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
  
  // Payment modal - Combined payment
  const [showCombinedPayment, setShowCombinedPayment] = useState(false);
  const [cashAmount, setCashAmount] = useState('');
  const [cardAmount, setCardAmount] = useState('');
  const [ticketAmount, setTicketAmount] = useState('');
  
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
  
  // Hold/Pending orders
  const [holdOrders, setHoldOrders] = useState([]);
  const [showHoldOrders, setShowHoldOrders] = useState(false);
  
  // Invoice modal
  const [showInvoice, setShowInvoice] = useState(false);
  const [invoiceData, setInvoiceData] = useState({ firma: '', cui: '', adresa: '', nr_reg_com: '', platitor_tva: false });
  const [searchingCUI, setSearchingCUI] = useState(false);
  
  const searchRef = useRef(null);

  const fetchProducts = useCallback(async () => {
    try {
      let url = `${API_URL}/products?limit=100&`;
      if (searchQuery) url += `search=${encodeURIComponent(searchQuery)}&`;
      if (selectedCategory) url += `categorie=${encodeURIComponent(selectedCategory)}&`;
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setProducts(data.products || []);
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
      setCategories(data.filter(c => c && c.trim() !== ''));
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

  // Barcode scanner handler - FIXED
  useEffect(() => {
    let barcodeBuffer = '';
    let lastKeyTime = 0;

    const handleKeyDown = async (e) => {
      const currentTime = Date.now();
      const timeDiff = currentTime - lastKeyTime;
      lastKeyTime = currentTime;

      // Skip if in modal inputs
      const activeEl = document.activeElement;
      const isInModal = activeEl.closest('[role="dialog"]');
      if (isInModal && activeEl.tagName === 'INPUT') {
        return;
      }

      // Fast typing detection (barcode scanners type very fast)
      if (e.key === 'Enter' && barcodeBuffer.length >= 5) {
        e.preventDefault();
        e.stopPropagation();
        
        const barcode = barcodeBuffer;
        barcodeBuffer = '';
        
        // Clear search field
        if (searchRef.current) {
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
            addToCart(product);
            toast.success(`${product.nume} adăugat în coș`);
          } else {
            toast.error(`Produs negăsit: ${barcode}`);
          }
        } catch (error) {
          console.error('Barcode lookup error:', error);
          toast.error('Eroare la căutare produs');
        }
      } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey) {
        // Add to buffer if fast typing or if it's a digit
        if (timeDiff < 100 || /^\d$/.test(e.key) || barcodeBuffer.length > 0) {
          barcodeBuffer += e.key;
        }
        
        // Clear buffer after 200ms of no input
        setTimeout(() => {
          if (Date.now() - lastKeyTime > 200) {
            barcodeBuffer = '';
          }
        }, 250);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [API_URL, token]);

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.product_id === product.id);
      if (existing) {
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
        ? { ...item, cantitate: newQty }
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

  // Hold current order
  const holdOrder = () => {
    if (cart.length === 0) {
      toast.error('Coșul este gol');
      return;
    }
    const holdOrder = {
      id: Date.now(),
      items: [...cart],
      discount: discount,
      time: new Date().toLocaleTimeString('ro-RO')
    };
    setHoldOrders(prev => [...prev, holdOrder]);
    clearCart();
    toast.success('Comandă pusă în așteptare');
  };

  // Restore held order
  const restoreOrder = (orderId) => {
    const order = holdOrders.find(o => o.id === orderId);
    if (order) {
      setCart(order.items);
      setDiscount(order.discount);
      setHoldOrders(prev => prev.filter(o => o.id !== orderId));
      setShowHoldOrders(false);
      toast.success('Comandă restaurată');
    }
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

  const handlePayment = async (method) => {
    if (cart.length === 0) return;

    let sumaCash = 0;
    let sumaCard = 0;
    let sumaTichete = 0;

    if (method === 'numerar') {
      sumaCash = total;
    } else if (method === 'card') {
      sumaCard = total;
    } else if (method === 'tichete') {
      sumaTichete = total;
    } else if (method === 'combinat') {
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
        metoda_plata: method,
        suma_numerar: sumaCash,
        suma_card: sumaCard + sumaTichete,
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
        fetchProducts();
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

  // Search company by CUI in ANAF
  const searchCUI = async () => {
    if (!invoiceData.cui || invoiceData.cui.trim().length < 5) {
      toast.error('Introduceți un CUI valid (minim 5 cifre)');
      return;
    }
    
    setSearchingCUI(true);
    try {
      const response = await fetch(`${API_URL}/anaf/search-cui`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ cui: invoiceData.cui })
      });
      
      if (response.ok) {
        const data = await response.json();
        setInvoiceData({
          ...invoiceData,
          firma: data.denumire || '',
          adresa: data.adresa || '',
          nr_reg_com: data.nr_reg_com || '',
          platitor_tva: data.platitor_tva || false
        });
        if (data.from_cache) {
          toast.success(`Firmă găsită în cache: ${data.denumire}`);
        } else {
          toast.success(`Firmă găsită: ${data.denumire}`);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Firma nu a fost găsită');
      }
    } catch (error) {
      toast.error('Eroare la căutarea firmei');
    } finally {
      setSearchingCUI(false);
    }
  };

  // Save company manually to cache
  const saveCompanyToCache = async () => {
    if (!invoiceData.cui || !invoiceData.firma) {
      toast.error('Completați cel puțin CUI și Nume Firmă');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/companies/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          cui: invoiceData.cui,
          denumire: invoiceData.firma,
          adresa: invoiceData.adresa,
          nr_reg_com: invoiceData.nr_reg_com,
          platitor_tva: invoiceData.platitor_tva
        })
      });
      
      if (response.ok) {
        toast.success('Firmă salvată în baza de date locală');
      } else {
        toast.error('Eroare la salvarea firmei');
      }
    } catch (error) {
      toast.error('Eroare la salvarea firmei');
    }
  };

  // Handle combined payment
  const handleCombinedPayment = async () => {
    const cash = parseFloat(cashAmount) || 0;
    const card = parseFloat(cardAmount) || 0;
    const tickets = parseFloat(ticketAmount) || 0;
    const totalPaid = cash + card + tickets;
    
    if (totalPaid < total) {
      toast.error(`Suma totală (${formatCurrency(totalPaid)}) este mai mică decât totalul (${formatCurrency(total)})`);
      return;
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
        metoda_plata: 'combinat',
        suma_numerar: cash,
        suma_card: card + tickets,
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
        setShowCombinedPayment(false);
        setShowReceipt(true);
        clearCart();
        fetchProducts();
        setCashAmount('');
        setCardAmount('');
        setTicketAmount('');
        toast.success('Vânzare finalizată cu succes');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Eroare la procesarea vânzării');
      }
    } catch (error) {
      toast.error('Eroare la procesarea plății');
    }
  };

  // Generate simplified invoice
  const generateInvoice = async () => {
    if (!invoiceData.firma || !invoiceData.cui) {
      toast.error('Completați datele firmei');
      return;
    }
    
    // Process as regular sale but mark as invoice
    await handlePayment('numerar');
    setShowInvoice(false);
    setInvoiceData({ firma: '', cui: '', adresa: '', nr_reg_com: '', platitor_tva: false });
    toast.success('Factură simplificată generată');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background" data-testid="pos-page">
      {/* Left Panel - Products */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Search & Categories */}
        <div className="p-3 border-b border-border space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              ref={searchRef}
              data-testid="pos-search"
              type="text"
              placeholder="Caută produs sau scanează cod bare..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-12 pl-10 pr-10 text-base bg-card border-border"
            />
            <Barcode className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          </div>

          {/* Categories */}
          <ScrollArea className="w-full whitespace-nowrap">
            <div className="flex gap-2 pb-1">
              <button
                onClick={() => setSelectedCategory('')}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                  !selectedCategory 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                TOATE
              </button>
              {categories.slice(0, 8).map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-4 py-2 rounded text-sm font-medium transition-colors whitespace-nowrap ${
                    selectedCategory === cat 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  {cat.toUpperCase()}
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Products Grid - REDESIGNED */}
        <ScrollArea className="flex-1 p-3">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="spinner" />
            </div>
          ) : products.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <p>Niciun produs găsit</p>
            </div>
          ) : (
            <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
              {products.map(product => (
                <button
                  key={product.id}
                  data-testid={`product-${product.id}`}
                  onClick={() => addToCart(product)}
                  className="bg-card border border-border rounded p-3 text-left hover:border-primary hover:bg-card/80 transition-all active:scale-95"
                >
                  <p className="text-sm font-medium text-foreground line-clamp-2 min-h-[40px] leading-tight">
                    {product.nume}
                  </p>
                  <p className="text-lg font-bold text-primary mt-1">
                    {formatCurrency(product.pret_vanzare)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {product.unitate}
                  </p>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Right Panel - Cart */}
      <div className="w-80 xl:w-96 border-l border-border bg-card flex flex-col h-full">
        {/* Cart Header */}
        <div className="p-3 border-b border-border flex items-center justify-between">
          <h2 className="font-bold text-lg text-foreground">COȘ</h2>
          <div className="flex gap-2">
            {holdOrders.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowHoldOrders(true)}
                className="h-8 px-2 border-yellow-500 text-yellow-500"
              >
                <PauseCircle className="w-4 h-4 mr-1" />
                {holdOrders.length}
              </Button>
            )}
            {cart.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearCart}
                className="h-8 text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Cart Items */}
        <ScrollArea className="flex-1">
          {cart.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
              <Receipt className="w-12 h-12 mb-2 opacity-50" />
              <p className="text-sm">Coșul este gol</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {cart.map(item => (
                <div key={item.product_id} className="p-3 hover:bg-secondary/30">
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium text-foreground flex-1 pr-2">{item.nume}</p>
                    <button
                      onClick={() => removeFromCart(item.product_id)}
                      className="text-destructive hover:bg-destructive/10 p-1 rounded"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => updateQuantity(item.product_id, item.cantitate - 1)}
                        className="w-8 h-8 bg-secondary rounded flex items-center justify-center hover:bg-secondary/80"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          setEditingItem(item);
                          setEditQuantity(item.cantitate.toString());
                          setEditPrice(item.pret_unitar.toString());
                        }}
                        className="w-12 h-8 bg-background border border-border rounded text-sm font-mono"
                      >
                        {formatNumber(item.cantitate, item.unitate === 'buc' ? 0 : 2)}
                      </button>
                      <button
                        onClick={() => updateQuantity(item.product_id, item.cantitate + 1)}
                        className="w-8 h-8 bg-secondary rounded flex items-center justify-center hover:bg-secondary/80"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                    <p className="font-bold text-primary">
                      {formatCurrency(item.cantitate * item.pret_unitar)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Cart Summary & Actions */}
        <div className="p-3 border-t border-border space-y-3 bg-card">
          {/* Totals */}
          <div className="space-y-1 text-sm">
            {discount > 0 && (
              <div className="flex justify-between text-green-500">
                <span>Reducere ({discount}%)</span>
                <span>-{formatCurrency(discountAmount)}</span>
              </div>
            )}
            <div className="flex justify-between text-muted-foreground">
              <span>TVA inclus</span>
              <span>{formatCurrency(tvaTotal)}</span>
            </div>
            <div className="flex justify-between text-xl font-bold pt-2 border-t border-border text-foreground">
              <span>TOTAL</span>
              <span className="text-primary">{formatCurrency(total)}</span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-4 gap-2">
            <Button
              variant="outline"
              onClick={() => setShowDiscount(true)}
              className="h-10 text-xs border-border"
            >
              <Percent className="w-4 h-4 mr-1" />
              %
            </Button>
            <Button
              variant="outline"
              onClick={holdOrder}
              disabled={cart.length === 0}
              className="h-10 text-xs border-yellow-500 text-yellow-500 hover:bg-yellow-500/10"
              title="Pune coșul în așteptare"
            >
              <PauseCircle className="w-4 h-4 mr-1" />
              AȘTEAPTĂ
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowHoldOrders(true)}
              disabled={holdOrders.length === 0}
              className={`h-10 text-xs ${holdOrders.length > 0 ? 'border-yellow-500 text-yellow-500' : 'border-border'}`}
              title="Vezi coșurile în așteptare"
            >
              <Clock className="w-4 h-4 mr-1" />
              {holdOrders.length > 0 ? holdOrders.length : '0'}
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowInvoice(true)}
              disabled={cart.length === 0}
              className="h-10 text-xs border-border"
            >
              <FileText className="w-4 h-4 mr-1" />
              FACT
            </Button>
          </div>

          {/* Payment Buttons - Big like ForIT */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={() => handlePayment('numerar')}
              disabled={cart.length === 0}
              className="h-14 text-lg font-bold bg-green-600 hover:bg-green-700 text-white"
            >
              <Banknote className="w-5 h-5 mr-2" />
              NUMERAR
            </Button>
            <Button
              onClick={() => handlePayment('card')}
              disabled={cart.length === 0}
              className="h-14 text-lg font-bold bg-blue-600 hover:bg-blue-700 text-white"
            >
              <CreditCard className="w-5 h-5 mr-2" />
              CARD
            </Button>
          </div>
          
          <div className="grid grid-cols-3 gap-2">
            <Button
              onClick={() => handlePayment('tichete')}
              disabled={cart.length === 0}
              className="h-12 font-bold bg-purple-600 hover:bg-purple-700 text-white"
            >
              <Ticket className="w-4 h-4 mr-1" />
              TICHETE
            </Button>
            <Button
              onClick={() => setShowCombinedPayment(true)}
              disabled={cart.length === 0}
              className="h-12 font-bold bg-orange-600 hover:bg-orange-700 text-white"
            >
              <Split className="w-4 h-4 mr-1" />
              COMBINAT
            </Button>
            <Button
              variant="destructive"
              onClick={clearCart}
              disabled={cart.length === 0}
              className="h-12 font-bold"
            >
              <X className="w-4 h-4 mr-1" />
              ANULEAZĂ
            </Button>
          </div>
        </div>
      </div>

      {/* Receipt Modal */}
      <Dialog open={showReceipt} onOpenChange={setShowReceipt}>
        <DialogContent className="bg-card border-border max-w-md">
          <DialogHeader>
            <DialogTitle className="text-center text-foreground">BON FISCAL</DialogTitle>
          </DialogHeader>

          {lastSale && (
            <div className="font-mono text-sm p-4 bg-background rounded receipt-printable">
              <div className="text-center border-b border-dashed border-border pb-3 mb-3">
                <h3 className="font-bold text-lg">ANDREPAU</h3>
                <p className="text-xs text-muted-foreground">Materiale Construcții</p>
                <p className="text-xs text-muted-foreground mt-2">
                  {new Date(lastSale.created_at).toLocaleString('ro-RO')}
                </p>
                <p className="text-xs">Nr: {lastSale.numar_bon}</p>
              </div>

              <div className="space-y-1 text-xs">
                {lastSale.items.map((item, idx) => (
                  <div key={idx} className="flex justify-between">
                    <span className="flex-1 truncate">{item.nume}</span>
                    <span className="ml-2">{formatNumber(item.cantitate)} x {formatCurrency(item.pret_unitar)}</span>
                  </div>
                ))}
              </div>

              <div className="border-t border-dashed border-border mt-3 pt-3 text-sm">
                <div className="flex justify-between font-bold text-lg">
                  <span>TOTAL:</span>
                  <span className="text-primary">{formatCurrency(lastSale.total)}</span>
                </div>
                <p className="text-center text-xs text-muted-foreground mt-3">
                  Plată: {lastSale.metoda_plata.toUpperCase()} | Casier: {lastSale.casier_nume}
                </p>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowReceipt(false)}>Închide</Button>
            <Button onClick={printReceipt} className="bg-primary">
              <Receipt className="w-4 h-4 mr-2" />
              Print
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Discount Modal */}
      <Dialog open={showDiscount} onOpenChange={setShowDiscount}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground">Reducere %</DialogTitle>
          </DialogHeader>
          <Input
            type="number"
            value={discountInput}
            onChange={(e) => setDiscountInput(e.target.value)}
            className="h-14 text-2xl font-mono text-center"
            placeholder="0"
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDiscount(false)}>Anulează</Button>
            <Button onClick={applyDiscount} className="bg-primary">Aplică</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Item Modal */}
      <Dialog open={!!editingItem} onOpenChange={() => setEditingItem(null)}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground">Modifică</DialogTitle>
          </DialogHeader>
          {editingItem && (
            <div className="space-y-4">
              <p className="font-medium">{editingItem.nume}</p>
              <div>
                <label className="text-sm text-muted-foreground">Cantitate</label>
                <Input
                  type="number"
                  value={editQuantity}
                  onChange={(e) => setEditQuantity(e.target.value)}
                  className="h-12 text-xl font-mono mt-1"
                  step="0.01"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Preț (RON)</label>
                <Input
                  type="number"
                  value={editPrice}
                  onChange={(e) => setEditPrice(e.target.value)}
                  className="h-12 text-xl font-mono mt-1"
                  step="0.01"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingItem(null)}>Anulează</Button>
            <Button onClick={saveEditedItem} className="bg-primary">Salvează</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Hold Orders Modal */}
      <Dialog open={showHoldOrders} onOpenChange={setShowHoldOrders}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground flex items-center gap-2">
              <Clock className="w-5 h-5 text-yellow-500" />
              Comenzi în Așteptare ({holdOrders.length})
            </DialogTitle>
          </DialogHeader>
          {holdOrders.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Clock className="w-12 h-12 mb-2 opacity-50" />
              <p>Nu există comenzi în așteptare</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-auto">
              {holdOrders.map(order => (
                <button
                  key={order.id}
                  onClick={() => restoreOrder(order.id)}
                  className="w-full p-4 bg-secondary rounded-lg text-left hover:bg-secondary/80 border border-border transition-colors"
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-foreground">{order.items.length} produse</span>
                    <span className="text-muted-foreground text-sm">{order.time}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">
                      {order.items.map(i => i.nume).slice(0, 2).join(', ')}
                      {order.items.length > 2 && '...'}
                    </span>
                    <span className="text-lg font-bold text-primary">
                      {formatCurrency(order.items.reduce((s, i) => s + i.cantitate * i.pret_unitar, 0))}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHoldOrders(false)}>Închide</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Invoice Modal with ANAF Search */}
      <Dialog open={showInvoice} onOpenChange={setShowInvoice}>
        <DialogContent className="bg-card border-border max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-foreground flex items-center gap-2">
              <Building2 className="w-5 h-5 text-primary" />
              Factură Simplificată
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* CUI Search */}
            <div>
              <label className="text-sm text-muted-foreground">CUI *</label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={invoiceData.cui}
                  onChange={(e) => setInvoiceData({...invoiceData, cui: e.target.value})}
                  className="h-12 flex-1 font-mono"
                  placeholder="12345678 sau RO12345678"
                  onKeyDown={(e) => e.key === 'Enter' && searchCUI()}
                />
                <Button
                  onClick={searchCUI}
                  disabled={searchingCUI || !invoiceData.cui}
                  className="h-12 px-4 bg-primary"
                >
                  {searchingCUI ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <Search className="w-5 h-5 mr-1" />
                      Caută
                    </>
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Introduceți CUI-ul și apăsați Caută pentru completare automată din ANAF
              </p>
            </div>

            {/* Auto-filled data */}
            <div>
              <label className="text-sm text-muted-foreground">Nume Firmă *</label>
              <Input
                value={invoiceData.firma}
                onChange={(e) => setInvoiceData({...invoiceData, firma: e.target.value})}
                className="h-12 mt-1"
                placeholder="Se completează automat din ANAF"
              />
            </div>
            
            <div>
              <label className="text-sm text-muted-foreground">Adresă Sediu</label>
              <Input
                value={invoiceData.adresa}
                onChange={(e) => setInvoiceData({...invoiceData, adresa: e.target.value})}
                className="h-12 mt-1"
                placeholder="Se completează automat din ANAF"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-muted-foreground">Nr. Reg. Comerț</label>
                <Input
                  value={invoiceData.nr_reg_com}
                  onChange={(e) => setInvoiceData({...invoiceData, nr_reg_com: e.target.value})}
                  className="h-12 mt-1 font-mono"
                  placeholder="J40/xxx/xxxx"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Plătitor TVA</label>
                <div className="h-12 mt-1 flex items-center px-3 bg-secondary rounded-md">
                  {invoiceData.platitor_tva ? (
                    <span className="flex items-center gap-2 text-green-500">
                      <CheckCircle className="w-4 h-4" />
                      Da
                    </span>
                  ) : (
                    <span className="text-muted-foreground">Nu</span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="p-4 bg-secondary/50 rounded-lg border border-border">
              <p className="text-sm text-muted-foreground">Total de facturat:</p>
              <p className="text-3xl font-bold text-primary">{formatCurrency(total)}</p>
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => {
              setShowInvoice(false);
              setInvoiceData({ firma: '', cui: '', adresa: '', nr_reg_com: '', platitor_tva: false });
            }}>
              Anulează
            </Button>
            <Button 
              onClick={generateInvoice} 
              disabled={!invoiceData.firma || !invoiceData.cui}
              className="bg-primary"
            >
              <FileText className="w-4 h-4 mr-2" />
              Generează Factură
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Combined Payment Modal */}
      <Dialog open={showCombinedPayment} onOpenChange={setShowCombinedPayment}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground flex items-center gap-2">
              <Split className="w-5 h-5 text-orange-500" />
              Plată Combinată
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-secondary/50 rounded-lg border border-border text-center">
              <p className="text-sm text-muted-foreground">Total de plată:</p>
              <p className="text-3xl font-bold text-primary">{formatCurrency(total)}</p>
            </div>
            
            <div>
              <label className="text-sm text-muted-foreground flex items-center gap-2">
                <Banknote className="w-4 h-4 text-green-500" />
                Numerar (RON)
              </label>
              <Input
                type="number"
                step="0.01"
                value={cashAmount}
                onChange={(e) => setCashAmount(e.target.value)}
                className="h-14 mt-1 text-xl font-mono text-center"
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="text-sm text-muted-foreground flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-blue-500" />
                Card (RON)
              </label>
              <Input
                type="number"
                step="0.01"
                value={cardAmount}
                onChange={(e) => setCardAmount(e.target.value)}
                className="h-14 mt-1 text-xl font-mono text-center"
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="text-sm text-muted-foreground flex items-center gap-2">
                <Ticket className="w-4 h-4 text-purple-500" />
                Tichete (RON)
              </label>
              <Input
                type="number"
                step="0.01"
                value={ticketAmount}
                onChange={(e) => setTicketAmount(e.target.value)}
                className="h-14 mt-1 text-xl font-mono text-center"
                placeholder="0.00"
              />
            </div>
            
            <div className="p-3 bg-background rounded-lg border border-border">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Sumă introdusă:</span>
                <span className={`font-bold ${
                  (parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0) + (parseFloat(ticketAmount) || 0) >= total
                    ? 'text-green-500'
                    : 'text-red-500'
                }`}>
                  {formatCurrency((parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0) + (parseFloat(ticketAmount) || 0))}
                </span>
              </div>
              {(parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0) + (parseFloat(ticketAmount) || 0) > total && (
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-muted-foreground">Rest:</span>
                  <span className="font-bold text-green-500">
                    {formatCurrency((parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0) + (parseFloat(ticketAmount) || 0) - total)}
                  </span>
                </div>
              )}
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => {
              setShowCombinedPayment(false);
              setCashAmount('');
              setCardAmount('');
              setTicketAmount('');
            }}>
              Anulează
            </Button>
            <Button 
              onClick={handleCombinedPayment}
              disabled={(parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0) + (parseFloat(ticketAmount) || 0) < total}
              className="bg-orange-600 hover:bg-orange-700"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Finalizează Plata
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
