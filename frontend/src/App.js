import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import POSPage from "./pages/POSPage";
import ProductsPage from "./pages/ProductsPage";
import StockPage from "./pages/StockPage";
import ReportsPage from "./pages/ReportsPage";
import SuppliersPage from "./pages/SuppliersPage";
import SettingsPage from "./pages/SettingsPage";
import Layout from "./components/Layout";
import PWAInstallPrompt from "./components/PWAInstallPrompt";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Register service worker for PWA
const registerServiceWorker = () => {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/service-worker.js')
        .then((registration) => {
          console.log('Service Worker registered:', registration.scope);
        })
        .catch((error) => {
          console.log('Service Worker registration failed:', error);
        });
    });
  }
};

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Admin Route component
const AdminRoute = ({ children }) => {
  const { user, loading, isAdmin } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (!isAdmin) {
    return <Navigate to="/pos" replace />;
  }
  
  return children;
};

// Auth redirect - if logged in, go to POS
const AuthRedirect = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }
  
  if (user) {
    return <Navigate to="/pos" replace />;
  }
  
  return children;
};

// Initialize database
const InitApp = () => {
  useEffect(() => {
    const seedDatabase = async () => {
      try {
        await axios.post(`${API_URL}/seed`);
        console.log('Database seeded successfully');
      } catch (error) {
        // Database might already be seeded, that's ok
        console.log('Database seed skipped or already seeded');
      }
    };
    seedDatabase();
  }, []);
  
  return null;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={
        <AuthRedirect>
          <LoginPage />
        </AuthRedirect>
      } />
      
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="/pos" replace />} />
        <Route path="pos" element={<POSPage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="stock" element={<StockPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="suppliers" element={
          <AdminRoute>
            <SuppliersPage />
          </AdminRoute>
        } />
        <Route path="settings" element={
          <AdminRoute>
            <SettingsPage />
          </AdminRoute>
        } />
      </Route>
      
      <Route path="*" element={<Navigate to="/pos" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <InitApp />
          <AppRoutes />
          <Toaster 
            position="top-right"
            toastOptions={{
              style: {
                background: 'hsl(240 10% 6.9%)',
                border: '1px solid hsl(240 4% 16%)',
                color: 'hsl(0 0% 98%)',
              },
            }}
          />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
