import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Switch } from './ui/switch';
import { toast } from 'sonner';
import { 
  Settings as SettingsIcon, 
  Lock, 
  User, 
  Eye, 
  EyeOff,
  CheckCircle,
  Mail,
  Server,
  Send,
  AlertCircle
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Settings = () => {
  const { user } = useAuth();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    feedback: ''
  });

  // Email configuration state
  const [emailConfig, setEmailConfig] = useState({
    smtp_server: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    use_tls: true,
    use_ssl: false,
    from_email: '',
    from_name: ''
  });
  const [emailConfigExists, setEmailConfigExists] = useState(false);
  const [emailConfigId, setEmailConfigId] = useState(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [testEmailLoading, setTestEmailLoading] = useState(false);
  const [showEmailPassword, setShowEmailPassword] = useState(false);

  useEffect(() => {
    if (user?.roles?.includes('Administrator')) {
      fetchEmailConfiguration();
    }
  }, [user]);

  const fetchEmailConfiguration = async () => {
    try {
      console.log('🔍 Fetching Email Config:');
      console.log('API URL:', `${API}/email-config`);
      console.log('Session Token:', localStorage.getItem('session_token'));

      const response = await axios.get(`${API}/email-config`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });
      
      console.log('✅ Fetch Success:', response.data);
      setEmailConfig(response.data);
      setEmailConfigExists(true);
      setEmailConfigId(response.data.id);
    } catch (error) {
      console.error('🚨 Fetch Email Config Error:', error);
      console.error('Response Status:', error.response?.status);
      console.error('Response Data:', error.response?.data);
      
      if (error.response?.status === 404) {
        setEmailConfigExists(false);
        console.log('ℹ️ No email configuration found (expected)');
      } else {
        console.error('❌ Unexpected error fetching email configuration:', error);
      }
    }
  };

  const handleEmailConfigChange = (field, value) => {
    setEmailConfig({ ...emailConfig, [field]: value });
  };

  const handleEmailConfigSubmit = async (e) => {
    e.preventDefault();
    setEmailLoading(true);

    try {
      const submitData = { ...emailConfig };
      // If password is masked, don't send it
      if (submitData.smtp_password === '***masked***') {
        delete submitData.smtp_password;
      }

      console.log('🔍 Frontend Debug Info:');
      console.log('API URL:', API);
      console.log('Session Token:', localStorage.getItem('session_token'));
      console.log('Token (legacy):', localStorage.getItem('token'));
      console.log('Submit Data:', submitData);
      console.log('Email Config Exists:', emailConfigExists);
      console.log('Email Config ID:', emailConfigId);

      const response = emailConfigExists 
        ? await axios.put(`${API}/email-config/${emailConfigId}`, submitData, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('session_token')}`
            }
          })
        : await axios.post(`${API}/email-config`, submitData, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('session_token')}`
            }
          });

      setEmailConfig(response.data);
      setEmailConfigExists(true);
      setEmailConfigId(response.data.id);
      toast.success(emailConfigExists ? 'Email configuration updated successfully' : 'Email configuration created successfully');
    } catch (error) {
      console.error('🚨 Email Configuration Error:', error);
      console.error('Error Message:', error.message);
      console.error('Response:', error.response);
      console.error('Response Data:', error.response?.data);
      console.error('Response Status:', error.response?.status);
      console.error('Response Headers:', error.response?.headers);
      console.error('Request Config:', error.config);
      
      // More detailed error analysis
      if (error.response?.data?.detail) {
        console.error('Backend Error Detail:', error.response.data.detail);
      }
      
      if (error.response?.status === 422) {
        console.error('Validation Error - Check your input data');
        if (error.response.data?.detail) {
          console.error('Validation Details:', JSON.stringify(error.response.data.detail, null, 2));
        }
      }
      
      toast.error(error.response?.data?.detail || 'Failed to save email configuration');
    } finally {
      setEmailLoading(false);
    }
  };

  const handleTestEmail = async () => {
    if (!emailConfigExists) {
      toast.error('Please save email configuration first');
      return;
    }

    setTestEmailLoading(true);
    try {
      await axios.post(`${API}/email-config/test`, {
        test_email: user.email
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });

      toast.success(`Test email sent successfully to ${user.email}`);
    } catch (error) {
      console.error('Error sending test email:', error);
      toast.error(error.response?.data?.detail || 'Failed to send test email');
    } finally {
      setTestEmailLoading(false);
    }
  };

  const calculatePasswordStrength = (password) => {
    let score = 0;
    let feedback = [];

    if (password.length >= 8) score += 1;
    else feedback.push('At least 8 characters');

    if (/[a-z]/.test(password)) score += 1;
    else feedback.push('Lowercase letter');

    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push('Uppercase letter');

    if (/[0-9]/.test(password)) score += 1;
    else feedback.push('Number');

    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    else feedback.push('Special character');

    return {
      score,
      feedback: feedback.length > 0 ? `Missing: ${feedback.join(', ')}` : 'Strong password!'
    };
  };

  const handlePasswordChange = (field, value) => {
    setPasswordData({ ...passwordData, [field]: value });
    
    if (field === 'new_password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 6) {
      toast.error('New password must be at least 6 characters long');
      return;
    }

    setLoading(true);

    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });

      toast.success('Password changed successfully');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setPasswordStrength({ score: 0, feedback: '' });
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = (score) => {
    if (score <= 2) return 'bg-red-500';
    if (score <= 3) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStrengthText = (score) => {
    if (score <= 2) return 'Weak';
    if (score <= 3) return 'Medium';
    return 'Strong';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account settings and security</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Information */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <div className="flex items-center">
              <User className="mr-2 h-5 w-5 text-blue-600" />
              <CardTitle>Profile Information</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl font-bold">
                  {user?.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </span>
              </div>
              <h3 className="text-lg font-medium text-gray-900">{user?.name}</h3>
              <p className="text-gray-600">{user?.email}</p>
              <div className="mt-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user?.roles?.includes('Administrator') ? 'bg-purple-100 text-purple-800' :
                  user?.roles?.includes('HR Manager') ? 'bg-blue-100 text-blue-800' :
                  user?.roles?.includes('Manager') ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {user?.roles?.[0] || user?.role}
                </span>
              </div>
            </div>
            
            <div className="pt-4 border-t">
              <div className="text-sm text-gray-600">
                <p><strong>Member since:</strong> {new Date(user?.created_at).toLocaleDateString()}</p>
                <p><strong>Status:</strong> 
                  <span className="text-green-600 ml-1">Active</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center">
              <Lock className="mr-2 h-5 w-5 text-blue-600" />
              <CardTitle>Change Password</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="current_password">Current Password</Label>
                <div className="relative">
                  <Input
                    id="current_password"
                    type={showCurrentPassword ? 'text' : 'password'}
                    value={passwordData.current_password}
                    onChange={(e) => handlePasswordChange('current_password', e.target.value)}
                    placeholder="Enter your current password"
                    required
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  >
                    {showCurrentPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <Label htmlFor="new_password">New Password</Label>
                <div className="relative">
                  <Input
                    id="new_password"
                    type={showNewPassword ? 'text' : 'password'}
                    value={passwordData.new_password}
                    onChange={(e) => handlePasswordChange('new_password', e.target.value)}
                    placeholder="Enter your new password"
                    required
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                
                {passwordData.new_password && (
                  <div className="mt-2 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Password strength:</span>
                      <span className={`font-medium ${
                        passwordStrength.score <= 2 ? 'text-red-600' :
                        passwordStrength.score <= 3 ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {getStrengthText(passwordStrength.score)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${getStrengthColor(passwordStrength.score)}`}
                        style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-600">{passwordStrength.feedback}</p>
                  </div>
                )}
              </div>

              <div>
                <Label htmlFor="confirm_password">Confirm New Password</Label>
                <div className="relative">
                  <Input
                    id="confirm_password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={passwordData.confirm_password}
                    onChange={(e) => handlePasswordChange('confirm_password', e.target.value)}
                    placeholder="Confirm your new password"
                    required
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                
                {passwordData.confirm_password && (
                  <div className="mt-1 flex items-center">
                    {passwordData.new_password === passwordData.confirm_password ? (
                      <div className="flex items-center text-green-600 text-sm">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Passwords match
                      </div>
                    ) : (
                      <div className="text-red-600 text-sm">
                        Passwords do not match
                      </div>
                    )}
                  </div>
                )}
              </div>

              <Alert>
                <AlertDescription>
                  <strong>Security Tips:</strong>
                  <ul className="mt-2 text-sm list-disc list-inside space-y-1">
                    <li>Use a combination of uppercase and lowercase letters</li>
                    <li>Include numbers and special characters</li>
                    <li>Avoid using personal information</li>
                    <li>Use a unique password not used elsewhere</li>
                  </ul>
                </AlertDescription>
              </Alert>

              <div className="flex justify-end pt-4">
                <Button 
                  type="submit" 
                  disabled={loading || passwordData.new_password !== passwordData.confirm_password}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {loading ? 'Changing Password...' : 'Change Password'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Email Configuration - Administrator Only */}
      {user?.roles?.includes('Administrator') && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Mail className="mr-2 h-5 w-5 text-blue-600" />
                <CardTitle>Email Configuration</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleTestEmail}
                  disabled={!emailConfigExists || testEmailLoading}
                >
                  <Send className="mr-2 h-4 w-4" />
                  {testEmailLoading ? 'Sending...' : 'Send Test Email'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEmailConfigSubmit} className="space-y-4">
              <Alert>
                <Server className="h-4 w-4" />
                <AlertDescription>
                  Configure SMTP server settings to enable email notifications for asset management activities.
                </AlertDescription>
              </Alert>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="smtp_server">SMTP Server *</Label>
                  <Input
                    id="smtp_server"
                    type="text"
                    value={emailConfig.smtp_server}
                    onChange={(e) => handleEmailConfigChange('smtp_server', e.target.value)}
                    placeholder="smtp.gmail.com"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="smtp_port">SMTP Port *</Label>
                  <Input
                    id="smtp_port"
                    type="number"
                    value={emailConfig.smtp_port}
                    onChange={(e) => handleEmailConfigChange('smtp_port', parseInt(e.target.value))}
                    placeholder="587"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="smtp_username">SMTP Username *</Label>
                  <Input
                    id="smtp_username"
                    type="text"
                    value={emailConfig.smtp_username}
                    onChange={(e) => handleEmailConfigChange('smtp_username', e.target.value)}
                    placeholder="your-email@domain.com"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="smtp_password">SMTP Password *</Label>
                  <div className="relative">
                    <Input
                      id="smtp_password"
                      type={showEmailPassword ? 'text' : 'password'}
                      value={emailConfig.smtp_password}
                      onChange={(e) => handleEmailConfigChange('smtp_password', e.target.value)}
                      placeholder="Enter SMTP password"
                      required={!emailConfigExists}
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowEmailPassword(!showEmailPassword)}
                    >
                      {showEmailPassword ? (
                        <EyeOff className="h-4 w-4 text-gray-400" />
                      ) : (
                        <Eye className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  <Label htmlFor="from_email">From Email *</Label>
                  <Input
                    id="from_email"
                    type="email"
                    value={emailConfig.from_email}
                    onChange={(e) => handleEmailConfigChange('from_email', e.target.value)}
                    placeholder="noreply@company.com"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="from_name">From Name *</Label>
                  <Input
                    id="from_name"
                    type="text"
                    value={emailConfig.from_name}
                    onChange={(e) => handleEmailConfigChange('from_name', e.target.value)}
                    placeholder="Asset Management System"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="use_tls"
                    checked={emailConfig.use_tls}
                    onCheckedChange={(checked) => handleEmailConfigChange('use_tls', checked)}
                  />
                  <Label htmlFor="use_tls">Use TLS (Port 587)</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="use_ssl"
                    checked={emailConfig.use_ssl}
                    onCheckedChange={(checked) => handleEmailConfigChange('use_ssl', checked)}
                  />
                  <Label htmlFor="use_ssl">Use SSL (Port 465)</Label>
                </div>
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Common SMTP Settings:</strong>
                  <ul className="mt-2 text-sm list-disc list-inside space-y-1">
                    <li><strong>Gmail:</strong> smtp.gmail.com, Port 587 (TLS) or 465 (SSL)</li>
                    <li><strong>Outlook:</strong> smtp-mail.outlook.com, Port 587 (TLS)</li>
                    <li><strong>Yahoo:</strong> smtp.mail.yahoo.com, Port 587 (TLS) or 465 (SSL)</li>
                  </ul>
                </AlertDescription>
              </Alert>

              <div className="flex justify-end pt-4">
                <Button 
                  type="submit" 
                  disabled={emailLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {emailLoading ? 'Saving...' : (emailConfigExists ? 'Update Configuration' : 'Save Configuration')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Asset System Reset - Administrator Only */}
        <Card className="border-red-200">
          <CardHeader>
            <div className="flex items-center">
              <AlertCircle className="mr-2 h-5 w-5 text-red-600" />
              <CardTitle className="text-red-700">Danger Zone - Asset System Reset</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                <strong>WARNING:</strong> This action will permanently delete ALL asset management data including:
                <ul className="mt-2 text-sm list-disc list-inside space-y-1">
                  <li>All Asset Types and Asset Definitions</li>
                  <li>All Asset Requisitions and Allocations</li>
                  <li>All Asset Retrievals and NDC Requests</li>
                  <li>All user asset assignments and history</li>
                </ul>
                <strong>This action cannot be undone!</strong>
              </AlertDescription>
            </Alert>

            <div className="flex justify-end pt-4">
              <AssetSystemResetButton />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Asset System Reset Button Component
const AssetSystemResetButton = () => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmationText, setConfirmationText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleResetSystem = async () => {
    if (confirmationText !== 'DELETE ALL ASSETS') {
      toast.error('Please type "DELETE ALL ASSETS" to confirm');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/reset-asset-system`, {}, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });

      toast.success('Asset system has been completely reset');
      console.log('Reset Summary:', response.data.deletion_summary);
      
      // Reset form
      setShowConfirmDialog(false);
      setConfirmationText('');
      
      // Optionally refresh the page to reflect changes
      setTimeout(() => {
        window.location.reload();
      }, 2000);

    } catch (error) {
      console.error('Error resetting asset system:', error);
      if (error.response?.status === 403) {
        toast.error('Access denied. Administrator role required.');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to reset asset system');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="destructive"
        onClick={() => setShowConfirmDialog(true)}
        className="bg-red-600 hover:bg-red-700"
      >
        <AlertCircle className="mr-2 h-4 w-4" />
        Reset Asset System
      </Button>

      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <AlertCircle className="mr-2 h-6 w-6 text-red-600" />
              <h3 className="text-lg font-semibold text-red-700">Confirm Asset System Reset</h3>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-4">
                This will permanently delete ALL asset management data. This action cannot be undone.
              </p>
              
              <p className="text-sm font-medium text-red-700 mb-2">
                Type "DELETE ALL ASSETS" to confirm:
              </p>
              
              <Input
                value={confirmationText}
                onChange={(e) => setConfirmationText(e.target.value)}
                placeholder="DELETE ALL ASSETS"
                className="border-red-300 focus:border-red-500"
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowConfirmDialog(false);
                  setConfirmationText('');
                }}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleResetSystem}
                disabled={loading || confirmationText !== 'DELETE ALL ASSETS'}
                className="bg-red-600 hover:bg-red-700"
              >
                {loading ? 'Resetting...' : 'Reset Asset System'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Settings;