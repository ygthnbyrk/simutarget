import { Routes, Route, Navigate } from 'react-router-dom'
import ScrollToTop from './components/ScrollToTop'
import useAuthStore from './stores/authStore'

// Pages
import Landing from './pages/Landing'
import Pricing from './pages/Pricing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import CampaignTest from './pages/CampaignTest'
import ABCompare from './pages/ABCompare'
import MultiCompare from './pages/MultiCompare'
import History from './pages/History'
import Profile from './pages/Profile'

// Legal & Info Pages
import AboutUs from './pages/AboutUs'
import Contact from './pages/Contact'
import FAQs from './pages/FAQs'
import TermsConditions from './pages/TermsConditions'
import PrivacyPolicy from './pages/PrivacyPolicy'
import CookiePolicy from './pages/CookiePolicy'
import RefundPolicy from './pages/RefundPolicy'
import Partner from './pages/Partner'

// Protected Route Component
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

// Public Route (redirect if logged in)
function PublicOnlyRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route 
        path="/login" 
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        } 
      />
      <Route 
        path="/register" 
        element={
          <PublicOnlyRoute>
            <Register />
          </PublicOnlyRoute>
        } 
      />

      {/* Legal & Info Pages */}
      <Route path="/about" element={<AboutUs />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/faqs" element={<FAQs />} />
      <Route path="/terms" element={<TermsConditions />} />
      <Route path="/privacy" element={<PrivacyPolicy />} />
      <Route path="/cookies" element={<CookiePolicy />} />
      <Route path="/refund" element={<RefundPolicy />} />
      <Route path="/partner" element={<Partner />} />

      {/* Protected Dashboard Routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route 
        path="/dashboard/test" 
        element={
          <ProtectedRoute>
            <CampaignTest />
          </ProtectedRoute>
        }
      />
      <Route 
        path="/dashboard/ab" 
        element={
          <ProtectedRoute>
            <ABCompare />
          </ProtectedRoute>
        }
      />
      <Route 
        path="/dashboard/multi" 
        element={
          <ProtectedRoute>
            <MultiCompare />
          </ProtectedRoute>
        }
      />
      <Route 
        path="/dashboard/history" 
        element={
          <ProtectedRoute>
            <History />
          </ProtectedRoute>
        }
      />
      <Route 
        path="/dashboard/profile" 
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App