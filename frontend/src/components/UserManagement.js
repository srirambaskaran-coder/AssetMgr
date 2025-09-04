import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { DataPagination } from './ui/data-pagination';
import { toast } from 'sonner';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Users,
  Filter,
  UserCheck,
  UserX,
  User,
  Calendar
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [managers, setManagers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchUsers();
    fetchManagers();
    fetchLocations();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const fetchManagers = async () => {
    try {
      const response = await axios.get(`${API}/users/managers`);
      setManagers(response.data);
    } catch (error) {
      console.error('Error fetching managers:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const handleCreateUser = async (formData) => {
    try {
      const response = await axios.post(`${API}/users`, formData);
      setUsers([...users, response.data]);
      setIsCreateModalOpen(false);
      await fetchManagers(); // Refresh managers list
      toast.success('User created successfully');
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleUpdateUser = async (id, formData) => {
    try {
      const response = await axios.put(`${API}/users/${id}`, formData);
      setUsers(users.map(user => user.id === id ? response.data : user));
      setIsEditModalOpen(false);
      setSelectedUser(null);
      await fetchManagers(); // Refresh managers list
      toast.success('User updated successfully');
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await axios.delete(`${API}/users/${id}`);
      setUsers(users.filter(user => user.id !== id));
      toast.success('User deleted successfully');
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const userRoles = user.roles || [user.role]; // Handle both new and old data structure
    const matchesRole = roleFilter === 'all' || userRoles.includes(roleFilter);
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && user.is_active) ||
                         (statusFilter === 'inactive' && !user.is_active);
    const matchesLocation = locationFilter === 'all' || user.location_name === locationFilter;
    return matchesSearch && matchesRole && matchesStatus && matchesLocation;
  });

  // Pagination logic
  const totalItems = filteredUsers.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedUsers = filteredUsers.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, roleFilter, statusFilter, locationFilter]);

  const getRoleBadgeColor = (role) => {
    const colors = {
      'Administrator': 'bg-purple-100 text-purple-800',
      'HR Manager': 'bg-blue-100 text-blue-800',
      'Manager': 'bg-green-100 text-green-800',
      'Asset Manager': 'bg-orange-100 text-orange-800',
      'Employee': 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600 mt-1">Manage system users and their access permissions</p>
        </div>

        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="mr-2 h-4 w-4" />
              Add User
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New User</DialogTitle>
            </DialogHeader>
            <UserForm onSubmit={handleCreateUser} managers={managers} locations={locations} />
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search users by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Filter by role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  <SelectItem value="Administrator">Administrator</SelectItem>
                  <SelectItem value="HR Manager">HR Manager</SelectItem>
                  <SelectItem value="Manager">Manager</SelectItem>
                  <SelectItem value="Employee">Employee</SelectItem>
                  <SelectItem value="Asset Manager">Asset Manager</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
              <Select value={locationFilter} onValueChange={setLocationFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Filter by location" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Locations</SelectItem>
                  {locations.map(location => (
                    <SelectItem key={location.id} value={location.name}>
                      {location.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <Users className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>Users ({filteredUsers.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {filteredUsers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No users found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || roleFilter !== 'all' || statusFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Get started by creating your first user.'
                }
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Designation</TableHead>
                    <TableHead>Roles</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Reporting To</TableHead>
                    <TableHead>Joining Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        {user.designation && (
                          <Badge variant="outline" className="bg-gray-50">
                            {user.designation}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {(user.roles || [user.role]).map((role) => (
                            <Badge key={role} className={getRoleBadgeColor(role)}>
                              {role}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.location_name ? (
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                            {user.location_name}
                          </Badge>
                        ) : (
                          <span className="text-gray-500 text-sm">Not Assigned</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.reporting_manager_name && (
                          <div className="flex items-center">
                            <User className="h-4 w-4 mr-1 text-gray-500" />
                            <span className="text-sm">{user.reporting_manager_name}</span>
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.date_of_joining && (
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1 text-gray-500" />
                            {new Date(user.date_of_joining).toLocaleDateString()}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {user.is_active ? (
                            <>
                              <UserCheck className="h-4 w-4 text-green-600" />
                              <Badge className="bg-green-100 text-green-800">Active</Badge>
                            </>
                          ) : (
                            <>
                              <UserX className="h-4 w-4 text-red-600" />
                              <Badge className="bg-red-100 text-red-800">Inactive</Badge>
                            </>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsEditModalOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
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

      {/* Edit Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
          </DialogHeader>
          {selectedUser && (
            <UserForm 
              initialData={selectedUser}
              onSubmit={(formData) => handleUpdateUser(selectedUser.id, formData)}
              managers={managers}
              locations={locations}
              isEdit={true}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

const UserForm = ({ initialData, onSubmit, managers = [], locations = [], isEdit = false }) => {
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    email: initialData?.email || '',
    designation: initialData?.designation || '',
    roles: initialData?.roles || ['Employee'],
    password: '',
    date_of_joining: initialData?.date_of_joining ? new Date(initialData.date_of_joining).toISOString().split('T')[0] : '',
    reporting_manager_id: initialData?.reporting_manager_id || 'none',
    location_id: initialData?.location_id ? initialData.location_id : 'none',
    is_active: initialData?.is_active ?? true
  });
  const [loading, setLoading] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const submitData = isEdit 
      ? { 
          name: formData.name, 
          designation: formData.designation,
          roles: formData.roles, 
          date_of_joining: formData.date_of_joining ? new Date(formData.date_of_joining).toISOString() : null,
          reporting_manager_id: formData.reporting_manager_id === "none" ? null : formData.reporting_manager_id || null,
          location_id: formData.location_id === "none" ? null : formData.location_id || null,
          is_active: formData.is_active,
          // Include password only if it's being changed
          ...(showPasswordChange && formData.password ? { password: formData.password } : {})
        }
      : {
          ...formData,
          date_of_joining: formData.date_of_joining ? new Date(formData.date_of_joining).toISOString() : null,
          reporting_manager_id: formData.reporting_manager_id === "none" ? null : formData.reporting_manager_id || null,
          location_id: formData.location_id === "none" ? null : formData.location_id || null
        };

    await onSubmit(submitData);
    setLoading(false);
    
    if (!isEdit) {
      setFormData({
        name: '',
        email: '',
        designation: '',
        roles: ['Employee'],
        password: '',
        date_of_joining: '',
        reporting_manager_id: 'none',
        location_id: 'none',
        is_active: true
      });
    }
  };

  // Filter out the current user from reporting managers (to prevent self-reporting)
  const availableManagers = managers.filter(manager => 
    !isEdit || manager.id !== initialData?.id
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-h-96 overflow-y-auto">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Full Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter full name"
            required
          />
        </div>

        <div>
          <Label htmlFor="email">Email Address *</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="Enter email address"
            required
            disabled={isEdit}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="designation">Designation</Label>
          <Input
            id="designation"
            value={formData.designation}
            onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
            placeholder="e.g., Software Engineer, HR Manager"
          />
        </div>

        <div>
          <Label htmlFor="date_of_joining">Date of Joining</Label>
          <Input
            id="date_of_joining"
            type="date"
            value={formData.date_of_joining}
            onChange={(e) => setFormData({ ...formData, date_of_joining: e.target.value })}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="roles">Roles *</Label>
          <div className="space-y-2">
            {['Employee', 'Manager', 'HR Manager', 'Asset Manager', 'Administrator'].map((roleOption) => (
              <div key={roleOption} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`role_${roleOption}`}
                  checked={formData.roles.includes(roleOption)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData({ 
                        ...formData, 
                        roles: [...formData.roles, roleOption]
                      });
                    } else {
                      setFormData({ 
                        ...formData, 
                        roles: formData.roles.filter(r => r !== roleOption)
                      });
                    }
                  }}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <Label htmlFor={`role_${roleOption}`} className="text-sm font-normal">
                  {roleOption}
                </Label>
              </div>
            ))}
            {formData.roles.length === 0 && (
              <p className="text-sm text-red-600">Please select at least one role</p>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="reporting_manager_id">Reporting Manager</Label>
          <Select 
            value={formData.reporting_manager_id} 
            onValueChange={(value) => setFormData({ ...formData, reporting_manager_id: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select reporting manager" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Reporting Manager</SelectItem>
              {availableManagers.map(manager => (
                <SelectItem key={manager.id} value={manager.id}>
                  {manager.name} ({manager.role})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="location_id">Location</Label>
          <Select 
            value={formData.location_id} 
            onValueChange={(value) => setFormData({ ...formData, location_id: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select location" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Location Assigned</SelectItem>
              {locations.map(location => (
                <SelectItem key={location.id} value={location.id}>
                  {location.name} ({location.country})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          {/* Empty div for grid layout balance */}
        </div>
      </div>

      {/* Password Section */}
      {!isEdit ? (
        <div>
          <Label htmlFor="password">Password *</Label>
          <Input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            placeholder="Enter password"
            required
          />
        </div>
      ) : (
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label>Password</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowPasswordChange(!showPasswordChange)}
            >
              {showPasswordChange ? 'Cancel' : 'Change Password'}
            </Button>
          </div>
          {showPasswordChange && (
            <div>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Enter new password"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Leave empty to keep current password
              </p>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <div className="flex items-center space-x-2">
          <Switch
            id="is_active"
            checked={formData.is_active}
            onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
          />
          <Label htmlFor="is_active">Active User</Label>
        </div>
      </div>

      {formData.roles.includes('Manager') && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center">
            <UserCheck className="h-4 w-4 text-blue-600 mr-2" />
            <span className="text-sm text-blue-800 font-medium">
              This user has Manager role and will be available as a reporting manager for other employees
            </span>
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Saving...' : (isEdit ? 'Update User' : 'Create User')}
        </Button>
      </div>
    </form>
  );
};

export default UserManagement;