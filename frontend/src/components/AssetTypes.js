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
  Package,
  Filter
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetTypes = () => {
  const [assetTypes, setAssetTypes] = useState([]);
  const [assetManagers, setAssetManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedAssetType, setSelectedAssetType] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchAssetTypes();
    fetchAssetManagers();
  }, []);

  const fetchAssetTypes = async () => {
    try {
      const response = await axios.get(`${API}/asset-types`);
      setAssetTypes(response.data);
    } catch (error) {
      console.error('Error fetching asset types:', error);
      toast.error('Failed to load asset types');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssetManagers = async () => {
    try {
      const response = await axios.get(`${API}/users/asset-managers`);
      setAssetManagers(response.data);
    } catch (error) {
      console.error('Error fetching asset managers:', error);
      toast.error('Failed to load asset managers');
    }
  };

  const handleCreateAssetType = async (formData) => {
    try {
      const response = await axios.post(`${API}/asset-types`, formData);
      setAssetTypes([...assetTypes, response.data]);
      setIsCreateModalOpen(false);
      toast.success('Asset type created successfully');
    } catch (error) {
      console.error('Error creating asset type:', error);
      toast.error(error.response?.data?.detail || 'Failed to create asset type');
    }
  };

  const handleUpdateAssetType = async (id, formData) => {
    try {
      const response = await axios.put(`${API}/asset-types/${id}`, formData);
      setAssetTypes(assetTypes.map(at => at.id === id ? response.data : at));
      setIsEditModalOpen(false);
      setSelectedAssetType(null);
      toast.success('Asset type updated successfully');
    } catch (error) {
      console.error('Error updating asset type:', error);
      toast.error(error.response?.data?.detail || 'Failed to update asset type');
    }
  };

  const handleDeleteAssetType = async (id) => {
    if (!window.confirm('Are you sure you want to delete this asset type?')) return;
    
    try {
      await axios.delete(`${API}/asset-types/${id}`);
      setAssetTypes(assetTypes.filter(at => at.id !== id));
      toast.success('Asset type deleted successfully');
    } catch (error) {
      console.error('Error deleting asset type:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete asset type');
    }
  };

  // Filter asset types first
  const filteredAssetTypes = assetTypes.filter(assetType => {
    const matchesSearch = assetType.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         assetType.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || assetType.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Apply pagination to filtered results
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedAssetTypes = filteredAssetTypes.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Reset to first page when search or filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter]);

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
          <h1 className="text-3xl font-bold text-gray-900">Asset Types</h1>
          <p className="text-gray-600 mt-1">Manage your organization's asset type definitions</p>
        </div>

        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="mr-2 h-4 w-4" />
              Add Asset Type
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create New Asset Type</DialogTitle>
            </DialogHeader>
            <AssetTypeForm onSubmit={handleCreateAssetType} assetManagers={assetManagers} />
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search asset types..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Active">Active</SelectItem>
                  <SelectItem value="Inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Asset Types Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <Package className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>Asset Types ({filteredAssetTypes.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {filteredAssetTypes.length === 0 ? (
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No asset types found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Get started by creating your first asset type.'
                }
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Depreciation</TableHead>
                      <TableHead>Asset Life</TableHead>
                      <TableHead>Recovery Required</TableHead>
                      <TableHead>Assigned Asset Manager</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedAssetTypes.map((assetType) => (
                      <TableRow key={assetType.id}>
                        <TableCell className="font-medium">{assetType.code}</TableCell>
                        <TableCell>{assetType.name}</TableCell>
                        <TableCell>
                          <Badge variant={assetType.depreciation_applicable ? "default" : "secondary"}>
                            {assetType.depreciation_applicable ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {assetType.depreciation_applicable 
                            ? `${assetType.asset_life} years` 
                            : 'N/A'
                          }
                        </TableCell>
                        <TableCell>
                          <Badge variant={assetType.to_be_recovered_on_separation ? "default" : "secondary"}>
                            {assetType.to_be_recovered_on_separation ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {assetType.assigned_asset_manager_name ? (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                              {assetType.assigned_asset_manager_name}
                            </Badge>
                          ) : (
                            <span className="text-gray-500 text-sm">Not Assigned</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={assetType.status === 'Active' ? "default" : "secondary"}
                            className={assetType.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
                          >
                            {assetType.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedAssetType(assetType);
                                setIsEditModalOpen(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteAssetType(assetType.id)}
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
              
              {/* Pagination */}
              <DataPagination
                currentPage={currentPage}
                totalPages={Math.ceil(filteredAssetTypes.length / itemsPerPage)}
                totalItems={filteredAssetTypes.length}
                itemsPerPage={itemsPerPage}
                onPageChange={handlePageChange}
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* Edit Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Asset Type</DialogTitle>
          </DialogHeader>
          {selectedAssetType && (
            <AssetTypeForm 
              initialData={selectedAssetType}
              onSubmit={(formData) => handleUpdateAssetType(selectedAssetType.id, formData)}
              assetManagers={assetManagers}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

const AssetTypeForm = ({ initialData, onSubmit, assetManagers = [] }) => {
  const [formData, setFormData] = useState({
    code: initialData?.code || '',
    name: initialData?.name || '',
    depreciation_applicable: initialData?.depreciation_applicable ?? true,
    asset_life: initialData?.asset_life || '',
    to_be_recovered_on_separation: initialData?.to_be_recovered_on_separation ?? true,
    status: initialData?.status || 'Active',
    assigned_asset_manager_id: initialData?.assigned_asset_manager_id || 'none'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const submitData = {
      ...formData,
      asset_life: formData.depreciation_applicable && formData.asset_life 
        ? parseInt(formData.asset_life) 
        : null,
      assigned_asset_manager_id: formData.assigned_asset_manager_id === 'none' ? null : formData.assigned_asset_manager_id
    };

    await onSubmit(submitData);
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="code">Code *</Label>
          <Input
            id="code"
            value={formData.code}
            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            placeholder="Enter asset type code"
            required
          />
        </div>
        <div>
          <Label htmlFor="status">Status</Label>
          <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Active">Active</SelectItem>
              <SelectItem value="Inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="name">Name *</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Enter asset type name"
          required
        />
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="depreciation"
          checked={formData.depreciation_applicable}
          onCheckedChange={(checked) => setFormData({ 
            ...formData, 
            depreciation_applicable: checked,
            asset_life: checked ? formData.asset_life : ''
          })}
        />
        <Label htmlFor="depreciation">Depreciation Applicable</Label>
      </div>

      {formData.depreciation_applicable && (
        <div>
          <Label htmlFor="asset_life">Asset Life (Years) *</Label>
          <Input
            id="asset_life"
            type="number"
            value={formData.asset_life}
            onChange={(e) => setFormData({ ...formData, asset_life: e.target.value })}
            placeholder="Enter asset life in years"
            required
            min="1"
          />
        </div>
      )}

      <div>
        <Label htmlFor="assigned_asset_manager">Assigned Asset Manager</Label>
        <Select 
          value={formData.assigned_asset_manager_id} 
          onValueChange={(value) => setFormData({ ...formData, assigned_asset_manager_id: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select an Asset Manager (Optional)" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No Asset Manager Assigned</SelectItem>
            {assetManagers.map(manager => (
              <SelectItem key={manager.id} value={manager.id}>
                {manager.name} ({manager.email})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-sm text-gray-500 mt-1">
          Asset requests for this type will be routed to the selected Asset Manager
        </p>
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="recovery"
          checked={formData.to_be_recovered_on_separation}
          onCheckedChange={(checked) => setFormData({ ...formData, to_be_recovered_on_separation: checked })}
        />
        <Label htmlFor="recovery">To be recovered on separation</Label>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
          {loading ? 'Saving...' : (initialData ? 'Update' : 'Create')}
        </Button>
      </div>
    </form>
  );
};

export default AssetTypes;