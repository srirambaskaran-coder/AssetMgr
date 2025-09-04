import React, { useState, useEffect } from 'react';
import { useAuth, useRole } from '../App';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { DataPagination } from './ui/data-pagination';
import { toast } from 'sonner';
import { 
  UserX,
  Plus,
  Search,
  Filter,
  Calendar,
  User,
  MapPin,
  Package,
  FileText,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NDCRequests = () => {
  const { user } = useAuth();
  const { effectiveRole } = useRole();
  const [ndcRequests, setNdcRequests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [managers, setManagers] = useState([]);
  const [separationReasons, setSeparationReasons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isAddReasonModalOpen, setIsAddReasonModalOpen] = useState(false);
  const [selectedNDC, setSelectedNDC] = useState(null);
  const [isAssetsModalOpen, setIsAssetsModalOpen] = useState(false);
  const itemsPerPage = 10;

  const isHRManager = effectiveRole === 'HR Manager';
  const isAssetManager = effectiveRole === 'Asset Manager';

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter]);

  const fetchData = async () => {
    try {
      await Promise.all([
        fetchNDCRequests(),
        isHRManager && fetchEmployees(),
        isHRManager && fetchManagers(), 
        fetchSeparationReasons()
      ].filter(Boolean));
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNDCRequests = async () => {
    try {
      const response = await axios.get(`${API}/ndc-requests`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      setNdcRequests(response.data);
    } catch (error) {
      console.error('Error fetching NDC requests:', error);
      toast.error('Failed to fetch NDC requests');
    }
  };

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      // Filter active employees only
      const activeEmployees = response.data.filter(user => 
        user.is_active && user.roles.includes('Employee')
      );
      setEmployees(activeEmployees);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const fetchManagers = async () => {
    try {
      const response = await axios.get(`${API}/users/managers`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      setManagers(response.data);
    } catch (error) {
      console.error('Error fetching managers:', error);
    }
  };

  const fetchSeparationReasons = async () => {
    try {
      const response = await axios.get(`${API}/separation-reasons`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      setSeparationReasons(response.data);
    } catch (error) {
      console.error('Error fetching separation reasons:', error);
      // Set default reasons if none exist
      setSeparationReasons([
        { id: '1', reason: 'Better Opportunities' },
        { id: '2', reason: 'Asked To Go' }
      ]);
    }
  };

  const handleCreateNDC = async (formData) => {
    try {
      await axios.post(`${API}/ndc-requests`, formData, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      toast.success('NDC request created successfully');
      setIsCreateModalOpen(false);
      fetchNDCRequests();
    } catch (error) {
      console.error('Error creating NDC request:', error);
      toast.error(error.response?.data?.detail || 'Failed to create NDC request');
    }
  };

  const handleAddSeparationReason = async (reason) => {
    try {
      const response = await axios.post(`${API}/separation-reasons`, { reason }, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
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
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      toast.success('NDC request revoked successfully');
      fetchNDCRequests();
    } catch (error) {
      console.error('Error revoking NDC request:', error);
      toast.error(error.response?.data?.detail || 'Failed to revoke NDC request');
    }
  };

  const handleViewAssets = async (ndc) => {
    setSelectedNDC(ndc);
    setIsAssetsModalOpen(true);
  };

  // Filter NDC requests
  const filteredNDCRequests = ndcRequests.filter(ndc => {
    const matchesSearch = ndc.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ndc.employee_designation?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ndc.separation_reason.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || ndc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Apply pagination
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedNDCRequests = filteredNDCRequests.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Pending': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'Asset Manager Confirmation': { color: 'bg-blue-100 text-blue-800', icon: AlertCircle },
      'Completed': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Revoked': { color: 'bg-red-100 text-red-800', icon: AlertCircle }
    };
    
    const config = statusConfig[status] || statusConfig['Pending'];
    const Icon = config.icon;
    
    return (
      <Badge variant="outline" className={config.color}>
        <Icon className="mr-1 h-3 w-3" />
        {status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading NDC requests...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">NDC Requests</h1>
        <p className="text-gray-600 mt-1">
          {isHRManager ? 'Manage employee separation and asset recovery requests' :
           isAssetManager ? 'Process asset recovery for separated employees' :
           'View NDC requests and asset recovery status'}
        </p>
      </div>

      {/* Actions and Filters */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="flex items-center">
              <UserX className="mr-2 h-5 w-5 text-blue-600" />
              NDC Requests
            </CardTitle>
            <div className="flex gap-2">
              {isHRManager && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setIsAddReasonModalOpen(true)}
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
                    <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Create NDC Request</DialogTitle>
                      </DialogHeader>
                      <NDCRequestForm 
                        onSubmit={handleCreateNDC}
                        employees={employees}
                        managers={managers}
                        separationReasons={separationReasons}
                      />
                    </DialogContent>
                  </Dialog>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
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
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Pending">Pending</SelectItem>
                  <SelectItem value="Asset Manager Confirmation">In Progress</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Revoked">Revoked</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* NDC Requests Table */}
          {filteredNDCRequests.length === 0 ? (
            <div className="text-center py-12">
              <UserX className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No NDC requests found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.'
                  : 'No NDC requests have been created yet.'
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
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedNDCRequests.map((ndc) => (
                      <TableRow key={ndc.id}>
                        <TableCell>
                          <div className="flex items-center">
                            <User className="mr-2 h-4 w-4 text-gray-400" />
                            <div>
                              <div className="font-medium">{ndc.employee_name}</div>
                              <div className="text-sm text-gray-500">{ndc.employee_code}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{ndc.employee_designation || 'N/A'}</TableCell>
                        <TableCell>
                          {ndc.employee_location_name && (
                            <div className="flex items-center">
                              <MapPin className="mr-1 h-4 w-4 text-gray-400" />
                              <span className="text-sm">{ndc.employee_location_name}</span>
                            </div>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <Calendar className="mr-1 h-4 w-4 text-gray-400" />
                            <span className="text-sm">
                              {new Date(ndc.last_working_date).toLocaleDateString()}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="bg-gray-50">
                            {ndc.separation_reason}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm font-medium">{ndc.asset_manager_name}</div>
                        </TableCell>
                        <TableCell>{getStatusBadge(ndc.status)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewAssets(ndc)}
                            >
                              <Package className="h-4 w-4" />
                            </Button>
                            {isHRManager && ndc.status !== 'Completed' && ndc.status !== 'Revoked' && (
                              <RevokeButton ndcId={ndc.id} onRevoke={handleRevokeNDC} />
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              {/* Pagination */}
              <DataPagination
                currentPage={currentPage}
                totalPages={Math.ceil(filteredNDCRequests.length / itemsPerPage)}
                totalItems={filteredNDCRequests.length}
                itemsPerPage={itemsPerPage}
                onPageChange={handlePageChange}
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* Add Reason Modal */}
      <Dialog open={isAddReasonModalOpen} onOpenChange={setIsAddReasonModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Separation Reason</DialogTitle>
          </DialogHeader>
          <AddReasonForm onSubmit={handleAddSeparationReason} />
        </DialogContent>
      </Dialog>

      {/* Assets Modal */}
      {selectedNDC && (
        <Dialog open={isAssetsModalOpen} onOpenChange={setIsAssetsModalOpen}>
          <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>NDC Assets - {selectedNDC.employee_name}</DialogTitle>
            </DialogHeader>
            <NDCAssetsView 
              ndc={selectedNDC} 
              isAssetManager={isAssetManager}
              onUpdate={fetchNDCRequests}
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

// Additional components will be added in separate files or below...
// For now, let's create placeholder components

const NDCRequestForm = ({ onSubmit, employees, managers, separationReasons }) => {
  const [formData, setFormData] = useState({
    employee_id: '',
    resigned_on: '',
    notice_period: 'Immediate',
    last_working_date: '',
    separation_approved_by: '',
    separation_approved_on: '',
    separation_reason: ''
  });
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeAssets, setEmployeeAssets] = useState([]);
  const [loading, setLoading] = useState(false);

  const noticePeriodOptions = [
    'Immediate', '7 days', '15 days', '30 days', '60 days', '90 days'
  ];

  const handleEmployeeSelect = async (employeeId) => {
    if (employeeId === 'none') {
      setSelectedEmployee(null);
      setEmployeeAssets([]);
      setFormData({ ...formData, employee_id: '' });
      return;
    }

    const employee = employees.find(emp => emp.id === employeeId);
    setSelectedEmployee(employee);
    setFormData({ ...formData, employee_id: employeeId });

    // Fetch employee assets
    try {
      const response = await axios.get(`${API}/asset-definitions`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      const userAssets = response.data.filter(asset => 
        asset.assigned_to === employeeId && asset.status === 'Allocated'
      );
      setEmployeeAssets(userAssets);
    } catch (error) {
      console.error('Error fetching employee assets:', error);
      setEmployeeAssets([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmployee || employeeAssets.length === 0) {
      toast.error('Please select an employee with allocated assets');
      return;
    }

    setLoading(true);
    const submitData = {
      ...formData,
      resigned_on: new Date(formData.resigned_on).toISOString(),
      last_working_date: new Date(formData.last_working_date).toISOString(),
      separation_approved_on: new Date(formData.separation_approved_on).toISOString()
    };

    await onSubmit(submitData);
    setLoading(false);
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Employee Selection */}
      <div>
        <Label htmlFor="employee_id">Employee to be Separated *</Label>
        <Select value={formData.employee_id} onValueChange={handleEmployeeSelect}>
          <SelectTrigger>
            <SelectValue placeholder="Select employee" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Select Employee</SelectItem>
            {employees.map(employee => (
              <SelectItem key={employee.id} value={employee.id}>
                {employee.name} ({employee.email})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Employee Details */}
      {selectedEmployee && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Employee Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-gray-500">Name</Label>
                <p className="text-sm">{selectedEmployee.name}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Designation</Label>
                <p className="text-sm">{selectedEmployee.designation || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Date of Joining</Label>
                <p className="text-sm">
                  {selectedEmployee.date_of_joining 
                    ? new Date(selectedEmployee.date_of_joining).toLocaleDateString()
                    : 'N/A'
                  }
                </p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Location</Label>
                <p className="text-sm">{selectedEmployee.location_name || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Reporting Manager</Label>
                <p className="text-sm">{selectedEmployee.reporting_manager_name || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Assets Allocated</Label>
                <p className="text-sm font-medium text-blue-600">{employeeAssets.length} items</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Separation Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="resigned_on">Resigned On *</Label>
          <Input
            id="resigned_on"
            type="date"
            value={formData.resigned_on}
            onChange={(e) => handleChange('resigned_on', e.target.value)}
            required
          />
        </div>
        
        <div>
          <Label htmlFor="notice_period">Notice Period *</Label>
          <Select value={formData.notice_period} onValueChange={(value) => handleChange('notice_period', value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {noticePeriodOptions.map(option => (
                <SelectItem key={option} value={option}>{option}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="last_working_date">Last Working Date *</Label>
          <Input
            id="last_working_date"
            type="date"
            value={formData.last_working_date}
            onChange={(e) => handleChange('last_working_date', e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="separation_approved_by">Separation Approved By *</Label>
          <Select value={formData.separation_approved_by} onValueChange={(value) => handleChange('separation_approved_by', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select approver" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Select Approver</SelectItem>
              {managers.map(manager => (
                <SelectItem key={manager.id} value={manager.id}>
                  {manager.name} ({manager.designation || 'Manager'})
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
            onChange={(e) => handleChange('separation_approved_on', e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="separation_reason">Reason for Separation *</Label>
          <Select value={formData.separation_reason} onValueChange={(value) => handleChange('separation_reason', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select reason" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Select Reason</SelectItem>
              {separationReasons.map(reason => (
                <SelectItem key={reason.id} value={reason.reason}>
                  {reason.reason}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Assets List */}
      {employeeAssets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Assets Associated with Employee</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset Code</TableHead>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Asset Value</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employeeAssets.map((asset) => (
                    <TableRow key={asset.id}>
                      <TableCell className="font-medium">{asset.asset_code}</TableCell>
                      <TableCell>{asset.asset_type_name}</TableCell>
                      <TableCell>₹{asset.asset_value?.toLocaleString() || 0}</TableCell>
                      <TableCell>
                        <Badge className="bg-blue-100 text-blue-800">
                          {asset.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Creating NDC Request...' : 'Submit NDC Request'}
        </Button>
      </div>
    </form>
  );
};

const AddReasonForm = ({ onSubmit }) => {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      toast.error('Please enter a separation reason');
      return;
    }

    setLoading(true);
    await onSubmit(reason.trim());
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
          placeholder="e.g., Performance Issues, Voluntary Resignation"
          required
        />
      </div>

      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Adding...' : 'Add Reason'}
        </Button>
      </div>
    </form>
  );
};

const RevokeButton = ({ ndcId, onRevoke }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRevoke = async () => {
    if (!reason.trim()) {
      toast.error('Please provide a reason for revocation');
      return;
    }

    setLoading(true);
    await onRevoke(ndcId, reason.trim());
    setLoading(false);
    setIsOpen(false);
    setReason('');
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-800">
          <AlertCircle className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Revoke NDC Request</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Are you sure you want to revoke this NDC request? Please provide a reason.
          </p>
          <div>
            <Label htmlFor="revoke_reason">Reason for Revocation *</Label>
            <Input
              id="revoke_reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g., Employee decided not to resign"
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleRevoke} 
              disabled={loading}
              className="bg-red-600 hover:bg-red-700"
            >
              {loading ? 'Revoking...' : 'Revoke Request'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const NDCAssetsView = ({ ndc, isAssetManager, onUpdate }) => {
  // This will be implemented next
  return <div>NDC Assets View - To be implemented</div>;
};

export default NDCRequests;