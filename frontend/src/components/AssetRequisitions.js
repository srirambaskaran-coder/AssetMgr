import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { useRole } from '../contexts/RoleContext';
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
import { toast } from 'sonner';
import { 
  Plus, 
  Search, 
  ClipboardList,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ArrowRight,
  User,
  Calendar
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetRequisitions = () => {
  const { user } = useAuth();
  const { activeRole, accessibleRoles } = useRole();
  const [requisitions, setRequisitions] = useState([]);
  const [assetTypes, setAssetTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

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

  const handleWithdrawRequisition = async (requisitionId) => {
    if (!window.confirm('Are you sure you want to withdraw this asset request? This action cannot be undone.')) {
      return;
    }

    try {
      await axios.delete(`${API}/asset-requisitions/${requisitionId}`);
      await fetchRequisitions();
      toast.success('Asset requisition withdrawn successfully');
    } catch (error) {
      console.error('Error withdrawing requisition:', error);
      toast.error(error.response?.data?.detail || 'Failed to withdraw requisition');
    }
  };

  const handleManagerAction = async (requisitionId, action) => {
    const actionMessages = {
      approve: 'Are you sure you want to approve this asset request?',
      reject: 'Are you sure you want to reject this asset request?',
      hold: 'Are you sure you want to put this asset request on hold?'
    };

    const reason = window.prompt(`${actionMessages[action]}\n\nPlease provide a reason:`);
    if (!reason || reason.trim() === '') {
      toast.error('Reason is required for this action');
      return;
    }

    try {
      await axios.post(`${API}/asset-requisitions/${requisitionId}/manager-action`, {
        action,
        reason: reason.trim()
      });
      await fetchRequisitions();
      toast.success(`Asset requisition ${action}d successfully`);
    } catch (error) {
      console.error(`Error ${action}ing requisition:`, error);
      toast.error(error.response?.data?.detail || `Failed to ${action} requisition`);
    }
  };

  const handleHRAction = async (requisitionId, action) => {
    const actionMessages = {
      approve: 'Are you sure you want to approve this asset request?',
      reject: 'Are you sure you want to reject this asset request?',
      hold: 'Are you sure you want to put this asset request on hold?'
    };

    const reason = window.prompt(`${actionMessages[action]}\n\nPlease provide a reason:`);
    if (!reason || reason.trim() === '') {
      toast.error('Reason is required for this action');
      return;
    }

    try {
      await axios.post(`${API}/asset-requisitions/${requisitionId}/hr-action`, {
        action,
        reason: reason.trim()
      });
      await fetchRequisitions();
      toast.success(`Asset requisition ${action}d successfully`);
    } catch (error) {
      console.error(`Error ${action}ing requisition:`, error);
      toast.error(error.response?.data?.detail || `Failed to ${action} requisition`);
    }
  };

  const filteredRequisitions = requisitions.filter(req => {
    const matchesSearch = req.asset_type_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         req.justification?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         req.requested_by_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || req.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Pagination logic
  const totalItems = filteredRequisitions.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedRequisitions = filteredRequisitions.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter]);

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

  const canCreateRequisition = () => {
    return accessibleRoles.includes('Employee') || accessibleRoles.includes('Manager');
  };

  const canManageRequisitions = () => {
    return accessibleRoles.includes('Manager') || accessibleRoles.includes('HR Manager') || 
           accessibleRoles.includes('Administrator') || accessibleRoles.includes('Asset Manager');
  };

  const hasRole = (roleName) => {
    return accessibleRoles.includes(roleName);
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
            {canCreateRequisition()
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
            <DialogContent className="max-w-2xl">
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
                  <SelectItem value="Assigned for Allocation">Assigned for Allocation</SelectItem>
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
                    <TableHead>Requisition ID</TableHead>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Request Type</TableHead>
                    <TableHead>Request For</TableHead>
                    <TableHead>Requested By</TableHead>
                    <TableHead>Required By</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Assigned To</TableHead>
                    <TableHead>Request Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedRequisitions.map((requisition) => (
                    <TableRow key={requisition.id}>
                      <TableCell className="font-medium">
                        <div className="text-xs text-gray-500">
                          {requisition.id.substring(0, 8)}...
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {requisition.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={requisition.request_type === 'New Allocation' ? 'default' : 'secondary'}
                          className={
                            requisition.request_type === 'New Allocation' ? 'bg-blue-100 text-blue-800' :
                            requisition.request_type === 'Replacement' ? 'bg-orange-100 text-orange-800' :
                            'bg-purple-100 text-purple-800'
                          }
                        >
                          {requisition.request_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-1 text-gray-500" />
                          {requisition.request_for === 'Team Member' 
                            ? requisition.team_member_name || 'Team Member' 
                            : 'Self'
                          }
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        {requisition.requested_by_name}
                      </TableCell>
                      <TableCell>
                        {requisition.required_by_date && (
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1 text-gray-500" />
                            {new Date(requisition.required_by_date).toLocaleDateString()}
                          </div>
                        )}
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
                      <TableCell>
                        {new Date(requisition.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {/* Employee withdraw option for their own pending requests */}
                          {canCreateRequisition() && 
                           requisition.requested_by === user?.id && 
                           requisition.status === 'Pending' && (
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-red-600 hover:text-red-800"
                              onClick={() => handleWithdrawRequisition(requisition.id)}
                            >
                              <XCircle className="h-3 w-3 mr-1" />
                              Withdraw
                            </Button>
                          )}
                          
                          {/* Manager approval options */}
                          {requisition.status === 'Pending' && hasRole('Manager') && (
                            <>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-green-600 hover:text-green-800"
                                onClick={() => handleManagerAction(requisition.id, 'approve')}
                              >
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Approve
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-red-600 hover:text-red-800"
                                onClick={() => handleManagerAction(requisition.id, 'reject')}
                              >
                                <XCircle className="h-3 w-3 mr-1" />
                                Reject
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-yellow-600 hover:text-yellow-800"
                                onClick={() => handleManagerAction(requisition.id, 'hold')}
                              >
                                <Clock className="h-3 w-3 mr-1" />
                                Hold
                              </Button>
                            </>
                          )}
                          
                          {/* HR Manager approval options */}
                          {(requisition.status === 'Manager Approved' || requisition.status === 'On Hold') && hasRole('HR Manager') && (
                            <>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-green-600 hover:text-green-800"
                                onClick={() => handleHRAction(requisition.id, 'approve')}
                              >
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Approve
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-red-600 hover:text-red-800"
                                onClick={() => handleHRAction(requisition.id, 'reject')}
                              >
                                <XCircle className="h-3 w-3 mr-1" />
                                Reject
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-yellow-600 hover:text-yellow-800"
                                onClick={() => handleHRAction(requisition.id, 'hold')}
                              >
                                <Clock className="h-3 w-3 mr-1" />
                                Hold
                              </Button>
                            </>
                          )}
                          
                          {/* Show no actions if none apply */}
                          {!canCreateRequisition() && !canManageRequisitions() && (
                            <span className="text-gray-400 text-sm">No actions available</span>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <DataPagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            itemsPerPage={itemsPerPage}
            onPageChange={handlePageChange}
          />
        )}
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
    request_type: 'New Allocation',
    reason_for_return_replacement: '',
    asset_details: '',
    request_for: 'Self',
    team_member_employee_id: '',
    justification: '',
    required_by_date: ''
  });
  const [loading, setLoading] = useState(false);
  const [teamMembers, setTeamMembers] = useState([]);

  // Fetch team members when request_for changes to Team Member
  useEffect(() => {
    if (formData.request_for === 'Team Member') {
      fetchTeamMembers();
    }
  }, [formData.request_for]);

  const fetchTeamMembers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      // Filter out current user and only show employees/managers
      setTeamMembers(response.data.filter(user => 
        user.role === 'Employee' || user.role === 'Manager'
      ));
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const submitData = {
      ...formData,
      required_by_date: formData.required_by_date ? new Date(formData.required_by_date).toISOString() : null
    };
    
    await onSubmit(submitData);
    setLoading(false);
    setFormData({
      asset_type_id: '',
      request_type: 'New Allocation',
      reason_for_return_replacement: '',
      asset_details: '',
      request_for: 'Self',
      team_member_employee_id: '',
      justification: '',
      required_by_date: ''
    });
  };

  const isConditionalFieldRequired = () => {
    return formData.request_type === 'Replacement' || formData.request_type === 'Return';
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-h-96 overflow-y-auto">
      <div className="grid grid-cols-2 gap-4">
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
          <Label htmlFor="request_type">Request Type *</Label>
          <Select 
            value={formData.request_type} 
            onValueChange={(value) => setFormData({ 
              ...formData, 
              request_type: value,
              reason_for_return_replacement: '',
              asset_details: ''
            })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select request type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="New Allocation">New Allocation</SelectItem>
              <SelectItem value="Replacement">Replacement</SelectItem>
              <SelectItem value="Return">Return</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isConditionalFieldRequired() && (
        <>
          <div>
            <Label htmlFor="reason_for_return_replacement">
              Reason for {formData.request_type} *
            </Label>
            <Textarea
              id="reason_for_return_replacement"
              value={formData.reason_for_return_replacement}
              onChange={(e) => setFormData({ ...formData, reason_for_return_replacement: e.target.value })}
              placeholder={`Please explain why you need a ${formData.request_type.toLowerCase()}...`}
              rows={3}
              required={isConditionalFieldRequired()}
            />
          </div>
          
          <div>
            <Label htmlFor="asset_details">Asset Details *</Label>
            <Textarea
              id="asset_details"
              value={formData.asset_details}
              onChange={(e) => setFormData({ ...formData, asset_details: e.target.value })}
              placeholder="Provide details about the current asset (model, serial number, condition, etc.)"
              rows={2}
              required={isConditionalFieldRequired()}
            />
          </div>
        </>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="request_for">Request For *</Label>
          <Select 
            value={formData.request_for} 
            onValueChange={(value) => setFormData({ 
              ...formData, 
              request_for: value,
              team_member_employee_id: ''
            })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select who this request is for" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Self">Self</SelectItem>
              <SelectItem value="Team Member">Team Member</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        {formData.request_for === 'Team Member' && (
          <div>
            <Label htmlFor="team_member_employee_id">Team Member *</Label>
            <Select 
              value={formData.team_member_employee_id} 
              onValueChange={(value) => setFormData({ ...formData, team_member_employee_id: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select team member" />
              </SelectTrigger>
              <SelectContent>
                {teamMembers.map(member => (
                  <SelectItem key={member.id} value={member.id}>
                    {member.name} ({member.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      <div>
        <Label htmlFor="required_by_date">Required By Date</Label>
        <Input
          id="required_by_date"
          type="date"
          value={formData.required_by_date}
          onChange={(e) => setFormData({ ...formData, required_by_date: e.target.value })}
          min={new Date().toISOString().split('T')[0]} // Prevent past dates
        />
      </div>

      <div>
        <Label htmlFor="justification">Business Justification / Remarks *</Label>
        <Textarea
          id="justification"
          value={formData.justification}
          onChange={(e) => setFormData({ ...formData, justification: e.target.value })}
          placeholder="Please explain the business need and how this asset will be used..."
          rows={4}
          required
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button 
          type="submit" 
          disabled={
            loading || 
            !formData.asset_type_id || 
            !formData.justification ||
            (formData.request_for === 'Team Member' && !formData.team_member_employee_id) ||
            (isConditionalFieldRequired() && (!formData.reason_for_return_replacement || !formData.asset_details))
          } 
          className="bg-blue-600 hover:bg-blue-700"
        >
          {loading ? 'Submitting...' : 'Submit Request'}
        </Button>
      </div>
    </form>
  );
};

export default AssetRequisitions;