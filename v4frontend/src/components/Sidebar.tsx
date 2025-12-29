import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { cn } from '../utils'
import {
  Upload,
  FileText,
  BarChart3,
  Clock,
  Users,
  Settings,
  Home,
  CreditCard
} from 'lucide-react'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  adminOnly?: boolean
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Upload Resume', href: '/upload', icon: Upload },
  { name: 'Resumes', href: '/resumes', icon: FileText },
  { name: 'Queue', href: '/queue', icon: Clock },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Credits', href: '/credits', icon: CreditCard },
  { name: 'Admin Users', href: '/admin/users', icon: Users, adminOnly: true },
  { name: 'Admin Settings', href: '/admin/settings', icon: Settings, adminOnly: true },
]

export const Sidebar: React.FC = () => {
  const { user } = useAuthStore()

  const filteredNavigation = navigation.filter(
    item => !item.adminOnly || user?.is_admin
  )

  return (
    <div className="w-64 border-r bg-white">
      <nav className="space-y-2 p-4">
        {filteredNavigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
