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
  ClipboardList,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ArrowRight,
  User,
  Calendar
} from 'lucide-react';
import { useAuth } from '../App';
import { useRole } from '../contexts/RoleContext';
import TableHeaderSortable from './ui/table-header-sortable';
import AdvancedFilters from './ui/advanced-filters';
import EnhancedPagination from './ui/enhanced-pagination';
import useTableControls from '../hooks/useTableControls';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Helper function to extract readable error messages from FastAPI validation errors
const getErrorMessage = (error) => {
  if (!error.response?.data?.detail) {
    return 'An unexpected error occurred';
  }
  
  const detail = error.response.data.detail;
  
  // If detail is a string, return it directly
  if (typeof detail === 'string') {
    return detail;
  }
  
  // If detail is an array of validation errors, format them
  if (Array.isArray(detail)) {
    return detail.map(err => {
      if (err.msg && err.loc) {
        const field = err.loc[err.loc.length - 1]; // Get the field name
        return `${field}: ${err.msg}`;
      }
      return err.msg || err.toString();
    }).join(', ');
  }
  
  // Fallback for other object types
  return detail.message || detail.toString() || 'Validation error occurred';
};

const AssetRequisitions = () => {
  const { user } = useAuth();
  const { activeRole } = useRole();
  const [assetRequisitions, setAssetRequisitions] = useState([]);
  const [assetTypes, setAssetTypes] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isManagerActionModalOpen, setIsManagerActionModalOpen] = useState(false);
  const [isHRActionModalOpen, setIsHRActionModalOpen] = useState(false);
  const [selectedRequisition, setSelectedRequisition] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchAssetRequisitions();
    fetchAssetTypes();
    fetchUsers();
  }, []);

  const fetchAssetRequisitions = async () => {
    try {
      const response = await axios.get(`${API}/asset-requisitions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setAssetRequisitions(response.data);
    } catch (error) {
      console.error('Error fetching asset requisitions:', error);
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

  const handleCreateAssetRequisition = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-requisitions`, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setAssetRequisitions([...assetRequisitions, response.data]);
      setIsCreateModalOpen(false);
      toast.success('Asset requisition created successfully');
    } catch (error) {
      console.error('Error creating asset requisition:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const handleManagerAction = async (requisitionId, action, reason) => {
    try {
      await axios.post(`${API}/asset-requisitions/${requisitionId}/manager-action`, {
        action,
        reason
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      
      fetchAssetRequisitions(); // Refresh data
      setIsManagerActionModalOpen(false);
      setSelectedRequisition(null);
      toast.success(`Requisition ${action}d successfully`);
    } catch (error) {
      console.error('Error processing manager action:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const handleHRAction = async (requisitionId, action, reason) => {
    try {
      await axios.post(`${API}/asset-requisitions/${requisitionId}/hr-action`, {
        action,
        reason
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      
      fetchAssetRequisitions(); // Refresh data
      setIsHRActionModalOpen(false);
      setSelectedRequisition(null);
      toast.success(`Requisition ${action}d successfully`);
    } catch (error) {
      console.error('Error processing HR action:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const withdrawRequisition = async (requisitionId) => {
    try {
      await axios.post(`${API}/asset-requisitions/${requisitionId}/withdraw`, {}, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      
      fetchAssetRequisitions(); // Refresh data
      toast.success('Requisition withdrawn successfully');
    } catch (error) {
      console.error('Error withdrawing requisition:', error);
      toast.error(getErrorMessage(error));
    }
  };

  // Enhanced table controls
  const tableControls = useTableControls(assetRequisitions, {
    initialItemsPerPage: 10,
    searchFields: ['id', 'asset_type_name', 'requested_for_name', 'requested_by_name'],
    sortableFields: {
      id: { sortFn: (a, b, direction) => direction === 'asc' ? a.localeCompare(b) : b.localeCompare(a) },
      asset_type_name: { sortFn: (a, b, direction) => direction === 'asc' ? a.localeCompare(b) : b.localeCompare(a) },
      request_type: { sortFn: (a, b, direction) => direction === 'asc' ? a.localeCompare(b) : b.localeCompare(a) },
      status: { sortFn: (a, b, direction) => direction === 'asc' ? a.localeCompare(b) : b.localeCompare(a) },
      created_at: { sortFn: (a, b, direction) => {
        const dateA = new Date(a);
        const dateB = new Date(b);
        return direction === 'asc' ? dateA - dateB : dateB - dateA;
      }},
      required_by_date: { sortFn: (a, b, direction) => {
        const dateA = new Date(a);
        const dateB = new Date(b);
        return direction === 'asc' ? dateA - dateB : dateB - dateA;
      }}
    }
  });

  // Update filters from legacy state to new format
  useEffect(() => {
    const newFilters = {};
    if (statusFilter && statusFilter !== 'all') {
      newFilters.status = statusFilter;
    }
    if (typeFilter && typeFilter !== 'all') {
      newFilters.asset_type_id = typeFilter;
    }
    
    // Update table controls filters
    Object.keys(newFilters).forEach(key => {
      if (tableControls.filters[key] !== newFilters[key]) {
        tableControls.handleFilterChange(key, newFilters[key]);
      }
    });
  }, [statusFilter, typeFilter]);

  // Sync legacy search with new controls
  useEffect(() => {
    if (tableControls.searchTerm !== searchTerm) {
      tableControls.handleSearchChange(searchTerm);
    }
  }, [searchTerm]);

  // Define filters for the advanced filter component
  const filters = [
    {
      key: 'asset_type_id',
      label: 'Asset Type',
      placeholder: 'Filter by type',
      width: 'w-[180px]',
      value: typeFilter,
      defaultValue: 'all',
      options: [
        { value: 'all', label: 'All Types' },
        ...assetTypes.map(type => ({
          value: type.id,
          label: type.name
        }))
      ]
    },
    {
      key: 'status',
      label: 'Status',
      placeholder: 'Filter by status',
      width: 'w-[200px]',
      value: statusFilter,
      defaultValue: 'all',
      options: [
        { value: 'all', label: 'All Status' },
        { value: 'Pending', label: 'Pending' },
        { value: 'Manager Approved', label: 'Manager Approved' },
        { value: 'HR Approved', label: 'HR Approved' },
        { value: 'Rejected', label: 'Rejected' },
        { value: 'Assigned for Allocation', label: 'Assigned for Allocation' },
        { value: 'Allocated', label: 'Allocated' }
      ]
    }
  ];

  const dateFilters = [
    {
      key: 'created_at',
      label: 'Request Date From',
      placeholder: 'From date',
      value: tableControls.dateFilters.created_at || ''
    },
    {
      key: 'required_by_date',
      label: 'Required Date From',
      placeholder: 'Required from',
      value: tableControls.dateFilters.required_by_date || ''
    }
  ];

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
      case 'Assigned for Allocation':
        return <ArrowRight className="h-4 w-4" />;
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
      'Assigned for Allocation': 'bg-purple-100 text-purple-800',
      'Allocated': 'bg-emerald-100 text-emerald-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Check if current user can create requisitions
  const canCreateRequisition = () => {
    const accessibleRoles = user?.roles || [];
    return accessibleRoles.includes('Employee') || 
           accessibleRoles.includes('Manager') || 
           accessibleRoles.includes('HR Manager');
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
          <p className="text-gray-600 mt-1">Manage asset requests and approvals</p>
        </div>
        
        <div className="flex items-center gap-2">
          <ExportButton 
            data={tableControls.filteredData}
            type="assetRequisitions"
            disabled={loading}
          />

          {canCreateRequisition() && (
            <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Requisition
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Asset Requisition</DialogTitle>
                </DialogHeader>
                <AssetRequisitionForm 
                  assetTypes={assetTypes}
                  users={users}
                  onSubmit={handleCreateAssetRequisition} 
                />
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Enhanced Filters */}
      <AdvancedFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        filters={filters}
        onFilterChange={(key, value) => {
          if (key === 'status') setStatusFilter(value);
          if (key === 'asset_type_id') setTypeFilter(value);
        }}
        dateFilters={dateFilters}
        onDateFilterChange={tableControls.handleDateFilterChange}
        onClearFilters={() => {
          setSearchTerm('');
          setStatusFilter('all');
          setTypeFilter('all');
          tableControls.clearFilters();
        }}
        activeFiltersCount={
          (statusFilter !== 'all' ? 1 : 0) + 
          (typeFilter !== 'all' ? 1 : 0) + 
          Object.values(tableControls.dateFilters).filter(v => v).length
        }
      />

      {/* Asset Requisitions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Asset Requisitions ({tableControls.totalItems})</CardTitle>
        </CardHeader>
        <CardContent>
          {tableControls.totalItems === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <ClipboardList className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No requisitions found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' || typeFilter !== 'all' 
                  ? 'Try adjusting your search or filters.' 
                  : 'Get started by creating a new asset requisition.'
                }
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHeaderSortable
                        sortKey="id"
                        currentSort={tableControls.sortConfig}
                        onSort={tableControls.handleSort}
                      >
                        Requisition ID
                      </TableHeaderSortable>
                      <TableHeaderSortable
                        sortKey="asset_type_name"
                        currentSort={tableControls.sortConfig}
                        onSort={tableControls.handleSort}
                      >
                        Asset Type
                      </TableHeaderSortable>
                      <TableHeaderSortable
                        sortKey="request_type"
                        currentSort={tableControls.sortConfig}
                        onSort={tableControls.handleSort}
                      >
                        Request Type
                      </TableHeaderSortable>
                      <TableHead>Request For</TableHead>
                      <TableHead>Requested By</TableHead>
                      <TableHeaderSortable
                        sortKey="required_by_date"
                        currentSort={tableControls.sortConfig}
                        onSort={tableControls.handleSort}
                      >
                        Required By
                      </TableHeaderSortable>
                      <TableHeaderSortable
                        sortKey="status"
                        currentSort={tableControls.sortConfig}
                        onSort={tableControls.handleSort}
                      >
                        Status
                      </TableHeaderSortable>
                      <TableHead>Assigned To</TableHead>
                      <TableHeaderSortable
                        sortKey="created_at"
                        currentSort={tableControls.sortConfig}
                        onSort={tableControls.handleSort}
                      >
                        Request Date
                      </TableHeaderSortable>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tableControls.data.map((requisition) => (
                      <TableRow key={requisition.id}>
                        <TableCell className="font-medium">{requisition.id}</TableCell>
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
                            {new Date(requisition.required_by_date).toLocaleDateString()}
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
                          {requisition.assigned_to_name ? (
                            <div className="space-y-1">
                              <div className="font-medium text-sm">
                                {requisition.assigned_to_name}
                              </div>
                              {requisition.routing_reason && (
                                <div className="text-xs text-gray-500">
                                  {requisition.routing_reason}
                                </div>
                              )}
                              {requisition.assigned_date && (
                                <div className="text-xs text-gray-400">
                                  {new Date(requisition.assigned_date).toLocaleDateString()}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400 text-sm">Not assigned</span>
                          )}
                        </TableCell>
                        <TableCell>{new Date(requisition.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            {requisition.status === 'Pending' && activeRole === 'Manager' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedRequisition(requisition);
                                  setIsManagerActionModalOpen(true);
                                }}
                              >
                                Review
                              </Button>
                            )}

                            {requisition.status === 'Manager Approved' && activeRole === 'HR Manager' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedRequisition(requisition);
                                  setIsHRActionModalOpen(true);
                                }}
                              >
                                Review
                              </Button>
                            )}

                            {requisition.status === 'Pending' && 
                             (activeRole === 'Employee' || activeRole === 'Manager') && 
                             requisition.requested_by === user.id && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => withdrawRequisition(requisition.id)}
                                className="text-red-600 hover:text-red-800"
                              >
                                Withdraw
                              </Button>
                            )}
                          </div>
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

      {/* Manager Action Modal */}
      <Dialog open={isManagerActionModalOpen} onOpenChange={setIsManagerActionModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Manager Review</DialogTitle>
          </DialogHeader>
          {selectedRequisition && (
            <ManagerActionForm 
              requisition={selectedRequisition}
              onSubmit={handleManagerAction}
              onCancel={() => {
                setIsManagerActionModalOpen(false);
                setSelectedRequisition(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* HR Action Modal */}
      <Dialog open={isHRActionModalOpen} onOpenChange={setIsHRActionModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>HR Review</DialogTitle>
          </DialogHeader>
          {selectedRequisition && (
            <HRActionForm 
              requisition={selectedRequisition}
              onSubmit={handleHRAction}
              onCancel={() => {
                setIsHRActionModalOpen(false);
                setSelectedRequisition(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Asset Requisition Form Component
const AssetRequisitionForm = ({ assetTypes, users, onSubmit }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    asset_type_id: '',
    request_type: 'New Allocation',
    request_for: 'Self',
    team_member_employee_id: '',
    required_by_date: '',
    justification: '',
    reason_for_return_replacement: '',
    asset_details: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Prepare submit data - send exact values expected by backend
    const submitData = {
      asset_type_id: formData.asset_type_id,
      request_type: formData.request_type,
      request_for: formData.request_for,
      team_member_employee_id: formData.request_for === 'Team Member' ? formData.team_member_employee_id : null,
      required_by_date: formData.required_by_date,
      justification: formData.justification,
      reason_for_return_replacement: formData.reason_for_return_replacement || null,
      asset_details: formData.asset_details || null
    };
    
    await onSubmit(submitData);
    setLoading(false);
  };

  // Check if current request type requires additional fields
  const requiresAdditionalFields = formData.request_type === 'Return' || formData.request_type === 'Replacement';

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="asset_type_id">Asset Type *</Label>
        <Select 
          value={formData.asset_type_id} 
          onValueChange={(value) => setFormData({ ...formData, asset_type_id: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select asset type" />
          </SelectTrigger>
          <SelectContent>
            {assetTypes.map(type => (
              <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="request_type">Request Type</Label>
        <Select 
          value={formData.request_type} 
          onValueChange={(value) => setFormData({ ...formData, request_type: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select request type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="New Allocation">New Allocation</SelectItem>
            <SelectItem value="Replacement">Replacement</SelectItem>
            <SelectItem value="Upgrade">Upgrade</SelectItem>
            <SelectItem value="Return">Return</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="request_for">Requested For *</Label>
        <Select 
          value={formData.request_for} 
          onValueChange={(value) => setFormData({ ...formData, request_for: value, team_member_employee_id: '' })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select who this is for" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Self">Self</SelectItem>
            <SelectItem value="Team Member">Team Member</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Show user selection dropdown only when "Team Member" is selected */}
      {formData.request_for === 'Team Member' && (
        <div>
          <Label htmlFor="team_member_employee_id">Select Team Member *</Label>
          <Select 
            value={formData.team_member_employee_id} 
            onValueChange={(value) => setFormData({ ...formData, team_member_employee_id: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select team member" />
            </SelectTrigger>
            <SelectContent>
              {users.filter(u => u.id !== user?.id).map(teamUser => (
                <SelectItem key={teamUser.id} value={teamUser.id}>
                  {teamUser.name} ({teamUser.email})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Conditional fields for Return/Replacement */}
      {requiresAdditionalFields && (
        <>
          <div>
            <Label htmlFor="reason_for_return_replacement">
              Reason for {formData.request_type} *
            </Label>
            <Textarea
              id="reason_for_return_replacement"
              value={formData.reason_for_return_replacement}
              onChange={(e) => setFormData({ ...formData, reason_for_return_replacement: e.target.value })}
              placeholder={`Enter reason for ${formData.request_type.toLowerCase()}`}
              rows={3}
              required
            />
          </div>

          <div>
            <Label htmlFor="asset_details">Asset Details *</Label>
            <Textarea
              id="asset_details"
              value={formData.asset_details}
              onChange={(e) => setFormData({ ...formData, asset_details: e.target.value })}
              placeholder="Enter details of the asset (Asset Code, Serial Number, Current Condition, etc.)"
              rows={3}
              required
            />
          </div>
        </>
      )}

      <div>
        <Label htmlFor="required_by_date">Required By Date *</Label>
        <Input
          id="required_by_date"
          type="date"
          value={formData.required_by_date}
          onChange={(e) => setFormData({ ...formData, required_by_date: e.target.value })}
          required
        />
      </div>

      <div>
        <Label htmlFor="justification">Justification</Label>
        <Textarea
          id="justification"
          value={formData.justification}
          onChange={(e) => setFormData({ ...formData, justification: e.target.value })}
          placeholder="Enter justification for the asset request"
          rows={3}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Creating...' : 'Create Requisition'}
        </Button>
      </div>
    </form>
  );
};

// Manager Action Form Component
const ManagerActionForm = ({ requisition, onSubmit, onCancel }) => {
  const [action, setAction] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!action) return;
    
    setLoading(true);
    await onSubmit(requisition.id, action, reason);
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <h4 className="font-medium">Requisition Details</h4>
        <div className="text-sm text-gray-600">
          <p><strong>Asset Type:</strong> {requisition.asset_type_name}</p>
          <p><strong>Requested For:</strong> {requisition.requested_for_name}</p>
          <p><strong>Required By:</strong> {new Date(requisition.required_by_date).toLocaleDateString()}</p>
        </div>
      </div>

      <div>
        <Label htmlFor="action">Action *</Label>
        <Select value={action} onValueChange={setAction}>
          <SelectTrigger>
            <SelectValue placeholder="Select action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="approve">Approve</SelectItem>
            <SelectItem value="reject">Reject</SelectItem>
            <SelectItem value="hold">Hold</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="reason">Reason</Label>
        <Textarea
          id="reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter reason for your decision"
          rows={3}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading || !action} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Processing...' : 'Submit'}
        </Button>
      </div>
    </form>
  );
};

// HR Action Form Component  
const HRActionForm = ({ requisition, onSubmit, onCancel }) => {
  const [action, setAction] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!action) return;
    
    setLoading(true);
    await onSubmit(requisition.id, action, reason);
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <h4 className="font-medium">Requisition Details</h4>
        <div className="text-sm text-gray-600">
          <p><strong>Asset Type:</strong> {requisition.asset_type_name}</p>
          <p><strong>Requested For:</strong> {requisition.requested_for_name}</p>
          <p><strong>Manager Status:</strong> {requisition.status}</p>
        </div>
      </div>

      <div>
        <Label htmlFor="action">Action *</Label>
        <Select value={action} onValueChange={setAction}>
          <SelectTrigger>
            <SelectValue placeholder="Select action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="approve">Approve</SelectItem>
            <SelectItem value="reject">Reject</SelectItem>
            <SelectItem value="hold">Hold</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="reason">Reason</Label>
        <Textarea
          id="reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter reason for your decision"
          rows={3}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading || !action} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Processing...' : 'Submit'}
        </Button>
      </div>
    </form>
  );
};

export default AssetRequisitions;