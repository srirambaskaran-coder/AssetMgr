import React, { useState, useEffect } from 'react';
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
  Package,
  Filter,
  CheckCircle,
  Clock,
  User,
  Calendar,
  FileText
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetAllocations = () => {
  const [allocations, setAllocations] = useState([]);
  const [pendingAllocations, setPendingAllocations] = useState([]);
  const [availableAssets, setAvailableAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedRequisition, setSelectedRequisition] = useState(null);

  useEffect(() => {
    fetchAllocations();
    fetchPendingAllocations();
    fetchAvailableAssets();
  }, []);

  const fetchAllocations = async () => {
    try {
      const response = await axios.get(`${API}/asset-allocations`);
      setAllocations(response.data);
    } catch (error) {
      console.error('Error fetching allocations:', error);
      toast.error('Failed to load asset allocations');
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingAllocations = async () => {
    try {
      const response = await axios.get(`${API}/pending-allocations`);
      setPendingAllocations(response.data);
    } catch (error) {
      console.error('Error fetching pending allocations:', error);
    }
  };

  const fetchAvailableAssets = async () => {
    try {
      const response = await axios.get(`${API}/asset-definitions`);
      setAvailableAssets(response.data.filter(asset => asset.status === 'Available'));
    } catch (error) {
      console.error('Error fetching available assets:', error);
    }
  };

  const handleCreateAllocation = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-allocations`, formData);
      setAllocations([response.data, ...allocations]);
      setIsCreateModalOpen(false);
      setSelectedRequisition(null);
      
      // Refresh pending allocations and available assets
      await fetchPendingAllocations();
      await fetchAvailableAssets();
      
      toast.success('Asset allocated successfully');
    } catch (error) {
      console.error('Error creating allocation:', error);
      toast.error(error.response?.data?.detail || 'Failed to allocate asset');
    }
  };

  const filteredAllocations = allocations.filter(allocation => {
    const matchesSearch = allocation.asset_definition_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         allocation.requested_for_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         allocation.asset_type_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || allocation.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadgeColor = (status) => {
    const colors = {
      'Allocated to Employee': 'bg-green-100 text-green-800',
      'Received from Employee': 'bg-blue-100 text-blue-800',
      'Not Received from Employee': 'bg-red-100 text-red-800',
      'Damaged': 'bg-yellow-100 text-yellow-800',
      'Lost': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold text-gray-900">Asset Allocations</h1>
          <p className="text-gray-600 mt-1">Manage asset allocations and track employee assignments</p>
        </div>

        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="mr-2 h-4 w-4" />
              Allocate Asset
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Allocate Asset to Employee</DialogTitle>
            </DialogHeader>
            <AllocationForm 
              pendingAllocations={pendingAllocations}
              availableAssets={availableAssets}
              onSubmit={handleCreateAllocation}
              selectedRequisition={selectedRequisition}
              setSelectedRequisition={setSelectedRequisition}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Allocations</p>
                <p className="text-2xl font-bold text-gray-900">{allocations.length}</p>
              </div>
              <Package className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Allocations</p>
                <p className="text-2xl font-bold text-orange-600">{pendingAllocations.length}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Allocations</p>
                <p className="text-2xl font-bold text-green-600">
                  {allocations.filter(a => a.status === 'Allocated to Employee').length}
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
                <p className="text-sm text-gray-600">Available Assets</p>
                <p className="text-2xl font-bold text-purple-600">{availableAssets.length}</p>
              </div>
              <Package className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Allocations Section */}
      {pendingAllocations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="mr-2 h-5 w-5 text-orange-600" />
              Pending Allocations ({pendingAllocations.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingAllocations.slice(0, 5).map((requisition) => (
                <div key={requisition.id} className="flex items-center justify-between p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <div>
                        <p className="font-medium text-gray-900">{requisition.asset_type_name}</p>
                        <p className="text-sm text-gray-600">Requested by: {requisition.requested_by_name}</p>
                      </div>
                      <Badge className="bg-orange-100 text-orange-800">
                        {requisition.status}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedRequisition(requisition);
                      setIsCreateModalOpen(true);
                    }}
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    Allocate Asset
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by asset code, employee name, or asset type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Allocated to Employee">Allocated to Employee</SelectItem>
                  <SelectItem value="Received from Employee">Received from Employee</SelectItem>
                  <SelectItem value="Not Received from Employee">Not Received</SelectItem>
                  <SelectItem value="Damaged">Damaged</SelectItem>
                  <SelectItem value="Lost">Lost</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Allocations Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <Package className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>Asset Allocations ({filteredAllocations.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {filteredAllocations.length === 0 ? (
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No allocations found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Start by allocating assets to approved requisitions.'
                }
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset Code</TableHead>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Allocated To</TableHead>
                    <TableHead>Approved By</TableHead>
                    <TableHead>Allocated Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Reference ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAllocations.map((allocation) => (
                    <TableRow key={allocation.id}>
                      <TableCell className="font-medium">{allocation.asset_definition_code}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {allocation.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-1 text-gray-500" />
                          {allocation.requested_for_name}
                        </div>
                      </TableCell>
                      <TableCell>{allocation.approved_by_name}</TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 mr-1 text-gray-500" />
                          {new Date(allocation.allocated_date).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeColor(allocation.status)}>
                          {allocation.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {allocation.reference_id && (
                          <div className="flex items-center">
                            <FileText className="h-4 w-4 mr-1 text-gray-500" />
                            {allocation.reference_id}
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const AllocationForm = ({ pendingAllocations, availableAssets, onSubmit, selectedRequisition, setSelectedRequisition }) => {
  const [formData, setFormData] = useState({
    requisition_id: selectedRequisition?.id || '',
    asset_definition_id: '',
    remarks: '',
    reference_id: '',
    document_id: '',
    dispatch_details: ''
  });
  const [loading, setLoading] = useState(false);

  // Update form when selected requisition changes
  useEffect(() => {
    if (selectedRequisition) {
      setFormData(prev => ({
        ...prev,
        requisition_id: selectedRequisition.id
      }));
    }
  }, [selectedRequisition]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSubmit(formData);
    setLoading(false);
    setFormData({
      requisition_id: '',
      asset_definition_id: '',
      remarks: '',
      reference_id: '',
      document_id: '',
      dispatch_details: ''
    });
  };

  const selectedReq = pendingAllocations.find(req => req.id === formData.requisition_id);
  const compatibleAssets = availableAssets.filter(asset => 
    selectedReq ? asset.asset_type_id === selectedReq.asset_type_id : true
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-h-96 overflow-y-auto">
      <div>
        <Label htmlFor="requisition_id">Select Requisition *</Label>
        <Select 
          value={formData.requisition_id} 
          onValueChange={(value) => {
            setFormData({ ...formData, requisition_id: value, asset_definition_id: '' });
            const req = pendingAllocations.find(r => r.id === value);
            setSelectedRequisition(req);
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select approved requisition" />
          </SelectTrigger>
          <SelectContent>
            {pendingAllocations.map(req => (
              <SelectItem key={req.id} value={req.id}>
                {req.asset_type_name} - {req.requested_by_name} ({req.status})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selectedReq && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Requisition Details</h4>
          <div className="text-sm text-blue-800">
            <p><strong>Asset Type:</strong> {selectedReq.asset_type_name}</p>
            <p><strong>Requested By:</strong> {selectedReq.requested_by_name}</p>
            <p><strong>Justification:</strong> {selectedReq.justification}</p>
            <p><strong>Status:</strong> {selectedReq.status}</p>
          </div>
        </div>
      )}

      <div>
        <Label htmlFor="asset_definition_id">Select Asset *</Label>
        <Select 
          value={formData.asset_definition_id} 
          onValueChange={(value) => setFormData({ ...formData, asset_definition_id: value })}
          disabled={!selectedReq}
        >
          <SelectTrigger>
            <SelectValue placeholder={selectedReq ? "Select available asset" : "Select requisition first"} />
          </SelectTrigger>
          <SelectContent>
            {compatibleAssets.map(asset => (
              <SelectItem key={asset.id} value={asset.id}>
                {asset.asset_code} - {asset.asset_description} (${asset.asset_value?.toLocaleString()})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="reference_id">Reference ID</Label>
          <Input
            id="reference_id"
            value={formData.reference_id}
            onChange={(e) => setFormData({ ...formData, reference_id: e.target.value })}
            placeholder="Enter reference ID"
          />
        </div>
        <div>
          <Label htmlFor="document_id">Document ID</Label>
          <Input
            id="document_id"
            value={formData.document_id}
            onChange={(e) => setFormData({ ...formData, document_id: e.target.value })}
            placeholder="Enter document ID"
          />
        </div>
      </div>

      <div>
        <Label htmlFor="dispatch_details">Dispatch Details</Label>
        <Textarea
          id="dispatch_details"
          value={formData.dispatch_details}
          onChange={(e) => setFormData({ ...formData, dispatch_details: e.target.value })}
          placeholder="Enter dispatch and delivery details"
          rows={2}
        />
      </div>

      <div>
        <Label htmlFor="remarks">Remarks</Label>
        <Textarea
          id="remarks"
          value={formData.remarks}
          onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
          placeholder="Enter any additional remarks"
          rows={2}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading || !formData.requisition_id || !formData.asset_definition_id} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Allocating...' : 'Allocate Asset'}
        </Button>
      </div>
    </form>
  );
};

export default AssetAllocations;