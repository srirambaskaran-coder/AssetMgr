import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  Package, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Users,
  TrendingUp,
  Activity,
  DollarSign,
  Target,
  BarChart3
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Handle both old single role structure and new multi-role structure
  const userRoles = user?.roles || (user?.role ? [user.role] : ['Employee']);
  const primaryRole = userRoles[0] || 'Employee';
  
  // Determine which dashboard to show based on role hierarchy
  const getEffectiveRole = () => {
    if (userRoles.includes('Administrator')) return 'Administrator';
    if (userRoles.includes('Asset Manager')) return 'Asset Manager';
    if (userRoles.includes('HR Manager')) return 'HR Manager';
    if (userRoles.includes('Manager')) return 'Manager';
    return 'Employee';
  };
  
  const effectiveRole = getEffectiveRole();

  useEffect(() => {
    fetchDashboardStats();
  }, [effectiveRole]);

  const fetchDashboardStats = async () => {
    try {
      let endpoint = `${API}/dashboard/stats`;
      if (effectiveRole === 'Asset Manager') {
        endpoint = `${API}/dashboard/asset-manager-stats`;
      }
      const response = await axios.get(endpoint);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      toast.error('Failed to load dashboard statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    let greeting = 'Good morning';
    if (hour >= 12 && hour < 18) greeting = 'Good afternoon';
    if (hour >= 18) greeting = 'Good evening';
    
    return `${greeting}, ${user?.name?.split(' ')[0]}!`;
  };

  const getRoleDashboard = () => {
    switch (user?.role) {
      case 'Administrator':
        return <AdminDashboard stats={stats} />;
      case 'HR Manager':
        return <HRManagerDashboard stats={stats} />;
      case 'Manager':
        return <ManagerDashboard stats={stats} />;
      case 'Employee':
        return <EmployeeDashboard stats={stats} />;
      case 'Asset Manager':
        return <AssetManagerDashboard stats={stats} />;
      default:
        return <div>Unknown role</div>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{getWelcomeMessage()}</h1>
            <p className="text-blue-100 mt-1">
              Welcome to your Asset Management Dashboard
            </p>
          </div>
          <div className="text-right">
            <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
              {user?.role}
            </Badge>
            <p className="text-sm text-blue-100 mt-1">
              {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Role-specific Dashboard */}
      {getRoleDashboard()}
    </div>
  );
};

const AdminDashboard = ({ stats }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <StatCard
      title="Total Asset Types"
      value={stats.total_asset_types || 0}
      icon={Package}
      color="text-blue-600"
      bgColor="bg-blue-100"
    />
    <StatCard
      title="Total Assets"
      value={stats.total_assets || 0}
      icon={FileText}
      color="text-green-600"
      bgColor="bg-green-100"
    />
    <StatCard
      title="Available Assets"
      value={stats.available_assets || 0}
      icon={CheckCircle}
      color="text-emerald-600"
      bgColor="bg-emerald-100"
    />
    <StatCard
      title="Pending Requisitions"
      value={stats.pending_requisitions || 0}
      icon={Clock}
      color="text-yellow-600"
      bgColor="bg-yellow-100"
    />
  </div>
);

const HRManagerDashboard = ({ stats }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <StatCard
      title="Total Assets"
      value={stats.total_assets || 0}
      icon={FileText}
      color="text-blue-600"
      bgColor="bg-blue-100"
    />
    <StatCard
      title="Available Assets"
      value={stats.available_assets || 0}
      icon={CheckCircle}
      color="text-green-600"
      bgColor="bg-green-100"
    />
    <StatCard
      title="Allocated Assets"
      value={stats.allocated_assets || 0}
      icon={Users}
      color="text-purple-600"
      bgColor="bg-purple-100"
    />
    <StatCard
      title="Pending Requisitions"
      value={stats.pending_requisitions || 0}
      icon={AlertTriangle}
      color="text-orange-600"
      bgColor="bg-orange-100"
    />
  </div>
);

const ManagerDashboard = ({ stats }) => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
    <StatCard
      title="Available Assets"
      value={stats.available_assets || 0}
      icon={CheckCircle}
      color="text-green-600"
      bgColor="bg-green-100"
    />
    <StatCard
      title="Pending Approvals"
      value={stats.pending_approvals || 0}
      icon={Clock}
      color="text-yellow-600"
      bgColor="bg-yellow-100"
    />
    <StatCard
      title="Total Assets"
      value={stats.total_assets || 0}
      icon={TrendingUp}
      color="text-blue-600"
      bgColor="bg-blue-100"
    />
  </div>
);

const EmployeeDashboard = ({ stats }) => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
    <StatCard
      title="My Requisitions"
      value={stats.my_requisitions || 0}
      icon={FileText}
      color="text-blue-600"
      bgColor="bg-blue-100"
    />
    <StatCard
      title="My Allocated Assets"
      value={stats.my_allocated_assets || 0}
      icon={Package}
      color="text-green-600"
      bgColor="bg-green-100"
    />
    <StatCard
      title="Available Assets"
      value={stats.available_assets || 0}
      icon={Activity}
      color="text-purple-600"
      bgColor="bg-purple-100"
    />
  </div>
);

const AssetManagerDashboard = ({ stats }) => (
  <div className="space-y-6">
    {/* Primary Stats */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Assets"
        value={stats.total_assets || 0}
        icon={Package}
        color="text-blue-600"
        bgColor="bg-blue-100"
      />
      <StatCard
        title="Allocated Assets"
        value={stats.allocated_assets || 0}
        icon={Users}
        color="text-green-600"
        bgColor="bg-green-100"
      />
      <StatCard
        title="Available Assets"
        value={stats.available_assets || 0}
        icon={CheckCircle}
        color="text-emerald-600"
        bgColor="bg-emerald-100"
      />
      <StatCard
        title="Pending Allocations"
        value={stats.pending_allocations || 0}
        icon={Clock}
        color="text-orange-600"
        bgColor="bg-orange-100"
      />
    </div>

    {/* Asset Health & Recovery Stats */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Damaged Assets"
        value={stats.damaged_assets || 0}
        icon={AlertTriangle}
        color="text-red-600"
        bgColor="bg-red-100"
      />
      <StatCard
        title="Lost Assets"
        value={stats.lost_assets || 0}
        icon={AlertTriangle}
        color="text-gray-600"
        bgColor="bg-gray-100"
      />
      <StatCard
        title="Under Repair"
        value={stats.under_repair || 0}
        icon={Activity}
        color="text-yellow-600"
        bgColor="bg-yellow-100"
      />
      <StatCard
        title="Pending Retrievals"
        value={stats.pending_retrievals || 0}
        icon={Package}
        color="text-purple-600"
        bgColor="bg-purple-100"
      />
    </div>

    {/* Key Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Allocation Rate</p>
            <p className="text-3xl font-bold text-blue-600">{stats.allocation_rate || 0}%</p>
            <p className="text-sm text-gray-500">of total assets allocated</p>
          </div>
          <Target className="h-12 w-12 text-blue-600" />
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Availability Rate</p>
            <p className="text-3xl font-bold text-green-600">{stats.availability_rate || 0}%</p>
            <p className="text-sm text-gray-500">of assets available</p>
          </div>
          <BarChart3 className="h-12 w-12 text-green-600" />
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Recovery Rate</p>
            <p className="text-3xl font-bold text-purple-600">
              {stats.completed_retrievals && stats.pending_retrievals + stats.completed_retrievals > 0
                ? Math.round((stats.completed_retrievals / (stats.pending_retrievals + stats.completed_retrievals)) * 100)
                : 0}%
            </p>
            <p className="text-sm text-gray-500">assets successfully recovered</p>
          </div>
          <TrendingUp className="h-12 w-12 text-purple-600" />
        </div>
      </Card>
    </div>

    {/* Asset Type Breakdown */}
    {stats.asset_type_breakdown && stats.asset_type_breakdown.length > 0 && (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Type Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.asset_type_breakdown.map((type, index) => (
            <div key={index} className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900">{type._id}</h4>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Total:</span>
                  <span className="font-medium">{type.total}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-600">Available:</span>
                  <span className="font-medium">{type.available}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-blue-600">Allocated:</span>
                  <span className="font-medium">{type.allocated}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    )}
  </div>
);

const StatCard = ({ title, value, icon: Icon, color, bgColor }) => (
  <Card className="hover:shadow-lg transition-shadow duration-200">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${bgColor}`}>
          <Icon className={`h-6 w-6 ${color}`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

export default Dashboard;