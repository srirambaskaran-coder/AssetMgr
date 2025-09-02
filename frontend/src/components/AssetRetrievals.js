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
import { Switch } from './ui/switch';
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
  AlertTriangle,
  Edit,
  DollarSign
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetRetrievals = () => {
  const [retrievals, setRetrievals] = useState([]);
  const [allocatedAssets, setAllocatedAssets] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedRetrieval, setSelectedRetrieval] = useState(null);

  useEffect(() => {
    fetchRetrievals();
    fetchAllocatedAssets();
    fetchUsers();
  }, []);

  const fetchRetrievals = async () => {
    try {
      const response = await axios.get(`${API}/asset-retrievals`);
      setRetrievals(response.data);
    } catch (error) {
      console.error('Error fetching retrievals:', error);
      toast.error('Failed to load asset retrievals');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllocatedAssets = async () => {
    try {
      const response = await axios.get(`${API}/allocated-assets`);
      setAllocatedAssets(response.data);
    } catch (error) {
      console.error('Error fetching allocated assets:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleCreateRetrieval = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-retrievals`, formData);
      setRetrievals([response.data, ...retrievals]);
      setIsCreateModalOpen(false);
      await fetchAllocatedAssets(); // Refresh allocated assets
      toast.success('Asset retrieval record created successfully');
    } catch (error) {
      console.error('Error creating retrieval:', error);
      toast.error(error.response?.data?.detail || 'Failed to create asset retrieval');
    }
  };

  const handleUpdateRetrieval = async (id, formData) => {
    try {
      const response = await axios.put(`${API}/asset-retrievals/${id}`, formData);
      setRetrievals(retrievals.map(retrieval => retrieval.id === id ? response.data : retrieval));
      setIsEditModalOpen(false);
      setSelectedRetrieval(null);
      await fetchAllocatedAssets(); // Refresh allocated assets
      toast.success('Asset retrieval updated successfully');
    } catch (error) {
      console.error('Error updating retrieval:', error);
      toast.error(error.response?.data?.detail || 'Failed to update asset retrieval');
    }
  };

  const filteredRetrievals = retrievals.filter(retrieval => {
    const matchesSearch = retrieval.employee_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         retrieval.asset_definition_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         retrieval.asset_type_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'recovered' && retrieval.recovered) ||
                         (statusFilter === 'pending' && !retrieval.recovered);
    return matchesSearch && matchesStatus;
  });

  const getStatusBadgeColor = (recovered) => {
    return recovered 
      ? 'bg-green-100 text-green-800'
      : 'bg-orange-100 text-orange-800';
  };

  const getConditionBadgeColor = (condition) => {
    const colors = {
      'Good Condition': 'bg-green-100 text-green-800',
      'Damaged': 'bg-red-100 text-red-800'
    };
    return colors[condition] || 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold text-gray-900">Asset Retrievals</h1>
          <p className="text-gray-600 mt-1">Manage asset recovery from employees on separation</p>
        </div>

        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="mr-2 h-4 w-4" />
              Create Retrieval Record
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create Asset Retrieval Record</DialogTitle>
            </DialogHeader>
            <RetrievalForm 
              allocatedAssets={allocatedAssets}
              users={users}
              onSubmit={handleCreateRetrieval}
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
                <p className="text-sm text-gray-600">Total Retrievals</p>
                <p className="text-2xl font-bold text-gray-900">{retrievals.length}</p>
              </div>
              <Package className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Recovery</p>
                <p className="text-2xl font-bold text-orange-600">
                  {retrievals.filter(r => !r.recovered).length}
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Successfully Recovered</p>
                <p className="text-2xl font-bold text-green-600">
                  {retrievals.filter(r => r.recovered).length}
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
                <p className="text-sm text-gray-600">Assets with Users</p>
                <p className="text-2xl font-bold text-purple-600">{allocatedAssets.length}</p>
              </div>
              <User className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by employee name, asset code, or asset type..."
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
                  <SelectItem value="pending">Pending Recovery</SelectItem>
                  <SelectItem value="recovered">Recovered</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Retrievals Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <Package className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>Asset Retrievals ({filteredRetrievals.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {filteredRetrievals.length === 0 ? (
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No retrievals found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Start by creating asset retrieval records for separating employees.'
                }
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Asset Code</TableHead>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Returned On</TableHead>
                    <TableHead>Recovery Value</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRetrievals.map((retrieval) => (
                    <TableRow key={retrieval.id}>
                      <TableCell>
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-1 text-gray-500" />
                          {retrieval.employee_name}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{retrieval.asset_definition_code}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {retrieval.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeColor(retrieval.recovered)}>
                          {retrieval.recovered ? 'Recovered' : 'Pending Recovery'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {retrieval.asset_condition && (
                          <Badge className={getConditionBadgeColor(retrieval.asset_condition)}>
                            {retrieval.asset_condition}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {retrieval.returned_on && (
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1 text-gray-500" />
                            {new Date(retrieval.returned_on).toLocaleDateString()}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {retrieval.recovery_value && (
                          <div className="flex items-center">
                            <DollarSign className="h-4 w-4 mr-1 text-gray-500" />
                            {retrieval.recovery_value.toLocaleString()}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedRetrieval(retrieval);
                            setIsEditModalOpen(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Update Asset Retrieval</DialogTitle>
          </DialogHeader>
          {selectedRetrieval && (
            <RetrievalUpdateForm 
              retrieval={selectedRetrieval}
              onSubmit={(formData) => handleUpdateRetrieval(selectedRetrieval.id, formData)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

const RetrievalForm = ({ allocatedAssets, users, onSubmit }) => {
  const [formData, setFormData] = useState({
    employee_id: '',
    asset_definition_id: '',
    remarks: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSubmit(formData);
    setLoading(false);
    setFormData({
      employee_id: '',
      asset_definition_id: '',
      remarks: ''
    });
  };

  const selectedEmployee = users.find(user => user.id === formData.employee_id);
  const employeeAssets = allocatedAssets.filter(asset => asset.allocated_to === formData.employee_id);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="employee_id">Employee *</Label>
        <Select 
          value={formData.employee_id} 
          onValueChange={(value) => setFormData({ ...formData, employee_id: value, asset_definition_id: '' })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select employee" />
          </SelectTrigger>
          <SelectContent>
            {users.filter(user => 
              allocatedAssets.some(asset => asset.allocated_to === user.id)
            ).map(user => (
              <SelectItem key={user.id} value={user.id}>
                {user.name} ({user.email})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="asset_definition_id">Asset to Retrieve *</Label>
        <Select 
          value={formData.asset_definition_id} 
          onValueChange={(value) => setFormData({ ...formData, asset_definition_id: value })}
          disabled={!selectedEmployee}
        >
          <SelectTrigger>
            <SelectValue placeholder={selectedEmployee ? "Select asset" : "Select employee first"} />
          </SelectTrigger>
          <SelectContent>
            {employeeAssets.map(asset => (
              <SelectItem key={asset.id} value={asset.id}>
                {asset.asset_code} - {asset.asset_description}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="remarks">Initial Remarks</Label>
        <Textarea
          id="remarks"
          value={formData.remarks}
          onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
          placeholder="Enter initial remarks about the retrieval process"
          rows={3}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading || !formData.employee_id || !formData.asset_definition_id} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Creating...' : 'Create Retrieval Record'}
        </Button>
      </div>
    </form>
  );
};

const RetrievalUpdateForm = ({ retrieval, onSubmit }) => {
  const [formData, setFormData] = useState({
    recovered: retrieval.recovered,
    asset_condition: retrieval.asset_condition || 'Good Condition',
    returned_on: retrieval.returned_on ? new Date(retrieval.returned_on).toISOString().split('T')[0] : '',
    recovery_value: retrieval.recovery_value || '',
    remarks: retrieval.remarks || '',
    status: retrieval.status || 'Pending Recovery'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const submitData = {
      ...formData,
      returned_on: formData.returned_on ? new Date(formData.returned_on).toISOString() : null,
      recovery_value: formData.recovery_value ? parseFloat(formData.recovery_value) : null
    };
    
    await onSubmit(submitData);
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      {/* Retrieval Info */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">Asset Retrieval Details</h4>
        <div className="text-sm text-blue-800">
          <p><strong>Employee:</strong> {retrieval.employee_name}</p>
          <p><strong>Asset:</strong> {retrieval.asset_definition_code}</p>
          <p><strong>Asset Type:</strong> {retrieval.asset_type_name}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center space-x-2">
          <Switch
            id="recovered"
            checked={formData.recovered}
            onCheckedChange={(checked) => setFormData({ 
              ...formData, 
              recovered: checked,
              returned_on: checked && !formData.returned_on ? new Date().toISOString().split('T')[0] : formData.returned_on
            })}
          />
          <Label htmlFor="recovered">Asset Recovered</Label>
        </div>

        {formData.recovered && (
          <>
            <div>
              <Label htmlFor="asset_condition">Asset Condition *</Label>
              <Select 
                value={formData.asset_condition} 
                onValueChange={(value) => setFormData({ ...formData, asset_condition: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select condition" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Good Condition">Good Condition</SelectItem>
                  <SelectItem value="Damaged">Damaged</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="returned_on">Returned On *</Label>
              <Input
                id="returned_on"
                type="date"
                value={formData.returned_on}
                onChange={(e) => setFormData({ ...formData, returned_on: e.target.value })}
                required
              />
            </div>

            {formData.asset_condition === 'Damaged' && (
              <div>
                <Label htmlFor="recovery_value">Recovery Value ($)</Label>
                <Input
                  id="recovery_value"
                  type="number"
                  step="0.01"
                  value={formData.recovery_value}
                  onChange={(e) => setFormData({ ...formData, recovery_value: e.target.value })}
                  placeholder="0.00"
                />
              </div>
            )}
          </>
        )}

        <div>
          <Label htmlFor="remarks">Remarks</Label>
          <Textarea
            id="remarks"
            value={formData.remarks}
            onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
            placeholder="Enter remarks about the retrieval process"
            rows={3}
          />
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
            {loading ? 'Updating...' : 'Update Retrieval'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default AssetRetrievals;