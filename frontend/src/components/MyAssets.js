import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { useRole } from '../contexts/RoleContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { DataPagination } from './ui/data-pagination';
import { toast } from 'sonner';
import { 
  Package,
  Calendar,
  CheckCircle,
  Clock,
  User,
  FileText,
  AlertCircle,
  IndianRupee
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyAssets = () => {
  const { user } = useAuth();
  const { activeRole } = useRole();
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [isAckModalOpen, setIsAckModalOpen] = useState(false);
  const [acknowledgmentNotes, setAcknowledgmentNotes] = useState('');
  const [acknowledging, setAcknowledging] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchMyAssets();
  }, []);

  const fetchMyAssets = async () => {
    try {
      const response = await axios.get(`${API}/my-allocated-assets`);
      setAssets(response.data);
    } catch (error) {
      console.error('Error fetching my assets:', error);
      toast.error('Failed to load your allocated assets');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledgeAsset = async () => {
    if (!selectedAsset) return;

    setAcknowledging(true);
    try {
      await axios.post(`${API}/asset-definitions/${selectedAsset.id}/acknowledge`, {
        acknowledgment_notes: acknowledgmentNotes
      });

      toast.success('Asset allocation acknowledged successfully');
      setIsAckModalOpen(false);
      setSelectedAsset(null);
      setAcknowledgmentNotes('');
      await fetchMyAssets(); // Refresh the list
    } catch (error) {
      console.error('Error acknowledging asset:', error);
      toast.error(error.response?.data?.detail || 'Failed to acknowledge asset allocation');
    } finally {
      setAcknowledging(false);
    }
  };

  const openAcknowledgmentModal = (asset) => {
    setSelectedAsset(asset);
    setAcknowledgmentNotes('');
    setIsAckModalOpen(true);
  };

  const getStatusBadge = (asset) => {
    if (asset.acknowledged) {
      return (
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="h-3 w-3 mr-1" />
          Acknowledged
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-yellow-100 text-yellow-800">
          <Clock className="h-3 w-3 mr-1" />
          Acknowledgment Pending
        </Badge>
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Pagination logic
  const totalItems = assets.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedAssets = assets.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Allocated Assets</h1>
          <p className="text-gray-600 mt-1">View and acknowledge your allocated assets</p>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Allocated</p>
                <p className="text-2xl font-bold text-gray-900">{assets.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Acknowledged</p>
                <p className="text-2xl font-bold text-gray-900">
                  {assets.filter(asset => asset.acknowledged).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending Acknowledgment</p>
                <p className="text-2xl font-bold text-gray-900">
                  {assets.filter(asset => !asset.acknowledged).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Assets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Your Allocated Assets</CardTitle>
        </CardHeader>
        <CardContent>
          {assets.length === 0 ? (
            <div className="text-center py-8">
              <Package className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No assets allocated to you</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset Code</TableHead>
                    <TableHead>Asset Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Allocation Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {assets.map((asset) => (
                    <TableRow key={asset.id}>
                      <TableCell className="font-medium">{asset.asset_code}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {asset.asset_type_name}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{asset.asset_description}</div>
                          <div className="text-sm text-gray-500">{asset.asset_details}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {asset.asset_value && (
                          <div className="flex items-center">
                            <IndianRupee className="h-4 w-4 mr-1 text-gray-500" />
                            ₹{asset.asset_value.toLocaleString()}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {asset.allocation_date && (
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1 text-gray-500" />
                            {new Date(asset.allocation_date).toLocaleDateString()}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(asset)}
                      </TableCell>
                      <TableCell className="text-right">
                        {!asset.acknowledged ? (
                          <Button
                            size="sm"
                            onClick={() => openAcknowledgmentModal(asset)}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Acknowledge
                          </Button>
                        ) : (
                          <div className="text-sm text-gray-500">
                            <div>Acknowledged on</div>
                            <div>{new Date(asset.acknowledgment_date).toLocaleDateString()}</div>
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

      {/* Acknowledgment Modal */}
      <Dialog open={isAckModalOpen} onOpenChange={setIsAckModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Acknowledge Asset Allocation</DialogTitle>
          </DialogHeader>
          
          {selectedAsset && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900">{selectedAsset.asset_code}</h4>
                <p className="text-sm text-gray-600">{selectedAsset.asset_description}</p>
                <p className="text-sm text-gray-500 mt-1">{selectedAsset.asset_details}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Acknowledgment Notes (Optional)
                </label>
                <Textarea
                  value={acknowledgmentNotes}
                  onChange={(e) => setAcknowledgmentNotes(e.target.value)}
                  placeholder="Any comments about the asset condition or receipt..."
                  className="w-full"
                  rows={3}
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsAckModalOpen(false)}
                  disabled={acknowledging}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAcknowledgeAsset}
                  disabled={acknowledging}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {acknowledging ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Acknowledging...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Acknowledge Receipt
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MyAssets;