from pydantic import BaseModel
from typing import List, Optional


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "casier"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    created_at: str


class ProductCreate(BaseModel):
    nume: str
    categorie: str
    furnizor_id: Optional[str] = None
    cod_bare: Optional[str] = None
    pret_achizitie: float = 0
    pret_vanzare: float
    tva: float = 21.0
    unitate: str = "buc"
    stoc: float = 0
    stoc_minim: float = 5
    descriere: Optional[str] = None


class ProductUpdate(BaseModel):
    nume: Optional[str] = None
    categorie: Optional[str] = None
    furnizor_id: Optional[str] = None
    cod_bare: Optional[str] = None
    pret_achizitie: Optional[float] = None
    pret_vanzare: Optional[float] = None
    tva: Optional[float] = None
    unitate: Optional[str] = None
    stoc: Optional[float] = None
    stoc_minim: Optional[float] = None
    descriere: Optional[str] = None


class ProductResponse(BaseModel):
    id: str
    nume: str
    categorie: str
    furnizor_id: Optional[str] = None
    cod_bare: Optional[str] = None
    pret_achizitie: float
    pret_vanzare: float
    tva: float
    unitate: str
    stoc: float
    stoc_minim: float
    descriere: Optional[str] = None
    created_at: str


class SupplierCreate(BaseModel):
    nume: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresa: Optional[str] = None


class SupplierResponse(BaseModel):
    id: str
    nume: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresa: Optional[str] = None
    created_at: str


class SaleItem(BaseModel):
    product_id: str
    nume: str
    cantitate: float
    pret_unitar: float
    tva: float


class SaleCreate(BaseModel):
    items: List[SaleItem]
    subtotal: float
    tva_total: float
    total: float
    discount_percent: float = 0
    metoda_plata: str
    suma_numerar: float = 0
    suma_card: float = 0
    casier_id: str
    transaction_id: Optional[str] = None
    fiscal_number: Optional[str] = None
    fiscal_status: str = "none"


class SaleResponse(BaseModel):
    id: str
    numar_bon: str
    items: List[SaleItem]
    subtotal: float
    tva_total: float
    total: float
    discount_percent: float
    metoda_plata: str
    suma_numerar: float
    suma_card: float
    casier_id: str
    casier_nume: str
    created_at: str
    transaction_id: Optional[str] = None
    fiscal_number: Optional[str] = None
    fiscal_status: str = "none"


class NIRItem(BaseModel):
    product_id: str
    nume: str
    cantitate: float
    pret_achizitie: float


class NIRCreate(BaseModel):
    furnizor_id: str
    numar_factura: str
    items: List[NIRItem]
    total: float


class NIRResponse(BaseModel):
    id: str
    numar_nir: str
    furnizor_id: str
    furnizor_nume: str
    numar_factura: str
    items: List[NIRItem]
    total: float
    created_at: str
