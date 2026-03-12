import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';
import { Calendar, Plus, CheckCircle2, RefreshCw, Trash2, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner'; 

// Google Icon Component
const GoogleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

// Outlook Icon Component
const OutlookIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path fill="#0078D4" d="M24 7.6V4.8c0-.663-.537-1.2-1.2-1.2h-9.6V1.2c0-.663-.537-1.2-1.2-1.2H1.2C.537 0 0 .537 0 1.2v21.6c0 .663.537 1.2 1.2 1.2h10.8c.663 0 1.2-.537 1.2-1.2v-2.4h9.6c.663 0 1.2-.537 1.2-1.2V7.6zM6 6c2.21 0 4 2.015 4 4.5S8.21 15 6 15s-4-2.015-4-4.5S3.79 6 6 6zm8.4 12H1.2V1.2h10.8v20.4zm8.4-1.2h-7.2V8.4h7.2v8.4z"/>
  </svg>
);

const CalendarProviders = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams(); 
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const apiUrl = import.meta.env.VITE_API_URL || process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchProviders();
    // ✅ ADDED: Check for OAuth success/error
    const success = searchParams.get('success');
    const error = searchParams.get('error');
    const email = searchParams.get('email');
    
    if (success === 'true' && email) {
      toast.success(`Successfully connected ${email}!`);
      // Clear URL params
      setSearchParams({});
    } else if (error) {
      toast.error(`OAuth failed: ${error}`);
      setSearchParams({});
    }    
  }, []);

  const fetchProviders = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${apiUrl}/api/calendar/providers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProviders(response.data);
    } catch (error) {
      console.error('Error fetching calendar providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectGoogle = () => {
    const token = localStorage.getItem('token');
    window.location.href = `${apiUrl}/api/calendar/oauth/google?token=${token}`;
  };

  const handleConnectMicrosoft = () => {
    const token = localStorage.getItem('token');
    window.location.href = `${apiUrl}/api/calendar/oauth/microsoft?token=${token}`;
  };

  const handleRefreshToken = async (providerId) => {
    setRefreshing(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${apiUrl}/api/calendar/providers/${providerId}/refresh`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchProviders();
    } catch (error) {
      console.error('Error refreshing token:', error);
      alert('Failed to refresh token. Please reconnect your calendar.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleDisconnect = async (providerId) => {
    if (!window.confirm('Are you sure you want to disconnect this calendar?')) {
      return;
    }

    setDeleting(providerId);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${apiUrl}/api/calendar/providers/${providerId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchProviders();
    } catch (error) {
      console.error('Error disconnecting calendar:', error);
      alert('Failed to disconnect calendar.');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Calendar Integration</h1>
          <p className="text-gray-600 mt-1">Connect your calendar for AI-powered meeting management</p>
        </div>
        <div className="flex gap-3">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button 
                  onClick={handleConnectGoogle}
                  className="w-14 h-14 rounded-lg bg-white border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
                >
                  <GoogleIcon className="w-8 h-8" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Connect with Google</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button 
                  onClick={handleConnectMicrosoft}
                  className="w-14 h-14 rounded-lg bg-white border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
                >
                  <OutlookIcon className="w-8 h-8" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Connect with Outlook</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Providers List */}
      {providers.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Calendar className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Calendar Connected</h3>
            <p className="text-gray-600 text-center mb-4">
              Connect your calendar to enable AI-powered meeting detection and scheduling
            </p>
            <div className="flex gap-3 justify-center">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button 
                      onClick={handleConnectGoogle}
                      className="w-16 h-16 rounded-lg bg-white border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
                    >
                      <GoogleIcon className="w-10 h-10" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Connect with Google</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button 
                      onClick={handleConnectMicrosoft}
                      className="w-16 h-16 rounded-lg bg-white border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
                    >
                      <OutlookIcon className="w-10 h-10" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Connect with Outlook</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {providers.map((provider) => (
            <Card key={provider.id} className="border-green-200 bg-green-50/30">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full flex items-center justify-center bg-gray-50">
                      {provider.provider === 'google' ? (
                        <GoogleIcon className="w-7 h-7" />
                      ) : (
                        <OutlookIcon className="w-7 h-7" />
                      )}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{provider.email}</CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        <Badge className="bg-green-500">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          Connected
                        </Badge>
                        <span className="text-xs capitalize">
                          {provider.provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'}
                        </span>
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDisconnect(provider.id)}
                    disabled={deleting === provider.id}
                    className="text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  >
                    {deleting === provider.id ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Status</span>
                    <span className="font-medium text-green-600">Active</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Connected On</span>
                    <span className="font-medium">
                      {new Date(provider.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {provider.last_sync && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Last Synced</span>
                      <span className="font-medium">
                        {new Date(provider.last_sync).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {provider.token_expires_at && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-600" />
                        <span className="text-sm text-gray-600">Token expires soon</span>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRefreshToken(provider.id)}
                        disabled={refreshing}
                      >
                        {refreshing ? (
                          <RefreshCw className="w-3 h-3 mr-2 animate-spin" />
                        ) : (
                          <RefreshCw className="w-3 h-3 mr-2" />
                        )}
                        Refresh Token
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default CalendarProviders;
