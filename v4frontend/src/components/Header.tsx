import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { Button } from './ui/button'
import { Bell, User, CreditCard, LogOut } from 'lucide-react'

export const Header: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="border-b bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-blue-600">HR Analytics</h1>
        </div>

        <div className="flex items-center space-x-4">
          {/* Credits Display */}
          <div className="flex items-center space-x-2 rounded-lg bg-gray-100 px-3 py-2">
            <CreditCard className="h-4 w-4" />
            <span className="text-sm font-medium">
              {user?.credits_balance || 0} Credits
            </span>
          </div>

          {/* Notifications */}
          <Button variant="ghost" size="icon">
            <Bell className="h-4 w-4" />
          </Button>

          {/* User Menu */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 rounded-lg bg-gray-100 px-3 py-2">
              <User className="h-4 w-4" />
              <span className="text-sm font-medium">{user?.username}</span>
              {user?.is_admin && (
                <span className="rounded bg-blue-600 px-2 py-1 text-xs text-white">
                  Admin
                </span>
              )}
            </div>
            
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}
