import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { 
  Building, 
  Mail, 
  Phone, 
  Globe, 
  MapPin,
  Save,
  Upload,
  Camera
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CompanyProfile = () => {
  const [profile, setProfile] = useState({
    company_name: '',
    company_address: '',
    company_phone: '',
    company_email: '',
    company_website: '',
    company_logo: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchCompanyProfile();
  }, []);

  const fetchCompanyProfile = async () => {
    try {
      const response = await axios.get(`${API}/company-profile`);
      setProfile(response.data);
    } catch (error) {
      console.error('Error fetching company profile:', error);
      toast.error('Failed to load company profile');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setProfile({ ...profile, [field]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const response = await axios.put(`${API}/company-profile`, profile);
      setProfile(response.data);
      setIsEditing(false);
      toast.success('Company profile updated successfully');
    } catch (error) {
      console.error('Error updating company profile:', error);
      toast.error(error.response?.data?.detail || 'Failed to update company profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    fetchCompanyProfile(); // Reset to original data
    setIsEditing(false);
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
          <h1 className="text-3xl font-bold text-gray-900">Company Profile</h1>
          <p className="text-gray-600 mt-1">Manage your organization's information and branding</p>
        </div>
        
        {!isEditing ? (
          <Button 
            onClick={() => setIsEditing(true)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Edit Profile
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button 
              variant="outline"
              onClick={handleCancel}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Save className="mr-2 h-4 w-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Company Logo and Basic Info */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Company Logo & Identity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className="relative">
                {profile.company_logo ? (
                  <img 
                    src={profile.company_logo} 
                    alt="Company Logo" 
                    className="w-32 h-32 object-contain mx-auto rounded-lg border border-gray-200"
                  />
                ) : (
                  <div className="w-32 h-32 bg-gray-100 rounded-lg flex items-center justify-center mx-auto">
                    <Building className="h-16 w-16 text-gray-400" />
                  </div>
                )}
                
                {isEditing && (
                  <div className="absolute bottom-0 right-0 transform translate-x-1/4 translate-y-1/4">
                    <Button size="sm" className="rounded-full p-2 bg-blue-600 hover:bg-blue-700">
                      <Camera className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
              
              <div className="mt-4 text-center">
                <h3 className="text-xl font-bold text-gray-900">
                  {profile.company_name || 'Your Company Name'}
                </h3>
                {profile.company_website && (
                  <a 
                    href={profile.company_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm flex items-center justify-center mt-1"
                  >
                    <Globe className="h-4 w-4 mr-1" />
                    Visit Website
                  </a>
                )}
              </div>
            </div>

            {isEditing && (
              <div>
                <Label htmlFor="company_logo">Logo URL</Label>
                <div className="flex space-x-2">
                  <Input
                    id="company_logo"
                    value={profile.company_logo}
                    onChange={(e) => handleInputChange('company_logo', e.target.value)}
                    placeholder="Enter logo URL or upload image"
                  />
                  <Button variant="outline" size="sm">
                    <Upload className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Company Details Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Company Information</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company_name">Company Name *</Label>
                  <Input
                    id="company_name"
                    value={profile.company_name}
                    onChange={(e) => handleInputChange('company_name', e.target.value)}
                    placeholder="Enter company name"
                    disabled={!isEditing}
                    required
                  />
                </div>
                
                <div>
                  <Label htmlFor="company_website">Website</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      id="company_website"
                      value={profile.company_website}
                      onChange={(e) => handleInputChange('company_website', e.target.value)}
                      placeholder="https://www.yourcompany.com"
                      disabled={!isEditing}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>

              <div>
                <Label htmlFor="company_address">Address</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 text-gray-400 h-4 w-4" />
                  <Textarea
                    id="company_address"
                    value={profile.company_address}
                    onChange={(e) => handleInputChange('company_address', e.target.value)}
                    placeholder="Enter complete company address"
                    disabled={!isEditing}
                    rows={3}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company_email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      id="company_email"
                      type="email"
                      value={profile.company_email}
                      onChange={(e) => handleInputChange('company_email', e.target.value)}
                      placeholder="contact@yourcompany.com"
                      disabled={!isEditing}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="company_phone">Phone</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      id="company_phone"
                      value={profile.company_phone}
                      onChange={(e) => handleInputChange('company_phone', e.target.value)}
                      placeholder="+1 (555) 123-4567"
                      disabled={!isEditing}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>

              {/* Additional Info Display */}
              {!isEditing && (
                <div className="pt-6 border-t border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                      <strong>Profile Created:</strong> {new Date(profile.created_at).toLocaleDateString()}
                    </div>
                    <div>
                      <strong>Last Updated:</strong> {new Date(profile.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              )}
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6">
            <div className="flex items-center space-x-4">
              {profile.company_logo ? (
                <img 
                  src={profile.company_logo} 
                  alt="Company Logo" 
                  className="w-16 h-16 object-contain rounded"
                />
              ) : (
                <div className="w-16 h-16 bg-white rounded flex items-center justify-center">
                  <Building className="h-8 w-8 text-blue-600" />
                </div>
              )}
              
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900">
                  {profile.company_name || 'Your Company Name'}
                </h3>
                {profile.company_address && (
                  <p className="text-gray-600 text-sm mt-1">{profile.company_address}</p>
                )}
                
                <div className="flex flex-wrap gap-4 mt-2">
                  {profile.company_email && (
                    <span className="text-blue-600 text-sm flex items-center">
                      <Mail className="h-3 w-3 mr-1" />
                      {profile.company_email}
                    </span>
                  )}
                  {profile.company_phone && (
                    <span className="text-blue-600 text-sm flex items-center">
                      <Phone className="h-3 w-3 mr-1" />
                      {profile.company_phone}
                    </span>
                  )}
                  {profile.company_website && (
                    <span className="text-blue-600 text-sm flex items-center">
                      <Globe className="h-3 w-3 mr-1" />
                      {profile.company_website}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompanyProfile;