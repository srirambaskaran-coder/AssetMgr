import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import { 
  Upload, 
  Download, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  Info
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BulkImport = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setImportResult(null);
      } else {
        toast.error('Please select a CSV file');
        event.target.value = '';
      }
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await axios.get(`${API}/asset-definitions/template`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'asset_definitions_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Template downloaded successfully');
    } catch (error) {
      console.error('Error downloading template:', error);
      toast.error('Failed to download template');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file to upload');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await axios.post(`${API}/asset-definitions/bulk-import`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setImportResult(response.data);
      
      if (response.data.success) {
        toast.success(`Import completed! ${response.data.successful_imports} assets imported successfully.`);
      } else {
        toast.error('Import completed with errors. Please check the results below.');
      }
      
      // Reset file input
      setSelectedFile(null);
      const fileInput = document.getElementById('file-upload');
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
      setImportResult(null);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Bulk Asset Import</h1>
        <p className="text-gray-600 mt-1">Import multiple asset definitions from CSV files</p>
      </div>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <div className="flex items-center">
            <Info className="mr-2 h-5 w-5 text-blue-600" />
            <CardTitle>How to Use Bulk Import</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-sm">1</span>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Download Template</h4>
                <p className="text-sm text-gray-600">Get the CSV template with required columns and sample data</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-sm">2</span>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Fill Your Data</h4>
                <p className="text-sm text-gray-600">Add your asset information following the template format</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-sm">3</span>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Upload & Import</h4>
                <p className="text-sm text-gray-600">Upload your completed CSV file to import assets</p>
              </div>
            </div>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Important:</strong> Make sure your asset type codes exist in the system before importing. 
              Asset codes must be unique across all assets.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Download Template */}
      <Card>
        <CardHeader>
          <CardTitle>Step 1: Download Template</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-green-600" />
              <div>
                <h4 className="font-medium text-gray-900">Asset Definitions Template</h4>
                <p className="text-sm text-gray-600">CSV template with sample data and required columns</p>
              </div>
            </div>
            <Button onClick={downloadTemplate} variant="outline" className="flex items-center">
              <Download className="mr-2 h-4 w-4" />
              Download Template
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* File Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Step 2: Upload Your CSV File</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="file-upload">Choose CSV File</Label>
            <Input
              id="file-upload"
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="mt-1"
            />
          </div>

          {selectedFile && (
            <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <FileText className="h-6 w-6 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-900">{selectedFile.name}</p>
                  <p className="text-sm text-blue-600">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <Button 
                onClick={handleUpload} 
                disabled={uploading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {uploading ? (
                  <>
                    <Upload className="mr-2 h-4 w-4 animate-pulse" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Import Assets
                  </>
                )}
              </Button>
            </div>
          )}

          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Uploading and processing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Import Results */}
      {importResult && (
        <Card>
          <CardHeader>
            <div className="flex items-center">
              {importResult.success ? (
                <CheckCircle className="mr-2 h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="mr-2 h-5 w-5 text-red-600" />
              )}
              <CardTitle>Import Results</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{importResult.total_rows}</div>
                <div className="text-sm text-gray-600">Total Rows</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{importResult.successful_imports}</div>
                <div className="text-sm text-green-600">Successful</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{importResult.failed_imports}</div>
                <div className="text-sm text-red-600">Failed</div>
              </div>
            </div>

            <Alert className={importResult.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
              <AlertDescription className={importResult.success ? "text-green-800" : "text-red-800"}>
                {importResult.message}
              </AlertDescription>
            </Alert>

            {importResult.errors && importResult.errors.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Import Errors:</h4>
                <div className="max-h-60 overflow-y-auto space-y-2">
                  {importResult.errors.map((error, index) => (
                    <div key={index} className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                      <span className="font-medium text-red-800">Row {error.row}:</span>
                      <span className="text-red-700 ml-2">{error.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BulkImport;