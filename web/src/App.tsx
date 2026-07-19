import { Suspense } from 'react'
import { Routes } from 'react-router-dom'
import PrismBackground from '@/components/ui/PrismBackground'
import { useAuth } from '@/contexts/AuthContext'
import { userRoutes, adminRoutes } from '@/routes'

function FullScreenLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="spinner" />
    </div>
  )
}

export default function App() {
  const { loading } = useAuth()
  if (loading) return <FullScreenLoader />
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <PrismBackground />
      <div className="relative z-10">
        <Suspense fallback={<FullScreenLoader />}>
          <Routes>
            {userRoutes}
            {adminRoutes()}
          </Routes>
        </Suspense>
      </div>
    </div>
  )
}