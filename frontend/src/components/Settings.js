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
      const response = await axios.get(`${API}/email-config`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setEmailConfig(response.data);
      setEmailConfigExists(true);
      setEmailConfigId(response.data.id);
    } catch (error) {
      if (error.response?.status === 404) {
        setEmailConfigExists(false);
      } else {
        console.error('Error fetching email configuration:', error);
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

      const response = emailConfigExists 
        ? await axios.put(`${API}/email-config/${emailConfigId}`, submitData, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          })
        : await axios.post(`${API}/email-config`, submitData, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });

      setEmailConfig(response.data);
      setEmailConfigExists(true);
      setEmailConfigId(response.data.id);
      toast.success(emailConfigExists ? 'Email configuration updated successfully' : 'Email configuration created successfully');
    } catch (error) {
      console.error('Error saving email configuration:', error);
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
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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
                  user?.role === 'Administrator' ? 'bg-purple-100 text-purple-800' :
                  user?.role === 'HR Manager' ? 'bg-blue-100 text-blue-800' :
                  user?.role === 'Manager' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {user?.role}
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
    </div>
  );
};

export default Settings;