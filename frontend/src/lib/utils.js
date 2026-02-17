import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value) {
  return new Intl.NumberFormat('ro-RO', {
    style: 'currency',
    currency: 'RON',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

export function formatNumber(value, decimals = 2) {
  return new Intl.NumberFormat('ro-RO', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
}

export function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('ro-RO', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatDateShort(dateString) {
  return new Date(dateString).toLocaleDateString('ro-RO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

export function getStockStatus(stoc, stocMinim) {
  if (stoc <= 0) return { status: 'critical', label: 'Fără stoc', className: 'stock-critical' };
  if (stoc <= stocMinim) return { status: 'low', label: 'Stoc scăzut', className: 'stock-low' };
  return { status: 'good', label: 'În stoc', className: 'stock-good' };
}

export function getUnitLabel(unit) {
  const units = {
    'buc': 'bucăți',
    'sac': 'saci',
    'kg': 'kg',
    'metru': 'metri',
    'litru': 'litri',
    'rola': 'role'
  };
  return units[unit] || unit;
}

export function calculateTVA(price, tvaPercent) {
  return price * (tvaPercent / 100);
}

export function calculatePriceWithoutTVA(priceWithTVA, tvaPercent) {
  return priceWithTVA / (1 + tvaPercent / 100);
}
