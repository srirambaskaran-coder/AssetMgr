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
import { toast } from 'sonner';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  FileText,
  Filter,
  IndianRupee
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetDefinitions = () => {
  const [assetDefinitions, setAssetDefinitions] = useState([]);
  const [assetTypes, setAssetTypes] = useState([]);
  const [assetManagers, setAssetManagers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedAssetDefinition, setSelectedAssetDefinition] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchAssetDefinitions();
    fetchAssetTypes();
    fetchAssetManagers();
    fetchLocations();
  }, []);

  const fetchAssetDefinitions = async () => {
    try {
      const response = await axios.get(`${API}/asset-definitions`);
      setAssetDefinitions(response.data);
    } catch (error) {
      console.error('Error fetching asset definitions:', error);
      toast.error('Failed to load asset definitions');
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

  const fetchAssetManagers = async () => {
    try {
      const response = await axios.get(`${API}/users/asset-managers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setAssetManagers(response.data);
    } catch (error) {
      console.error('Error fetching asset managers:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      setLocations(response.data.filter(location => location.status === 'Active'));
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const handleCreateAssetDefinition = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-definitions`, formData);
      setAssetDefinitions([...assetDefinitions, response.data]);
      setIsCreateModalOpen(false);
      toast.success('Asset definition created successfully');
    } catch (error) {
      console.error('Error creating asset definition:', error);
      toast.error(error.response?.data?.detail || 'Failed to create asset definition');
    }
  };

  const handleUpdateAssetDefinition = async (id, formData) => {
    try {
      const response = await axios.put(`${API}/asset-definitions/${id}`, formData);
      setAssetDefinitions(assetDefinitions.map(ad => ad.id === id ? response.data : ad));
      setIsEditModalOpen(false);
      setSelectedAssetDefinition(null);
      toast.success('Asset definition updated successfully');
    } catch (error) {
      console.error('Error updating asset definition:', error);
      toast.error(error.response?.data?.detail || 'Failed to update asset definition');
    }
  };

  const handleDeleteAssetDefinition = async (id) => {
    if (!window.confirm('Are you sure you want to delete this asset definition?')) return;
    
    try {
      await axios.delete(`${API}/asset-definitions/${id}`);
      setAssetDefinitions(assetDefinitions.filter(ad => ad.id !== id));
      toast.success('Asset definition deleted successfully');
    } catch (error) {
      console.error('Error deleting asset definition:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete asset definition');
    }
  };

  const filteredAssetDefinitions = assetDefinitions.filter(assetDef => {
    const matchesSearch = assetDef.asset_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         assetDef.asset_description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || assetDef.status === statusFilter;
    const matchesType = typeFilter === 'all' || assetDef.asset_type_id === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  // Pagination logic
  const totalItems = filteredAssetDefinitions.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedAssetDefinitions = filteredAssetDefinitions.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, typeFilter]);

  const getStatusBadgeColor = (status) => {
    const colors = {
      'Available': 'bg-green-100 text-green-800',
      'Allocated': 'bg-blue-100 text-blue-800',
      'Damaged': 'bg-red-100 text-red-800',
      'Lost': 'bg-gray-100 text-gray-800',
      'Under Repair': 'bg-yellow-100 text-yellow-800',
      'On Hold': 'bg-purple-100 text-purple-800'
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
          <h1 className="text-3xl font-bold text-gray-900">Asset Definitions</h1>
          <p className="text-gray-600 mt-1">Manage individual asset records and their specifications</p>
        </div>

        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="mr-2 h-4 w-4" />
              Add Asset Definition
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Asset Definition</DialogTitle>
            </DialogHeader>
            <AssetDefinitionForm 
              assetTypes={assetTypes}
              assetManagers={assetManagers}
              locations={locations}
              onSubmit={handleCreateAssetDefinition} 
            />
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
                  placeholder="Search by asset code or description..."
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
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Available">Available</SelectItem>
                  <SelectItem value="Allocated">Allocated</SelectItem>
                  <SelectItem value="Damaged">Damaged</SelectItem>
                  <SelectItem value="Lost">Lost</SelectItem>
                  <SelectItem value="Under Repair">Under Repair</SelectItem>
                  <SelectItem value="On Hold">On Hold</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Asset Definitions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <FileText className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>Asset Definitions ({filteredAssetDefinitions.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {filteredAssetDefinitions.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No asset definitions found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' || typeFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Get started by creating your first asset definition.'
                }
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset Code</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Current Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Asset Manager</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Allocated To</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedAssetDefinitions.map((assetDef) => (
                    <TableRow key={assetDef.id}>
                      <TableCell className="font-medium">{assetDef.asset_code}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {assetDef.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">{assetDef.asset_description}</TableCell>
                      <TableCell className="font-medium">
                        <div className="flex items-center">
                          <IndianRupee className="h-4 w-4 text-gray-500 mr-1" />
                          ₹{assetDef.asset_value?.toLocaleString()}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        <div className="flex items-center">
                          <IndianRupee className="h-4 w-4 text-gray-500 mr-1" />
                          ₹{assetDef.current_depreciation_value?.toLocaleString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeColor(assetDef.status)}>
                          {assetDef.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {assetDef.assigned_asset_manager_name || 
                          <span className="text-gray-400">Not assigned</span>
                        }
                      </TableCell>
                      <TableCell>
                        {assetDef.location_name || 
                          <span className="text-gray-400">Not assigned</span>
                        }
                      </TableCell>
                      <TableCell>
                        {assetDef.allocated_to_name || '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedAssetDefinition(assetDef);
                              setIsEditModalOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteAssetDefinition(assetDef.id)}
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
            <DialogTitle>Edit Asset Definition</DialogTitle>
          </DialogHeader>
          {selectedAssetDefinition && (
            <AssetDefinitionForm 
              assetTypes={assetTypes}
              assetManagers={assetManagers}
              locations={locations}
              initialData={selectedAssetDefinition}
              onSubmit={(formData) => handleUpdateAssetDefinition(selectedAssetDefinition.id, formData)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

const AssetDefinitionForm = ({ assetTypes, assetManagers, locations, initialData, onSubmit }) => {
  const [formData, setFormData] = useState({
    asset_type_id: initialData?.asset_type_id || '',
    asset_code: initialData?.asset_code || '',
    asset_description: initialData?.asset_description || '',
    asset_details: initialData?.asset_details || '',
    asset_value: initialData?.asset_value || '',
    asset_depreciation_value_per_year: initialData?.asset_depreciation_value_per_year || '',
    status: initialData?.status || 'Available',
    assigned_asset_manager_id: initialData?.assigned_asset_manager_id || '',
    location_id: initialData?.location_id || ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const submitData = {
      ...formData,
      asset_value: parseFloat(formData.asset_value),
      asset_depreciation_value_per_year: formData.asset_depreciation_value_per_year 
        ? parseFloat(formData.asset_depreciation_value_per_year) 
        : null
    };

    await onSubmit(submitData);
    setLoading(false);
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
          <Label htmlFor="asset_code">Asset Code *</Label>
          <Input
            id="asset_code"
            value={formData.asset_code}
            onChange={(e) => setFormData({ ...formData, asset_code: e.target.value })}
            placeholder="Enter unique asset code"
            required
          />
        </div>
      </div>

      <div>
        <Label htmlFor="asset_description">Asset Description *</Label>
        <Input
          id="asset_description"
          value={formData.asset_description}
          onChange={(e) => setFormData({ ...formData, asset_description: e.target.value })}
          placeholder="Enter asset description"
          required
        />
      </div>

      <div>
        <Label htmlFor="asset_details">Asset Details</Label>
        <Textarea
          id="asset_details"
          value={formData.asset_details}
          onChange={(e) => setFormData({ ...formData, asset_details: e.target.value })}
          placeholder="Enter detailed asset specifications, model numbers, etc."
          rows={3}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="asset_value">Asset Value (₹) *</Label>
          <Input
            id="asset_value"
            type="number"
            step="0.01"
            value={formData.asset_value}
            onChange={(e) => setFormData({ ...formData, asset_value: e.target.value })}
            placeholder="0.00"
            required
            min="0"
          />
        </div>
        <div>
          <Label htmlFor="asset_depreciation_value_per_year">Depreciation per Year (₹)</Label>
          <Input
            id="asset_depreciation_value_per_year"
            type="number"
            step="0.01"
            value={formData.asset_depreciation_value_per_year}
            onChange={(e) => setFormData({ ...formData, asset_depreciation_value_per_year: e.target.value })}
            placeholder="0.00"
            min="0"
          />
        </div>
      </div>

      <div>
        <Label htmlFor="status">Status</Label>
        <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
          <SelectTrigger>
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Available">Available</SelectItem>
            <SelectItem value="Allocated">Allocated</SelectItem>
            <SelectItem value="Damaged">Damaged</SelectItem>
            <SelectItem value="Lost">Lost</SelectItem>
            <SelectItem value="Under Repair">Under Repair</SelectItem>
            <SelectItem value="On Hold">On Hold</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="assigned_asset_manager_id">Assigned Asset Manager</Label>
          <Select 
            value={formData.assigned_asset_manager_id} 
            onValueChange={(value) => setFormData({ ...formData, assigned_asset_manager_id: value === 'none' ? '' : value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select asset manager" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Asset Manager</SelectItem>
              {assetManagers.map(manager => (
                <SelectItem key={manager.id} value={manager.id}>{manager.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="location_id">Location</Label>
          <Select 
            value={formData.location_id} 
            onValueChange={(value) => setFormData({ ...formData, location_id: value === 'none' ? '' : value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select location" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Location</SelectItem>
              {locations.map(location => (
                <SelectItem key={location.id} value={location.id}>{location.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Saving...' : (initialData ? 'Update' : 'Create')}
        </Button>
      </div>
    </form>
  );
};

export default AssetDefinitions;