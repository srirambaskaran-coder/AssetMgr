import React, { useState } from 'react';
import { useAuth } from '../App';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from './ui/dropdown-menu';
import { 
  Building2, 
  LayoutDashboard, 
  Package, 
  FileText, 
  ClipboardList,
  LogOut,
  User,
  ChevronDown,
  Settings,
  Building,
  Menu,
  X
} from 'lucide-react';

const Navigation = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      roles: ['Administrator', 'HR Manager', 'Employee', 'Manager']
    },
    {
      name: 'Asset Types',
      href: '/asset-types',
      icon: Package,
      roles: ['Administrator', 'HR Manager']
    },
    {
      name: 'Asset Definitions',
      href: '/asset-definitions',
      icon: FileText,
      roles: ['Administrator', 'HR Manager']
    },
    {
      name: 'Asset Requisitions',
      href: '/asset-requisitions',
      icon: ClipboardList,
      roles: ['Administrator', 'HR Manager', 'Employee', 'Manager']
    },
    {
      name: 'User Management',
      href: '/users',
      icon: User,
      roles: ['Administrator']
    },
    {
      name: 'Bulk Import',
      href: '/bulk-import',
      icon: FileText,
      roles: ['Administrator', 'HR Manager']
    }
  ];

  const filteredNavItems = navigationItems.filter(item => 
    item.roles.includes(user?.role)
  );

  const isActivePage = (href) => location.pathname === href;

  const getRoleColor = (role) => {
    const roleColors = {
      'Administrator': 'text-purple-600 bg-purple-100',
      'HR Manager': 'text-blue-600 bg-blue-100',
      'Manager': 'text-green-600 bg-green-100',
      'Employee': 'text-gray-600 bg-gray-100'
    };
    return roleColors[role] || 'text-gray-600 bg-gray-100';
  };

  return (
    <>
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Building2 className="h-6 w-6 text-white" />
              </div>
              <div>
                <span className="text-lg font-bold text-gray-900">AssetFlow</span>
                <div className="text-xs text-gray-500">Inventory Management</div>
              </div>
            </Link>
            
            {/* Mobile close button */}
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors w-full ${
                    isActivePage(item.href)
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="mr-3 h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User Profile Section */}
          <div className="border-t border-gray-200 p-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center space-x-3 p-2 w-full justify-start hover:bg-gray-100">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback className="bg-blue-600 text-white text-sm">
                      {user?.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <div className="text-sm font-medium text-gray-900 truncate">{user?.name}</div>
                    <div className={`text-xs px-2 py-1 rounded-full inline-block mt-1 ${getRoleColor(user?.role)}`}>
                      {user?.role}
                    </div>
                  </div>
                  <ChevronDown className="h-4 w-4 text-gray-500" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-3 py-2">
                  <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                  <p className="text-sm text-gray-500">{user?.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/dashboard" className="flex items-center cursor-pointer">
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                {user?.role === 'Administrator' && (
                  <>
                    <DropdownMenuItem asChild>
                      <Link to="/settings" className="flex items-center cursor-pointer">
                        <Settings className="mr-2 h-4 w-4" />
                        Settings
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/company-profile" className="flex items-center cursor-pointer">
                        <Building className="mr-2 h-4 w-4" />
                        Company Profile
                      </Link>
                    </DropdownMenuItem>
                  </>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={logout}
                  className="text-red-600 cursor-pointer"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Top bar for mobile */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 lg:hidden">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <Link to="/dashboard" className="flex items-center space-x-2">
            <div className="p-1 bg-blue-600 rounded">
              <Building2 className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">AssetFlow</span>
          </Link>
          
          <div className="w-8" /> {/* Spacer for centering */}
        </div>
      </div>
    </>
  );
};

export default Navigation;