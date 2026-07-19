import { lazy, ReactNode } from 'react'
import { Navigate, Route } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { CrawlProvider } from '@/contexts/CrawlContext'
import Navbar from '@/components/layout/Navbar'
import Sidebar from '@/components/layout/Sidebar'

// User-facing pages
const Home = lazy(() => import('@/pages/user/Home'))
const SearchPage = lazy(() => import('@/pages/user/Search'))
const ListingDetail = lazy(() => import('@/pages/user/ListingDetail'))
const NeighborhoodsPage = lazy(() => import('@/pages/user/Neighborhoods'))
const ChatPage = lazy(() => import('@/pages/user/Chat'))
const Login = lazy(() => import('@/pages/user/Login'))
const Profile = lazy(() => import('@/pages/user/Profile'))
const Favorites = lazy(() => import('@/pages/user/Favorites'))
const Alerts = lazy(() => import('@/pages/user/Alerts'))

// Admin pages
const AdminLogin = lazy(() => import('@/pages/admin/AdminLogin'))
const AdminDashboard = lazy(() => import('@/pages/admin/Dashboard'))
const AdminListings = lazy(() => import('@/pages/admin/Listings'))
const AdminPending = lazy(() => import('@/pages/admin/Pending'))
const AdminSources = lazy(() => import('@/pages/admin/Sources'))
const AdminNeighborhoods = lazy(() => import('@/pages/admin/Neighborhoods'))
const AdminJobs = lazy(() => import('@/pages/admin/Jobs'))

function UserShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="pt-20">{children}</div>
    </div>
  )
}

function AdminShell({ children }: { children: ReactNode }) {
  return (
    <CrawlProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 min-w-0 pt-20 px-4 pb-6 md:px-6 lg:p-10 md:ml-64 lg:pt-10">{children}</main>
      </div>
    </CrawlProvider>
  )
}

function Protected({ children }: { children: ReactNode }) {
  const { user, isAdmin, loading } = useAuth()
  if (loading) return null
  if (!isAdmin) return <Navigate to="/admin/login" replace />
  return <AdminShell>{children}</AdminShell>
}

export const userRoutes = (
  <>
    <Route path="/" element={<UserShell><Home /></UserShell>} />
    <Route path="/recherche" element={<UserShell><SearchPage /></UserShell>} />
    <Route path="/annonces/:id" element={<UserShell><ListingDetail /></UserShell>} />
    <Route path="/quartiers" element={<UserShell><NeighborhoodsPage /></UserShell>} />
    <Route path="/chat" element={<UserShell><ChatPage /></UserShell>} />
    <Route path="/login" element={<UserShell><Login /></UserShell>} />
    <Route path="/profil" element={<UserShell><Profile /></UserShell>} />
    <Route path="/favoris" element={<UserShell><Favorites /></UserShell>} />
    <Route path="/alertes" element={<UserShell><Alerts /></UserShell>} />
  </>
)

export function adminRoutes() {
  return (
    <>
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin" element={<Protected><AdminDashboard /></Protected>} />
      <Route path="/admin/annonces" element={<Protected><AdminListings /></Protected>} />
      <Route path="/admin/file-attente" element={<Protected><AdminPending /></Protected>} />
      <Route path="/admin/sources" element={<Protected><AdminSources /></Protected>} />
      <Route path="/admin/quartiers" element={<Protected><AdminNeighborhoods /></Protected>} />
      <Route path="/admin/jobs" element={<Protected><AdminJobs /></Protected>} />
    </>
  )
}