import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Link as LinkIcon, Unlink, RefreshCw, Check, X, ExternalLink, Target, Sparkles } from 'lucide-react';

const Settings = () => {
  const { user, refreshUser } = useAuth();
  const [hubspotStatus, setHubspotStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [leadSettings, setLeadSettings] = useState({
    global_lead_qualification_enabled: false,
    global_lead_nurturing_enabled: false
  });
  const [savingLeadSettings, setSavingLeadSettings] = useState(false);

  useEffect(() => {
    loadHubSpotStatus();
    loadLeadSettings();
  }, []);

  const loadHubSpotStatus = async () => {
    try {
      const status = await API.getHubSpotStatus();
      setHubspotStatus(status);
    } catch (error) {
      console.error('Failed to load HubSpot status:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadLeadSettings = () => {
    if (user) {
      setLeadSettings({
        global_lead_qualification_enabled: user.global_lead_qualification_enabled || false,
        global_lead_nurturing_enabled: user.global_lead_nurturing_enabled || false
      });
    }
  };

  const handleToggleLeadQualification = async () => {
    const newValue = !leadSettings.global_lead_qualification_enabled;
    setSavingLeadSettings(true);
    
    try {
      await API.updateUserSettings({
        global_lead_qualification_enabled: newValue
      });
      
      setLeadSettings(prev => ({
        ...prev,
        global_lead_qualification_enabled: newValue
      }));
      
      await refreshUser();
      
      toast.success(newValue ? 'Lead Qualification enabled' : 'Lead Qualification disabled');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setSavingLeadSettings(false);
    }
  };

  const handleToggleLeadNurturing = async () => {
    const newValue = !leadSettings.global_lead_nurturing_enabled;
    setSavingLeadSettings(true);
    
    try {
      await API.updateUserSettings({
        global_lead_nurturing_enabled: newValue
      });
      
      setLeadSettings(prev => ({
        ...prev,
        global_lead_nurturing_enabled: newValue
      }));
      
      await refreshUser();
      
      toast.success(newValue ? 'Lead Nurturing enabled' : 'Lead Nurturing disabled');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setSavingLeadSettings(false);
    }
  };

  const handleConnectHubSpot = async () => {
    if (!user.hubspot_enabled) {
      toast.error('HubSpot integration not enabled for your account. Contact admin.');
      return;
    }

    setConnecting(true);
    try {
      const response = await API.startHubSpotOAuth();
      
      // Open HubSpot OAuth in a new window
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      
      const authWindow = window.open(
        response.authorization_url,
        'HubSpot Authorization',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      // Poll for window close or URL change
      const checkWindow = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkWindow);
          setConnecting(false);
          // Reload status after a delay
          setTimeout(() => {
            loadHubSpotStatus();
          }, 2000);
        }
      }, 500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start HubSpot connection');
      setConnecting(false);
    }
  };

  const handleDisconnectHubSpot = async () => {
    if (!window.confirm('Are you sure you want to disconnect your HubSpot account?')) {
      return;
    }

    try {
      await API.disconnectHubSpot();
      toast.success('HubSpot account disconnected');
      loadHubSpotStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to disconnect HubSpot');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your integrations and preferences</p>
      </div>

      {/* Lead Management Settings Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Target className="w-8 h-8 text-purple-600" />
                Lead Management Settings
              </CardTitle>
              <CardDescription className="mt-2">
                Control how the system qualifies and nurtures inbound leads
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Lead Qualification Toggle */}
          <div className="border rounded-lg p-4 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-indigo-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Lead Qualification</h3>
                  {leadSettings.global_lead_qualification_enabled ? (
                    <Badge className="bg-green-500 text-white">
                      <Check className="w-3 h-3 mr-1" />
                      Enabled
                    </Badge>
                  ) : (
                    <Badge variant="secondary">
                      <X className="w-3 h-3 mr-1" />
                      Disabled
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-700 mb-3">
                  Automatically evaluate and score incoming leads based on their responses. The system will ask qualification questions and assign scores to help prioritize high-value leads.
                </p>
                <div className="bg-white rounded p-3 border border-indigo-200">
                  <p className="text-xs text-gray-600">
                    <strong>How it works:</strong> When enabled, the system will automatically ask relevant questions to qualify leads and score them from 0-100 based on their answers. Leads scoring above 60 are marked as "qualified".
                  </p>
                </div>
              </div>
              <div className="ml-4">
                <Button
                  onClick={handleToggleLeadQualification}
                  disabled={savingLeadSettings}
                  className={leadSettings.global_lead_qualification_enabled 
                    ? "bg-green-600 hover:bg-green-700" 
                    : "bg-gray-400 hover:bg-gray-500"
                  }
                >
                  {savingLeadSettings ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : leadSettings.global_lead_qualification_enabled ? (
                    'Disable'
                  ) : (
                    'Enable'
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Lead Nurturing Toggle */}
          <div className="border rounded-lg p-4 bg-gradient-to-r from-purple-50 to-pink-50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Lead Nurturing</h3>
                  {leadSettings.global_lead_nurturing_enabled ? (
                    <Badge className="bg-green-500 text-white">
                      <Check className="w-3 h-3 mr-1" />
                      Enabled
                    </Badge>
                  ) : (
                    <Badge variant="secondary">
                      <X className="w-3 h-3 mr-1" />
                      Disabled
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-700 mb-3">
                  Engage leads with intelligent follow-up questions to gather more information and build relationships. The system will ask 1-2 contextual questions per email to understand their needs better.
                </p>
                <div className="bg-white rounded p-3 border border-purple-200">
                  <p className="text-xs text-gray-600 mb-2">
                    <strong>How it works:</strong> When enabled, the AI will naturally include 1-2 relevant questions in auto-replies to learn more about the lead's needs, timeline, and budget.
                  </p>
                  <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded">
                    <strong>Note:</strong> Nurturing is kept minimal - only essential questions are asked to avoid overwhelming leads. You can configure specific questions per intent in the Intents page.
                  </p>
                </div>
              </div>
              <div className="ml-4">
                <Button
                  onClick={handleToggleLeadNurturing}
                  disabled={savingLeadSettings}
                  className={leadSettings.global_lead_nurturing_enabled 
                    ? "bg-green-600 hover:bg-green-700" 
                    : "bg-gray-400 hover:bg-gray-500"
                  }
                >
                  {savingLeadSettings ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : leadSettings.global_lead_nurturing_enabled ? (
                    'Disable'
                  ) : (
                    'Enable'
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Important Notes */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">Important Notes</h4>
            <ul className="text-sm text-blue-800 space-y-2 list-disc list-inside">
              <li><strong>Optional by Default:</strong> Both features are disabled by default. Enable only if you want automated lead management.</li>
              <li><strong>Per-Intent Control:</strong> Even when globally enabled, you can control these features per intent in the Intents configuration page.</li>
              <li><strong>Minimal Conversations:</strong> The system is designed to gather information efficiently with minimal back-and-forth.</li>
              <li><strong>Auto-Reply Integration:</strong> These features work seamlessly with auto-reply. Questions are naturally integrated into response emails.</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* HubSpot Integration Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <svg className="w-8 h-8" viewBox="0 0 24 24" fill="#FF7A59">
                  <path d="M18.7 8.7l-3.4-3.4c-.4-.4-1-.4-1.4 0l-.9.9 4.8 4.8.9-.9c.4-.4.4-1 0-1.4zM8 12l4.8 4.8 8.2-8.2-4.8-4.8L8 12zm-1.4 6.4l1.9-5.7 3.8 3.8-5.7 1.9z"/>
                </svg>
                HubSpot CRM Integration
              </CardTitle>
              <CardDescription className="mt-2">
                Connect your HubSpot account to automatically sync leads to your CRM
              </CardDescription>
            </div>
            {hubspotStatus?.connected ? (
              <Badge className="bg-green-500 text-white px-4 py-2">
                <Check className="w-4 h-4 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary" className="px-4 py-2">
                <X className="w-4 h-4 mr-1" />
                Not Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {!user.hubspot_enabled ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-yellow-800">HubSpot Integration Not Enabled</h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    Contact your administrator to enable HubSpot integration for your account.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {hubspotStatus?.connected ? (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <Check className="w-5 h-5 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-green-800">HubSpot Connected</h3>
                        <p className="text-sm text-green-700 mt-1">
                          Your HubSpot account is connected and ready to sync leads.
                        </p>
                        {hubspotStatus.connected_at && (
                          <p className="text-xs text-green-600 mt-2">
                            Connected on: {new Date(hubspotStatus.connected_at).toLocaleDateString()}
                          </p>
                        )}
                        {hubspotStatus.last_sync_at && (
                          <p className="text-xs text-green-600">
                            Last sync: {new Date(hubspotStatus.last_sync_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Button
                      variant="destructive"
                      onClick={handleDisconnectHubSpot}
                      className="flex items-center gap-2"
                    >
                      <Unlink className="w-4 h-4" />
                      Disconnect HubSpot
                    </Button>
                    <Button
                      variant="outline"
                      onClick={loadHubSpotStatus}
                      className="flex items-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Refresh Status
                    </Button>
                  </div>

                  {hubspotStatus.error_message && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-sm text-red-800">
                        <strong>Error:</strong> {hubspotStatus.error_message}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-blue-800 mb-2">About HubSpot Integration</h3>
                    <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
                      <li>Automatically sync your inbound leads to HubSpot CRM</li>
                      <li>Keep your contact information up-to-date</li>
                      <li>Manual or automatic sync options available</li>
                      <li>Secure OAuth 2.0 authentication</li>
                    </ul>
                  </div>

                  <Button
                    onClick={handleConnectHubSpot}
                    disabled={connecting}
                    className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white flex items-center gap-2"
                  >
                    {connecting ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <LinkIcon className="w-4 h-4" />
                        Connect HubSpot Account
                      </>
                    )}
                  </Button>
                </div>
              )}
            </>
          )}

          {user.role === 'super_admin' || user.role === 'admin' ? (
            <>
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">Admin Controls</h3>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-sm text-purple-700">
                    As an administrator, you can manage HubSpot access for all users.
                  </p>
                  <Button
                    variant="outline"
                    className="mt-3"
                    onClick={() => window.location.href = '/admin/hubspot'}
                  >
                    <SettingsIcon className="w-4 h-4 mr-2" />
                    Manage User Access
                  </Button>
                </div>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>

      {/* Integration Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>How to Use HubSpot Integration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="list-decimal list-inside space-y-3 text-gray-700">
            <li>
              <strong>Connect Your Account:</strong> Click the "Connect HubSpot Account" button above and authorize access to your HubSpot portal.
            </li>
            <li>
              <strong>Automatic Sync:</strong> Once connected, you can enable automatic syncing in the Inbound Leads page.
            </li>
            <li>
              <strong>Manual Sync:</strong> You can also manually sync specific leads or all pending leads from the Inbound Leads page.
            </li>
            <li>
              <strong>Monitor Status:</strong> Check the sync status of each lead in the Inbound Leads table.
            </li>
          </ol>
          
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Need help?</strong> Visit the{' '}
              <a 
                href="https://knowledge.hubspot.com/integrations/connect-apps-to-hubspot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline inline-flex items-center gap-1"
              >
                HubSpot Documentation
                <ExternalLink className="w-3 h-3" />
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
