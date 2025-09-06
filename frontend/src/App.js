import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import { Toaster, toast } from 'sonner';

// Components
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import AssetTypes from './components/AssetTypes';
import AssetDefinitions from './components/AssetDefinitions';
import AssetRequisitions from './components/AssetRequisitions';
import AssetAllocations from './components/AssetAllocations';
import AssetRetrievals from './components/AssetRetrievals';
import MyAssets from './components/MyAssets';
import UserManagement from './components/UserManagement';
import LocationManagement from './components/LocationManagement';
import NDCRequests from './components/NDCRequests';
import BulkImport from './components/BulkImport';
import Settings from './components/Settings';
import CompanyProfile from './components/CompanyProfile';
import Navigation from './components/Navigation';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { RoleProvider } from './contexts/RoleContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionToken, setSessionToken] = useState(localStorage.getItem('session_token'));

  // Set axios default headers
  useEffect(() => {
    if (sessionToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${sessionToken}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [sessionToken]);

  // Check for session token on app load
  useEffect(() => {
    const checkAuth = async () => {
      if (sessionToken) {
        try {
          const response = await axios.get(`${API}/auth/me`);
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('session_token');
          setSessionToken(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [sessionToken]);

  // Handle Emergent Auth callback
  useEffect(() => {
    const handleAuthCallback = async () => {
      const hash = window.location.hash;
      if (hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1];
        try {
          const response = await axios.post(`${API}/auth/emergent-callback?session_id=${sessionId}`);
          if (response.data.success) {
            const token = response.data.session_token;
            localStorage.setItem('session_token', token);
            setSessionToken(token);
            setUser(response.data.user);
            toast.success('Successfully logged in!');
            // Clear the hash from URL
            window.location.hash = '';
            window.location.pathname = '/dashboard';
          }
        } catch (error) {
          console.error('Auth callback failed:', error);
          toast.error('Authentication failed');
        }
      }
    };

    handleAuthCallback();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      if (response.data.success) {
        const token = response.data.session_token;
        localStorage.setItem('session_token', token);
        setSessionToken(token);
        setUser(response.data.user);
        toast.success('Successfully logged in!');
        return true;
      }
    } catch (error) {
      console.error('Login failed:', error);
      toast.error('Login failed. Please check your credentials.');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('session_token');
    setSessionToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    toast.success('Successfully logged out!');
  };

  const emergentLogin = () => {
    const redirectUrl = encodeURIComponent(window.location.origin + '/profile');
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        emergentLogin,
        loading,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, requiredRoles = [] }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Handle both old single role structure and new multi-role structure
  const userRoles = user?.roles || (user?.role ? [user.role] : ['Employee']);
  const hasRequiredRole = requiredRoles.length === 0 || requiredRoles.some(role => userRoles.includes(role));
  
  if (!hasRequiredRole) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="text-center text-red-600">Access Denied</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-600 mb-4">
              You don't have permission to access this page.
            </p>
            <p className="text-sm text-gray-500">
              Required roles: {requiredRoles.join(', ')}
            </p>
            <p className="text-sm text-gray-500">
              Your roles: {userRoles.join(', ')}
            </p>
            <Button 
              onClick={() => window.history.back()} 
              className="mt-4"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return children;
};

// Main App Layout
const AppLayout = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();

  if (location.pathname === '/login') {
    return children;
  }

  return (
    <RoleProvider>
      <div className="min-h-screen bg-gray-50 flex">
        <Navigation />
        <main className="flex-1 lg:ml-0">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </RoleProvider>
  );
};

// Home redirect component
const Home = () => {
  const { user } = useAuth();
  
  useEffect(() => {
    if (user) {
      window.location.pathname = '/dashboard';
    }
  }, [user]);

  return <Navigate to="/login" replace />;
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <AppLayout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/profile" element={<Navigate to="/dashboard" replace />} />
              
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/asset-types" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator', 'HR Manager']}>
                    <AssetTypes />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/asset-definitions" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator', 'HR Manager']}>
                    <AssetDefinitions />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/asset-requisitions" 
                element={
                  <ProtectedRoute>
                    <AssetRequisitions />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/asset-allocations" 
                element={
                  <ProtectedRoute requiredRoles={['Asset Manager', 'Administrator']}>
                    <AssetAllocations />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/asset-retrievals" 
                element={
                  <ProtectedRoute requiredRoles={['Asset Manager', 'Administrator', 'Manager']}>
                    <AssetRetrievals />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/my-assets" 
                element={
                  <ProtectedRoute requiredRoles={['Employee', 'Manager', 'HR Manager', 'Administrator']}>
                    <MyAssets />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/users" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator']}>
                    <UserManagement />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/locations" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator']}>
                    <LocationManagement />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/ndc-requests" 
                element={
                  <ProtectedRoute requiredRoles={['HR Manager', 'Asset Manager', 'Administrator']}>
                    <NDCRequests />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/bulk-import" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator', 'HR Manager']}>
                    <BulkImport />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/settings" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator']}>
                    <Settings />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/company-profile" 
                element={
                  <ProtectedRoute requiredRoles={['Administrator']}>
                    <CompanyProfile />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </AppLayout>
        </BrowserRouter>
        <Toaster position="top-right" />
      </AuthProvider>
    </div>
  );
}

export default App;