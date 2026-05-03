import { Outlet, Route, Routes } from 'react-router-dom'
import { Header } from './components/layout/Header'
import { Footer } from './components/layout/Footer'
import { SellerLayout } from './components/layout/SellerLayout'
import { AdminLayout } from './components/layout/AdminLayout'
import { ProtectedRoute } from './components/auth/ProtectedRoute'

// Public pages
import { HomePage } from './pages/public/HomePage'
import { MerchantsPage } from './pages/public/MerchantsPage'
import { MerchantProfilePage } from './pages/public/MerchantProfilePage'
import { ProductsPage } from './pages/public/ProductsPage'
import { ProductDetailPage } from './pages/public/ProductDetailPage'
import { MapPage } from './pages/public/MapPage'
import { ReservationPage } from './pages/public/ReservationPage'
import { ReservationConfirmationPage } from './pages/public/ReservationConfirmationPage'
import { CustomerProfilePage } from './pages/public/CustomerProfilePage'
import { FavoritesPage } from './pages/public/FavoritesPage'

// Seller pages
import { SellerDashboard } from './pages/seller/SellerDashboard'
import { SellerReservationsPage } from './pages/seller/SellerReservationsPage'
import { SellerReservationDetailPage } from './pages/seller/SellerReservationDetailPage'
import { SellerProductsPage } from './pages/seller/SellerProductsPage'
import { SellerProductFormPage } from './pages/seller/SellerProductFormPage'
import { SellerProfilePage } from './pages/seller/SellerProfilePage'

// Admin pages
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { AdminMerchantsPage } from './pages/admin/AdminMerchantsPage'
import { AdminMerchantFormPage } from './pages/admin/AdminMerchantFormPage'
import { AdminCategoriesPage } from './pages/admin/AdminCategoriesPage'
import { AdminContentPage } from './pages/admin/AdminContentPage'

function PublicLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/haendler" element={<MerchantsPage />} />
        <Route path="/haendler/:slug" element={<MerchantProfilePage />} />
        <Route path="/produkte" element={<ProductsPage />} />
        <Route path="/produkte/:slug" element={<ProductDetailPage />} />
        <Route path="/karte" element={<MapPage />} />
        <Route path="/reservierung/:productId" element={<ReservationPage />} />
        <Route path="/reservierung/bestaetigung/:id" element={<ReservationConfirmationPage />} />
        <Route path="/profil" element={<CustomerProfilePage />} />
        <Route path="/favoriten" element={<FavoritesPage />} />
      </Route>

      {/* Seller routes */}
      <Route
        path="/seller"
        element={
          <ProtectedRoute role="merchant">
            <SellerLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<SellerDashboard />} />
        <Route path="reservierungen" element={<SellerReservationsPage />} />
        <Route path="reservierungen/:id" element={<SellerReservationDetailPage />} />
        <Route path="produkte" element={<SellerProductsPage />} />
        <Route path="produkte/neu" element={<SellerProductFormPage />} />
        <Route path="produkte/:id/bearbeiten" element={<SellerProductFormPage />} />
        <Route path="profil" element={<SellerProfilePage />} />
      </Route>

      {/* Admin routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute role="admin">
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="haendler" element={<AdminMerchantsPage />} />
        <Route path="haendler/neu" element={<AdminMerchantFormPage />} />
        <Route path="haendler/:id/bearbeiten" element={<AdminMerchantFormPage />} />
        <Route path="kategorien" element={<AdminCategoriesPage />} />
        <Route path="inhalte" element={<AdminContentPage />} />
      </Route>
    </Routes>
  )
}
