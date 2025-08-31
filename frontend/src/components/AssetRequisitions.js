import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { toast } from 'sonner';
import { 
  Plus, 
  Search, 
  ClipboardList,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetRequisitions = () => {
  const { user } = useAuth();
  const [requisitions, setRequisitions] = useState([]);
  const [assetTypes, setAssetTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    fetchRequisitions();
    fetchAssetTypes();
  }, []);

  const fetchRequisitions = async () => {
    try {
      const response = await axios.get(`${API}/asset-requisitions`);
      setRequisitions(response.data);
    } catch (error) {
      console.error('Error fetching requisitions:', error);
      toast.error('Failed to load asset requisitions');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssetTypes = async () => {
    try {
      const response = await axios.get(`${API}/asset-types`);
      setAssetTypes(response.data.filter(type => type.status === 'Active'));
    } catch (error) {
      console.error('Error fetching asset types:', error);
    }
  };

  const handleCreateRequisition = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-requisitions`, formData);
      setRequisitions([response.data, ...requisitions]);
      setIsCreateModalOpen(false);
      toast.success('Asset requisition submitted successfully');
    } catch (error) {
      console.error('Error creating requisition:', error);
      toast.error(error.response?.data?.detail || 'Failed to create requisition');
    }
  };

  const filteredRequisitions = requisitions.filter(req => {
    const matchesSearch = req.asset_type_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         req.justification?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         req.requested_by_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || req.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Pending':
        return <Clock className="h-4 w-4" />;
      case 'Manager Approved':
        return <CheckCircle className="h-4 w-4" />;
      case 'HR Approved':
        return <CheckCircle className="h-4 w-4" />;
      case 'Rejected':
        return <XCircle className="h-4 w-4" />;
      case 'Allocated':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getStatusBadgeColor = (status) => {
    const colors = {
      'Pending': 'bg-yellow-100 text-yellow-800',
      'Manager Approved': 'bg-blue-100 text-blue-800',
      'HR Approved': 'bg-green-100 text-green-800',
      'Rejected': 'bg-red-100 text-red-800',
      'Allocated': 'bg-emerald-100 text-emerald-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const canCreateRequisition = () => {
    return ['Employee', 'Manager'].includes(user?.role);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Asset Requisitions</h1>
          <p className="text-gray-600 mt-1">
            {user?.role === 'Employee' 
              ? 'Submit and track your asset requests'
              : 'Manage and approve asset requisition requests'
            }
          </p>
        </div>

        {canCreateRequisition() && (
          <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="mr-2 h-4 w-4" />
                Request Asset
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>New Asset Requisition</DialogTitle>
              </DialogHeader>
              <RequisitionForm 
                assetTypes={assetTypes}
                onSubmit={handleCreateRequisition} 
              />
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search requisitions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Pending">Pending</SelectItem>
                  <SelectItem value="Manager Approved">Manager Approved</SelectItem>
                  <SelectItem value="HR Approved">HR Approved</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                  <SelectItem value="Allocated">Allocated</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Requisitions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <ClipboardList className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>Asset Requisitions ({filteredRequisitions.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {filteredRequisitions.length === 0 ? (
            <div className="text-center py-12">
              <ClipboardList className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No requisitions found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.' 
                  : canCreateRequisition() 
                    ? 'Get started by requesting your first asset.'
                    : 'No asset requisitions have been submitted yet.'
                }
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Requested By</TableHead>
                    <TableHead>Justification</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Request Date</TableHead>
                    {user?.role !== 'Employee' && <TableHead>Actions</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRequisitions.map((requisition) => (
                    <TableRow key={requisition.id}>
                      <TableCell>
                        <Badge variant="outline">
                          {requisition.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">
                        {requisition.requested_by_name}
                      </TableCell>
                      <TableCell className="max-w-xs">
                        <div className="truncate" title={requisition.justification}>
                          {requisition.justification}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(requisition.status)}
                          <Badge className={getStatusBadgeColor(requisition.status)}>
                            {requisition.status}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        {new Date(requisition.created_at).toLocaleDateString()}
                      </TableCell>
                      {user?.role !== 'Employee' && (
                        <TableCell>
                          <div className="flex gap-2">
                            {requisition.status === 'Pending' && user?.role === 'Manager' && (
                              <>
                                <Button size="sm" variant="outline" className="text-green-600 hover:text-green-800">
                                  Approve
                                </Button>
                                <Button size="sm" variant="outline" className="text-red-600 hover:text-red-800">
                                  Reject
                                </Button>
                              </>
                            )}
                            {requisition.status === 'Manager Approved' && user?.role === 'HR Manager' && (
                              <>
                                <Button size="sm" variant="outline" className="text-green-600 hover:text-green-800">
                                  Approve
                                </Button>
                                <Button size="sm" variant="outline" className="text-red-600 hover:text-red-800">
                                  Reject
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Statistics Cards for Managers */}
      {['Manager', 'HR Manager', 'Administrator'].includes(user?.role) && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pending</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {requisitions.filter(r => r.status === 'Pending').length}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Manager Approved</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {requisitions.filter(r => r.status === 'Manager Approved').length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">HR Approved</p>
                  <p className="text-2xl font-bold text-green-600">
                    {requisitions.filter(r => r.status === 'HR Approved').length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Rejected</p>
                  <p className="text-2xl font-bold text-red-600">
                    {requisitions.filter(r => r.status === 'Rejected').length}
                  </p>
                </div>
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

const RequisitionForm = ({ assetTypes, onSubmit }) => {
  const [formData, setFormData] = useState({
    asset_type_id: '',
    justification: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSubmit(formData);
    setLoading(false);
    setFormData({ asset_type_id: '', justification: '' });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="asset_type_id">Asset Type *</Label>
        <Select 
          value={formData.asset_type_id} 
          onValueChange={(value) => setFormData({ ...formData, asset_type_id: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select asset type needed" />
          </SelectTrigger>
          <SelectContent>
            {assetTypes.map(type => (
              <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="justification">Business Justification *</Label>
        <Textarea
          id="justification"
          value={formData.justification}
          onChange={(e) => setFormData({ ...formData, justification: e.target.value })}
          placeholder="Please explain why you need this asset and how it will be used..."
          rows={4}
          required
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading || !formData.asset_type_id || !formData.justification} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Submitting...' : 'Submit Request'}
        </Button>
      </div>
    </form>
  );
};

export default AssetRequisitions;