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
  FileText,
  User,
  Calendar,
  Eye,
  XCircle
} from 'lucide-react';
import { useAuth } from '../App';
import { useRole } from '../contexts/RoleContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NDCRequests = () => {
  const { user } = useAuth();
  const { activeRole } = useRole();
  const [ndcRequests, setNdcRequests] = useState([]);
  const [separationReasons, setSeparationReasons] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isAddReasonModalOpen, setIsAddReasonModalOpen] = useState(false);
  const [isAssetsModalOpen, setIsAssetsModalOpen] = useState(false);
  const [selectedNDC, setSelectedNDC] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchNDCRequests();
    fetchSeparationReasons();
    fetchEmployees();
    fetchManagers();
  }, []);

  const fetchNDCRequests = async () => {
    try {
      const response = await axios.get(`${API}/ndc-requests`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setNdcRequests(response.data);
    } catch (error) {
      console.error('Error fetching NDC requests:', error);
      toast.error('Failed to load NDC requests');
    } finally {
      setLoading(false);
    }
  };

  const fetchSeparationReasons = async () => {
    try {
      const response = await axios.get(`${API}/separation-reasons`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setSeparationReasons(response.data);
    } catch (error) {
      console.error('Error fetching separation reasons:', error);
    }
  };

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      // Filter for employees only
      const employeeUsers = response.data.filter(user => 
        user.is_active && user.roles && user.roles.includes('Employee')
      );
      setEmployees(employeeUsers);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const fetchManagers = async () => {
    try {
      const response = await axios.get(`${API}/users/managers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setManagers(response.data);
    } catch (error) {
      console.error('Error fetching managers:', error);
    }
  };

  const handleCreateNDCRequest = async (formData) => {
    try {
      const response = await axios.post(`${API}/ndc-requests`, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setNdcRequests([...ndcRequests, response.data]);
      setIsCreateModalOpen(false);
      toast.success('NDC request created successfully');
    } catch (error) {
      console.error('Error creating NDC request:', error);
      toast.error(error.response?.data?.detail || 'Failed to create NDC request');
    }
  };

  const handleAddSeparationReason = async (formData) => {
    try {
      const response = await axios.post(`${API}/separation-reasons`, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setSeparationReasons([...separationReasons, response.data]);
      setIsAddReasonModalOpen(false);
      toast.success('Separation reason added successfully');
    } catch (error) {
      console.error('Error adding separation reason:', error);
      toast.error(error.response?.data?.detail || 'Failed to add separation reason');
    }
  };

  const handleRevokeNDC = async (ndcId, reason) => {
    try {
      await axios.post(`${API}/ndc-requests/${ndcId}/revoke`, { reason }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      fetchNDCRequests(); // Refresh data
      toast.success('NDC request revoked successfully');
    } catch (error) {
      console.error('Error revoking NDC request:', error);
      toast.error(error.response?.data?.detail || 'Failed to revoke NDC request');
    }
  };

  // Filter NDC requests based on search term and filters
  const filteredNDCRequests = ndcRequests.filter(ndc => {
    const matchesSearch = 
      ndc.employee_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ndc.employee_designation?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ndc.separation_reason?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || ndc.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Pagination logic
  const totalItems = filteredNDCRequests.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedNDCRequests = filteredNDCRequests.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter]);

  const getStatusBadgeColor = (status) => {
    const statusColors = {
      'Pending': { color: 'bg-yellow-100 text-yellow-800', icon: '⏳' },
      'In Progress': { color: 'bg-blue-100 text-blue-800', icon: '🔄' },
      'Assets Recovered': { color: 'bg-green-100 text-green-800', icon: '✅' },
      'Completed': { color: 'bg-emerald-100 text-emerald-800', icon: '🎉' },
      'Revoked': { color: 'bg-red-100 text-red-800', icon: '❌' }
    };
    return statusColors[status] || { color: 'bg-gray-100 text-gray-800', icon: '❓' };
  };

  // Check if current user can create NDC requests
  const canCreateNDC = () => {
    const accessibleRoles = user?.roles || [];
    return accessibleRoles.includes('HR Manager') || accessibleRoles.includes('Administrator');
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
          <h1 className="text-3xl font-bold text-gray-900">NDC Requests</h1>
          <p className="text-gray-600 mt-1">Manage No Dues Certificate requests for employee separation</p>
        </div>
        
        <div className="flex items-center gap-2">
          <ExportButton 
            data={filteredNDCRequests}
            type="ndcRequests"
            disabled={loading}
          />

          {canCreateNDC() && (
            <>
              <Button
                variant="outline"
                onClick={() => setIsAddReasonModalOpen(true)}
                className="bg-gray-50 hover:bg-gray-100"
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Reason
              </Button>
              
              <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="mr-2 h-4 w-4" />
                    Request for NDC
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Create NDC Request</DialogTitle>
                  </DialogHeader>
                  <NDCRequestForm 
                    employees={employees}
                    separationReasons={separationReasons}
                    managers={managers}
                    onSubmit={handleCreateNDCRequest} 
                  />
                </DialogContent>
              </Dialog>
            </>
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
                  placeholder="Search by employee name, designation, or reason..."
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
                  <SelectItem value="In Progress">In Progress</SelectItem>
                  <SelectItem value="Assets Recovered">Assets Recovered</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Revoked">Revoked</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* NDC Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle>NDC Requests ({filteredNDCRequests.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredNDCRequests.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No NDC requests found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters.' 
                  : 'Get started by creating a new NDC request.'
                }
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Designation</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Last Working Date</TableHead>
                      <TableHead>Separation Reason</TableHead>
                      <TableHead>Asset Manager</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedNDCRequests.map((ndc) => (
                      <TableRow key={ndc.id}>
                        <TableCell>
                          <div className="flex items-center">
                            <User className="h-4 w-4 text-gray-400 mr-2" />
                            <div>
                              <div className="font-medium">{ndc.employee_name}</div>
                              <div className="text-sm text-gray-500">{ndc.employee_email}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{ndc.employee_designation}</TableCell>
                        <TableCell>{ndc.location_name || '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                            {new Date(ndc.last_working_date).toLocaleDateString()}
                          </div>
                        </TableCell>
                        <TableCell>{ndc.separation_reason}</TableCell>
                        <TableCell>{ndc.asset_manager_name || 'Not assigned'}</TableCell>
                        <TableCell>
                          <Badge className={getStatusBadgeColor(ndc.status).color}>
                            {getStatusBadgeColor(ndc.status).icon} {ndc.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(ndc.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedNDC(ndc);
                                setIsAssetsModalOpen(true);
                              }}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View Assets
                            </Button>

                            {(ndc.status === 'Pending' || ndc.status === 'In Progress') && canCreateNDC() && (
                              <RevokeButton 
                                ndc={ndc}
                                onRevoke={handleRevokeNDC}
                              />
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

      {/* Add Separation Reason Modal */}
      <Dialog open={isAddReasonModalOpen} onOpenChange={setIsAddReasonModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Separation Reason</DialogTitle>
          </DialogHeader>
          <AddReasonForm onSubmit={handleAddSeparationReason} />
        </DialogContent>
      </Dialog>

      {/* NDC Assets View Modal */}
      <Dialog open={isAssetsModalOpen} onOpenChange={setIsAssetsModalOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              NDC Assets - {selectedNDC?.employee_name}
            </DialogTitle>
          </DialogHeader>
          {selectedNDC && (
            <NDCAssetsView ndc={selectedNDC} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// NDC Request Form Component
const NDCRequestForm = ({ employees, separationReasons, managers, onSubmit }) => {
  const [formData, setFormData] = useState({
    employee_id: '',
    resigned_on: '',
    notice_period: '',
    last_working_date: '',
    separation_approved_by: '',
    separation_approved_on: '',
    separation_reason_id: ''
  });
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (formData.employee_id) {
      const employee = employees.find(emp => emp.id === formData.employee_id);
      setSelectedEmployee(employee);
    } else {
      setSelectedEmployee(null);
    }
  }, [formData.employee_id, employees]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSubmit(formData);
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-h-96 overflow-y-auto">
      <div>
        <Label htmlFor="employee_id">Employee to be Separated *</Label>
        <Select 
          value={formData.employee_id} 
          onValueChange={(value) => setFormData({ ...formData, employee_id: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select employee" />
          </SelectTrigger>
          <SelectContent>
            {employees.map(employee => (
              <SelectItem key={employee.id} value={employee.id}>
                {employee.name} ({employee.email})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selectedEmployee && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-2">
          <h4 className="font-medium text-gray-900">Employee Information</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Designation:</span>
              <div className="font-medium">{selectedEmployee.designation || 'Not specified'}</div>
            </div>
            <div>
              <span className="text-gray-600">Date of Joining:</span>
              <div className="font-medium">
                {selectedEmployee.date_of_joining 
                  ? new Date(selectedEmployee.date_of_joining).toLocaleDateString()
                  : 'Not specified'
                }
              </div>
            </div>
            <div>
              <span className="text-gray-600">Location:</span>
              <div className="font-medium">{selectedEmployee.location_name || 'Not specified'}</div>
            </div>
            <div>
              <span className="text-gray-600">Reporting Manager:</span>
              <div className="font-medium">{selectedEmployee.reporting_manager_name || 'Not specified'}</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="resigned_on">Resigned On *</Label>
          <Input
            id="resigned_on"
            type="date"
            value={formData.resigned_on}
            onChange={(e) => setFormData({ ...formData, resigned_on: e.target.value })}
            required
          />
        </div>

        <div>
          <Label htmlFor="notice_period">Notice Period *</Label>
          <Select 
            value={formData.notice_period} 
            onValueChange={(value) => setFormData({ ...formData, notice_period: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select notice period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Immediate">Immediate</SelectItem>
              <SelectItem value="7 days">7 days</SelectItem>
              <SelectItem value="15 days">15 days</SelectItem>
              <SelectItem value="30 days">30 days</SelectItem>
              <SelectItem value="60 days">60 days</SelectItem>
              <SelectItem value="90 days">90 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="last_working_date">Last Working Date *</Label>
        <Input
          id="last_working_date"
          type="date"
          value={formData.last_working_date}
          onChange={(e) => setFormData({ ...formData, last_working_date: e.target.value })}
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="separation_approved_by">Separation Approved By *</Label>
          <Select 
            value={formData.separation_approved_by} 
            onValueChange={(value) => setFormData({ ...formData, separation_approved_by: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select approver" />
            </SelectTrigger>
            <SelectContent>
              {managers.map(manager => (
                <SelectItem key={manager.id} value={manager.id}>
                  {manager.name} ({manager.email})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="separation_approved_on">Separation Approved On *</Label>
          <Input
            id="separation_approved_on"
            type="date"
            value={formData.separation_approved_on}
            onChange={(e) => setFormData({ ...formData, separation_approved_on: e.target.value })}
            required
          />
        </div>
      </div>

      <div>
        <Label htmlFor="separation_reason_id">Reason for Separation *</Label>
        <Select 
          value={formData.separation_reason_id} 
          onValueChange={(value) => setFormData({ ...formData, separation_reason_id: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select separation reason" />
          </SelectTrigger>
          <SelectContent>
            {separationReasons.map(reason => (
              <SelectItem key={reason.id} value={reason.id}>
                {reason.reason}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Creating...' : 'Submit NDC Request'}
        </Button>
      </div>
    </form>
  );
};

// Add Reason Form Component
const AddReasonForm = ({ onSubmit }) => {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSubmit({ reason });
    setLoading(false);
    setReason('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="reason">Separation Reason *</Label>
        <Input
          id="reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter separation reason"
          required
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading || !reason.trim()}>
          {loading ? 'Adding...' : 'Add Reason'}
        </Button>
      </div>
    </form>
  );
};

// Revoke Button Component
const RevokeButton = ({ ndc, onRevoke }) => {
  const [showDialog, setShowDialog] = useState(false);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRevoke = async () => {
    if (!reason.trim()) {
      toast.error('Please enter a reason for revocation');
      return;
    }

    setLoading(true);
    await onRevoke(ndc.id, reason);
    setLoading(false);
    setShowDialog(false);
    setReason('');
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowDialog(true)}
        className="text-red-600 hover:text-red-800"
      >
        <XCircle className="h-4 w-4 mr-1" />
        Revoke
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Revoke NDC Request</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p><strong>Employee:</strong> {ndc.employee_name}</p>
              <p><strong>Status:</strong> {ndc.status}</p>
            </div>

            <div>
              <Label htmlFor="revoke_reason">Reason for Revocation *</Label>
              <Textarea
                id="revoke_reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Enter reason for revoking this NDC request"
                rows={3}
                required
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowDialog(false);
                  setReason('');
                }}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleRevoke}
                disabled={loading || !reason.trim()}
                className="bg-red-600 hover:bg-red-700"
              >
                {loading ? 'Revoking...' : 'Revoke NDC'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

// NDC Assets View Component
const NDCAssetsView = ({ ndc }) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNDCAssets = async () => {
      try {
        const response = await axios.get(`${API}/ndc-requests/${ndc.id}/assets`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('session_token')}`
          }
        });
        setAssets(response.data);
      } catch (error) {
        console.error('Error fetching NDC assets:', error);
        toast.error('Failed to load NDC assets');
      } finally {
        setLoading(false);
      }
    };

    fetchNDCAssets();
  }, [ndc.id]);

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading assets...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">NDC Information</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Employee:</span>
            <div className="font-medium">{ndc.employee_name}</div>
          </div>
          <div>
            <span className="text-gray-600">Last Working Date:</span>
            <div className="font-medium">{new Date(ndc.last_working_date).toLocaleDateString()}</div>
          </div>
          <div>
            <span className="text-gray-600">Status:</span>
            <div className="font-medium">{ndc.status}</div>
          </div>
          <div>
            <span className="text-gray-600">Asset Manager:</span>
            <div className="font-medium">{ndc.asset_manager_name || 'Not assigned'}</div>
          </div>
        </div>
      </div>

      {assets.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No assets found</h3>
          <p className="mt-1 text-sm text-gray-500">
            This employee has no allocated assets to recover.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Asset Code</TableHead>
                <TableHead>Asset Type</TableHead>
                <TableHead>Asset Value</TableHead>
                <TableHead>Recovery Status</TableHead>
                <TableHead>Recovery Date</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead>Remarks</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assets.map((asset) => (
                <TableRow key={asset.asset_id}>
                  <TableCell className="font-medium">{asset.asset_code}</TableCell>
                  <TableCell>{asset.asset_type}</TableCell>
                  <TableCell>₹{asset.asset_value?.toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge className={asset.recovered ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                      {asset.recovered ? 'Recovered' : 'Pending'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {asset.recovery_date 
                      ? new Date(asset.recovery_date).toLocaleDateString()
                      : '-'
                    }
                  </TableCell>
                  <TableCell>{asset.asset_condition || '-'}</TableCell>
                  <TableCell className="max-w-xs truncate">{asset.remarks || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export default NDCRequests;