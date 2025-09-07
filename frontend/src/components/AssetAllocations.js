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
import { DataPagination } from './ui/data-pagination';
import ExportButton from './ui/export-button';
import { toast } from 'sonner';
import { 
  Plus, 
  Search, 
  Filter,
  IndianRupee,
  Package,
  User,
  Calendar
} from 'lucide-react';
import { useAuth } from '../App';
import { useRole } from '../contexts/RoleContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetAllocations = () => {
  const { user } = useAuth();
  const { activeRole } = useRole();
  const [allocations, setAllocations] = useState([]);
  const [pendingRequisitions, setPendingRequisitions] = useState([]);
  const [assetTypes, setAssetTypes] = useState([]);
  const [assetDefinitions, setAssetDefinitions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    asset_type_id: '',
    asset_definition_id: '',
    request_type: 'New Request',
    requested_for: '',
    remarks: '',
    dispatch_details: '',
    requisition_id: null
  });
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchAssetAllocations();
    fetchPendingRequisitions();
    fetchAssetTypes();
    fetchAssetDefinitions();
    fetchUsers();
  }, []);

  const fetchAssetAllocations = async () => {
    try {
      const response = await axios.get(`${API}/asset-allocations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setAllocations(response.data);
    } catch (error) {
      console.error('Error fetching asset allocations:', error);
      toast.error('Failed to load asset allocations');
    }
  };

  const fetchPendingRequisitions = async () => {
    try {
      const response = await axios.get(`${API}/asset-requisitions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      
      // Filter requisitions assigned to current user (Asset Manager) for allocation
      const assignedRequisitions = response.data.filter(req => 
        req.status === 'Assigned for Allocation' && 
        req.assigned_to === user?.id
      );
      
      setPendingRequisitions(assignedRequisitions);
    } catch (error) {
      console.error('Error fetching pending requisitions:', error);
      toast.error('Failed to load pending requisitions');
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

  const fetchAssetDefinitions = async () => {
    try {
      const response = await axios.get(`${API}/asset-definitions`);
      setAssetDefinitions(response.data.filter(def => def.status === 'Available'));
    } catch (error) {
      console.error('Error fetching asset definitions:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setUsers(response.data.filter(user => user.is_active));
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleCreateAllocation = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-allocations`, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setAllocations([...allocations, response.data]);
      setIsCreateModalOpen(false);
      toast.success('Asset allocation created successfully');
      
      // Reset form data
      setFormData({
        asset_type_id: '',
        asset_definition_id: '',
        request_type: 'New Request',
        requested_for: '',
        remarks: '',
        dispatch_details: '',
        requisition_id: null
      });
      
      // Refresh asset definitions to update availability
      fetchAssetDefinitions();
      
      // If this was from a pending requisition, refresh the pending requisitions
      if (formData.requisition_id) {
        fetchPendingRequisitions();
      }
    } catch (error) {
      console.error('Error creating asset allocation:', error);
      toast.error(error.response?.data?.detail || 'Failed to create asset allocation');
    }
  };

  const handleAllocateFromRequisition = (requisition) => {
    // Pre-populate the allocation form with requisition data
    setFormData({
      asset_type_id: requisition.asset_type_id,
      asset_definition_id: '', // This will be selected by the Asset Manager
      request_type: requisition.request_type,
      requested_for: requisition.requested_for,
      remarks: `Allocated from requisition ${requisition.id}`,
      dispatch_details: '',
      requisition_id: requisition.id // Add this to link the allocation to the requisition
    });
    setIsCreateModalOpen(true);
  };

  // Filter allocations based on search term and filters
  const filteredAllocations = allocations.filter(allocation => {
    const matchesSearch = 
      allocation.asset_definition_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      allocation.asset_type_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      allocation.requested_for_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      allocation.allocated_by_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || allocation.status === statusFilter;
    const matchesType = typeFilter === 'all' || allocation.asset_type_id === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // Pagination logic
  const totalItems = filteredAllocations.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedAllocations = filteredAllocations.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, typeFilter]);

  const getStatusBadgeColor = (status) => {
    const colors = {
      'Allocated to Employee': 'bg-green-100 text-green-800',
      'Ready for Collection': 'bg-blue-100 text-blue-800',
      'Collected': 'bg-emerald-100 text-emerald-800',
      'Returned': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Check if current user can create allocations
  const canCreateAllocation = () => {
    const accessibleRoles = user?.roles || [];
    return accessibleRoles.includes('Asset Manager') || accessibleRoles.includes('Administrator');
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
          <p className="text-gray-600 mt-1">Manage asset allocation and distribution to employees</p>
        </div>
        
        <div className="flex items-center gap-2">
          <ExportButton 
            data={filteredAllocations}
            type="assetAllocations"
            disabled={loading}
          />

          {canCreateAllocation() && (
            <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="mr-2 h-4 w-4" />
                  Allocate Asset
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Asset Allocation</DialogTitle>
                </DialogHeader>
                <AssetAllocationForm 
                  assetTypes={assetTypes}
                  assetDefinitions={assetDefinitions}
                  users={users}
                  onSubmit={handleCreateAllocation}
                  initialData={formData}
                  onClose={() => {
                    setIsCreateModalOpen(false);
                    setFormData({
                      asset_type_id: '',
                      asset_definition_id: '',
                      request_type: 'New Request',
                      requested_for: '',
                      remarks: '',
                      dispatch_details: '',
                      requisition_id: null
                    });
                  }}
                />
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search allocations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {assetTypes.map(type => (
                    <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Allocated to Employee">Allocated</SelectItem>
                  <SelectItem value="Ready for Collection">Ready for Collection</SelectItem>
                  <SelectItem value="Collected">Collected</SelectItem>
                  <SelectItem value="Returned">Returned</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pending Requisitions for Allocation */}
      {pendingRequisitions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-orange-700">
              Pending Requisitions for Allocation ({pendingRequisitions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Requisition ID</TableHead>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Request Type</TableHead>
                    <TableHead>Requested For</TableHead>
                    <TableHead>Requested By</TableHead>
                    <TableHead>Required By</TableHead>
                    <TableHead>Approved By</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pendingRequisitions.map((requisition) => (
                    <TableRow key={requisition.id} className="bg-orange-50">
                      <TableCell className="font-medium">
                        {requisition.id}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {requisition.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell>{requisition.request_type}</TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <User className="h-4 w-4 text-gray-400 mr-2" />
                          {requisition.requested_for_name}
                        </div>
                      </TableCell>
                      <TableCell>{requisition.requested_by_name}</TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                          {requisition.required_by_date ? 
                            new Date(requisition.required_by_date).toLocaleDateString() : 
                            '-'
                          }
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <User className="h-4 w-4 text-gray-400 mr-2" />
                          {requisition.manager_action_by_name || requisition.hr_action_by_name || '-'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button 
                          size="sm" 
                          className="bg-blue-600 hover:bg-blue-700"
                          onClick={() => handleAllocateFromRequisition(requisition)}
                        >
                          Allocate
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Asset Allocations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Completed Allocations ({filteredAllocations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredAllocations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No allocations found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' || typeFilter !== 'all' 
                  ? 'Try adjusting your search or filters.' 
                  : 'Get started by creating a new asset allocation.'
                }
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset Code</TableHead>
                      <TableHead>Asset Type</TableHead>
                      <TableHead>Request Type</TableHead>
                      <TableHead>Allocated To</TableHead>
                      <TableHead>Allocated By</TableHead>
                      <TableHead>Allocation Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Remarks</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedAllocations.map((allocation) => (
                      <TableRow key={allocation.id}>
                        <TableCell className="font-medium">
                          {allocation.asset_definition_code}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {allocation.asset_type_name}
                          </Badge>
                        </TableCell>
                        <TableCell>{allocation.request_type}</TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <User className="h-4 w-4 text-gray-400 mr-2" />
                            {allocation.requested_for_name}
                          </div>
                        </TableCell>
                        <TableCell>{allocation.allocated_by_name}</TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                            {new Date(allocation.allocated_date).toLocaleDateString()}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadgeColor(allocation.status)}>
                            {allocation.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {allocation.remarks || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <DataPagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={totalItems}
                itemsPerPage={itemsPerPage}
                onPageChange={handlePageChange}
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Asset Allocation Form Component
const AssetAllocationForm = ({ assetTypes, assetDefinitions, users, onSubmit, initialData, onClose }) => {
  const [formData, setFormData] = useState({
    asset_definition_id: initialData?.asset_definition_id || '',
    allocated_date: new Date().toISOString().split('T')[0], // Default to today
    dispatch_details: initialData?.dispatch_details || '',
    reference_id: '',
    remarks: initialData?.remarks || '',
    // Read-only fields from requisition
    requisition_id: initialData?.requisition_id || null,
    request_type: initialData?.request_type || '',
    asset_type_id: initialData?.asset_type_id || '',
    requested_for: initialData?.requested_for || '',
    approved_by: initialData?.manager_action_by_name || initialData?.hr_action_by_name || ''
  });
  const [loading, setLoading] = useState(false);
  const [filteredAssetDefinitions, setFilteredAssetDefinitions] = useState([]);
  const [selectedAssetDetails, setSelectedAssetDetails] = useState(null);

  // Update form data when initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData(prev => ({
        ...prev,
        asset_definition_id: initialData.asset_definition_id || '',
        dispatch_details: initialData.dispatch_details || '',
        remarks: initialData.remarks || '',
        requisition_id: initialData.requisition_id || null,
        request_type: initialData.request_type || '',
        asset_type_id: initialData.asset_type_id || '',
        requested_for: initialData.requested_for || '',
        approved_by: initialData.manager_action_by_name || initialData.hr_action_by_name || ''
      }));
    }
  }, [initialData]);

  // Filter asset definitions based on selected asset type
  useEffect(() => {
    if (formData.asset_type_id) {
      const filtered = assetDefinitions.filter(def => 
        def.asset_type_id === formData.asset_type_id && 
        def.status === 'Available'
      );
      setFilteredAssetDefinitions(filtered);
    } else {
      setFilteredAssetDefinitions([]);
    }
  }, [formData.asset_type_id, assetDefinitions]);

  // Update asset details when asset definition is selected
  useEffect(() => {
    if (formData.asset_definition_id) {
      const selectedAsset = assetDefinitions.find(def => def.id === formData.asset_definition_id);
      setSelectedAssetDetails(selectedAsset);
    } else {
      setSelectedAssetDetails(null);
    }
  }, [formData.asset_definition_id, assetDefinitions]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Prepare submission data with only editable fields
    const submissionData = {
      asset_definition_id: formData.asset_definition_id,
      allocated_date: formData.allocated_date,
      dispatch_details: formData.dispatch_details,
      reference_id: formData.reference_id,
      remarks: formData.remarks,
      // Include read-only fields for backend processing
      requisition_id: formData.requisition_id,
      request_type: formData.request_type,
      requested_for: formData.requested_for
    };
    
    await onSubmit(submissionData);
    setLoading(false);
  };

  // Get requested employee name
  const requestedEmployee = users.find(user => user.id === formData.requested_for);
  
  // Get asset type name
  const assetType = assetTypes.find(type => type.id === formData.asset_type_id);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Read-only Fields Section */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Requisition Details (Read-only)</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-gray-600">Requisition ID</Label>
            <Input 
              value={formData.requisition_id || 'System Generated'} 
              disabled 
              className="bg-gray-100 text-gray-700"
            />
          </div>
          <div>
            <Label className="text-gray-600">Request Type</Label>
            <Input 
              value={formData.request_type} 
              disabled 
              className="bg-gray-100 text-gray-700"
            />
          </div>
          <div>
            <Label className="text-gray-600">Asset Type</Label>
            <Input 
              value={assetType?.name || 'Unknown'} 
              disabled 
              className="bg-gray-100 text-gray-700"
            />
          </div>
          <div>
            <Label className="text-gray-600">Requested For (Employee)</Label>
            <Input 
              value={requestedEmployee ? `${requestedEmployee.name} (${requestedEmployee.email})` : 'Unknown Employee'} 
              disabled 
              className="bg-gray-100 text-gray-700"
            />
          </div>
          <div className="col-span-2">
            <Label className="text-gray-600">Approved By</Label>
            <Input 
              value={formData.approved_by || 'Not Available'} 
              disabled 
              className="bg-gray-100 text-gray-700"
            />
          </div>
        </div>
      </div>

      {/* Asset Details Section (Read-only) */}
      {selectedAssetDetails && (
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-sm font-semibold text-blue-900 mb-3">Asset Details (Read-only)</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-blue-700">Asset Code</Label>
              <Input 
                value={selectedAssetDetails.asset_code} 
                disabled 
                className="bg-blue-100 text-blue-900"
              />
            </div>
            <div>
              <Label className="text-blue-700">Asset Description</Label>
              <Input 
                value={selectedAssetDetails.asset_description} 
                disabled 
                className="bg-blue-100 text-blue-900"
              />
            </div>
            <div>
              <Label className="text-blue-700">Brand</Label>
              <Input 
                value={selectedAssetDetails.brand || 'N/A'} 
                disabled 
                className="bg-blue-100 text-blue-900"
              />
            </div>
            <div>
              <Label className="text-blue-700">Model</Label>
              <Input 
                value={selectedAssetDetails.model || 'N/A'} 
                disabled 
                className="bg-blue-100 text-blue-900"
              />
            </div>
          </div>
        </div>
      )}

      {/* Editable Fields Section */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="text-sm font-semibold text-green-900 mb-3">Asset Manager Input Fields</h3>
        <div className="space-y-4">
          <div>
            <Label htmlFor="asset_definition_id" className="text-green-800">Asset Definition ID *</Label>
            <Select 
              value={formData.asset_definition_id} 
              onValueChange={(value) => setFormData({ ...formData, asset_definition_id: value })}
            >
              <SelectTrigger className="bg-white">
                <SelectValue placeholder={
                  filteredAssetDefinitions.length === 0 
                    ? "No available assets for this type" 
                    : "Select asset to allocate"
                } />
              </SelectTrigger>
              <SelectContent>
                {filteredAssetDefinitions.map(asset => (
                  <SelectItem key={asset.id} value={asset.id}>
                    {asset.asset_code} - {asset.asset_description}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="allocated_date" className="text-green-800">Allocated Date *</Label>
            <Input
              id="allocated_date"
              type="date"
              value={formData.allocated_date}
              onChange={(e) => setFormData({ ...formData, allocated_date: e.target.value })}
              className="bg-white"
              required
            />
          </div>

          <div>
            <Label htmlFor="dispatch_details" className="text-green-800">Dispatch Details</Label>
            <Textarea
              id="dispatch_details"
              value={formData.dispatch_details}
              onChange={(e) => setFormData({ ...formData, dispatch_details: e.target.value })}
              placeholder="Enter dispatch or delivery details"
              rows={2}
              className="bg-white"
            />
          </div>

          <div>
            <Label htmlFor="reference_id" className="text-green-800">Reference ID</Label>
            <Input
              id="reference_id"
              value={formData.reference_id}
              onChange={(e) => setFormData({ ...formData, reference_id: e.target.value })}
              placeholder="Enter reference ID (invoice, delivery note, etc.)"
              className="bg-white"
            />
          </div>

          <div>
            <Label htmlFor="remarks" className="text-green-800">Remarks</Label>
            <Textarea
              id="remarks"
              value={formData.remarks}
              onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
              placeholder="Enter any additional remarks"
              rows={3}
              className="bg-white"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button 
          type="submit" 
          disabled={loading || !formData.asset_definition_id} 
          className="bg-blue-600 hover:bg-blue-700"
        >
          {loading ? 'Allocating...' : 'Allocate Asset'}
        </Button>
      </div>
    </form>
  );
};

export default AssetAllocations;