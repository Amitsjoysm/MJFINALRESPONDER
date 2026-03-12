import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { User, Mail, Calendar, Activity } from 'lucide-react';

const Profile = () => {
  const { user } = useAuth();
  const [quota, setQuota] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuota();
  }, []);

  const loadQuota = async () => {
    try {
      const data = await API.getQuota();
      setQuota(data);
    } catch (error) {
      toast.error('Failed to load quota information');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600 mt-1">Manage your account settings and preferences</p>
      </div>

      {/* User Info Card */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center">
              <User className="w-10 h-10 text-white" />
            </div>
            <div>
              <CardTitle className="text-2xl">{user?.full_name || 'User'}</CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1 text-base">
                <Mail className="w-4 h-4" />
                {user?.email}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Account Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5 text-purple-600" />
              Account Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-700">Full Name</Label>
              <Input value={user?.full_name || ''} disabled className="mt-1" />
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-700">Email Address</Label>
              <Input value={user?.email || ''} disabled className="mt-1" />
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-700">Account ID</Label>
              <Input value={user?.id || ''} disabled className="mt-1 font-mono text-xs" />
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-700">Member Since</Label>
              <Input 
                value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'} 
                disabled 
                className="mt-1" 
              />
            </div>
          </CardContent>
        </Card>

        {/* Quota Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-600" />
              Usage & Quota
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <Label className="text-sm font-medium text-gray-700">Daily Quota</Label>
                <span className="text-sm font-bold text-gray-900">
                  {quota?.used || user?.quota_used || 0} / {quota?.limit || user?.quota || 100}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-purple-600 to-pink-600 h-3 rounded-full transition-all"
                  style={{ 
                    width: `${Math.min(((quota?.used || user?.quota_used || 0) / (quota?.limit || user?.quota || 100)) * 100, 100)}%` 
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs text-blue-600 font-medium uppercase">Emails Processed</p>
                <p className="text-2xl font-bold text-blue-900 mt-1">
                  {quota?.used || user?.quota_used || 0}
                </p>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-xs text-green-600 font-medium uppercase">Remaining</p>
                <p className="text-2xl font-bold text-green-900 mt-1">
                  {(quota?.limit || user?.quota || 100) - (quota?.used || user?.quota_used || 0)}
                </p>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs text-amber-800">
                <strong>Note:</strong> Your quota resets daily at midnight UTC
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Security Card */}
      <Card>
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription>Manage your account security settings</CardDescription>
        </CardHeader>
        <CardContent>
          <Button disabled variant="outline">
            Change Password (Coming Soon)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Profile;