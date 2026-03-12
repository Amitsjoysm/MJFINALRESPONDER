import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Target, Sparkles, Check, X, RefreshCw, Info, Settings as SettingsIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const LeadSettings = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [leadSettings, setLeadSettings] = useState({
    global_lead_qualification_enabled: false,
    global_lead_nurturing_enabled: false
  });
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load user settings
      if (user) {
        setLeadSettings({
          global_lead_qualification_enabled: user.global_lead_qualification_enabled || false,
          global_lead_nurturing_enabled: user.global_lead_nurturing_enabled || false
        });
      }
      
      // Load intents
      const intentsData = await API.getIntents();
      setIntents(intentsData);
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleQualification = async () => {
    const newValue = !leadSettings.global_lead_qualification_enabled;
    setSaving(true);
    
    try {
      await API.updateUserSettings({
        global_lead_qualification_enabled: newValue
      });
      
      setLeadSettings(prev => ({
        ...prev,
        global_lead_qualification_enabled: newValue
      }));
      
      await refreshUser();
      
      toast.success(newValue ? 'Lead Qualification enabled globally' : 'Lead Qualification disabled globally');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleNurturing = async () => {
    const newValue = !leadSettings.global_lead_nurturing_enabled;
    setSaving(true);
    
    try {
      await API.updateUserSettings({
        global_lead_nurturing_enabled: newValue
      });
      
      setLeadSettings(prev => ({
        ...prev,
        global_lead_nurturing_enabled: newValue
      }));
      
      await refreshUser();
      
      toast.success(newValue ? 'Lead Nurturing enabled globally' : 'Lead Nurturing disabled globally');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  const leadIntents = intents.filter(i => i.is_inbound_lead);
  const qualificationIntents = leadIntents.filter(i => i.enable_lead_qualification);
  const nurturingIntents = leadIntents.filter(i => i.enable_lead_nurturing);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Lead Management Controls</h1>
        <p className="text-gray-600 mt-1">Control how your AI assistant qualifies and nurtures inbound leads</p>
      </div>

      {/* Global Status Card */}
      <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-purple-600" />
            Global Lead Settings
          </CardTitle>
          <CardDescription>
            These settings control lead management across all intents
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Lead Qualification Toggle */}
            <div className="bg-white rounded-lg p-6 border-2 border-indigo-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Target className="w-8 h-8 text-indigo-600" />
                  <div>
                    <h3 className="font-semibold text-lg">Lead Qualification</h3>
                    <p className="text-xs text-gray-600">Automatic lead scoring</p>
                  </div>
                </div>
                {leadSettings.global_lead_qualification_enabled ? (
                  <Badge className="bg-green-500 text-white text-base px-3 py-1">
                    <Check className="w-4 h-4 mr-1" />
                    ON
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-base px-3 py-1">
                    <X className="w-4 h-4 mr-1" />
                    OFF
                  </Badge>
                )}
              </div>
              <p className="text-sm text-gray-700 mb-4">
                Automatically evaluate and score leads based on their responses (0-100 scale)
              </p>
              <Button
                onClick={handleToggleQualification}
                disabled={saving}
                className={`w-full ${leadSettings.global_lead_qualification_enabled 
                  ? 'bg-orange-500 hover:bg-orange-600' 
                  : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {saving ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : leadSettings.global_lead_qualification_enabled ? (
                  <>
                    <X className="w-4 h-4 mr-2" />
                    Disable Qualification
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Enable Qualification
                  </>
                )}
              </Button>
            </div>

            {/* Lead Nurturing Toggle */}
            <div className="bg-white rounded-lg p-6 border-2 border-pink-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Sparkles className="w-8 h-8 text-pink-600" />
                  <div>
                    <h3 className="font-semibold text-lg">Lead Nurturing</h3>
                    <p className="text-xs text-gray-600">Contextual questions</p>
                  </div>
                </div>
                {leadSettings.global_lead_nurturing_enabled ? (
                  <Badge className="bg-green-500 text-white text-base px-3 py-1">
                    <Check className="w-4 h-4 mr-1" />
                    ON
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-base px-3 py-1">
                    <X className="w-4 h-4 mr-1" />
                    OFF
                  </Badge>
                )}
              </div>
              <p className="text-sm text-gray-700 mb-4">
                Ask one-two contextual questions per email to gather lead information naturally
              </p>
              <Button
                onClick={handleToggleNurturing}
                disabled={saving}
                className={`w-full ${leadSettings.global_lead_nurturing_enabled 
                  ? 'bg-orange-500 hover:bg-orange-600' 
                  : 'bg-pink-600 hover:bg-pink-700'
                }`}
              >
                {saving ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : leadSettings.global_lead_nurturing_enabled ? (
                  <>
                    <X className="w-4 h-4 mr-2" />
                    Disable Nurturing
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Enable Nurturing
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Intent-Level Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-600" />
            Per-Intent Configuration
          </CardTitle>
          <CardDescription>
            Even with global settings enabled, you can control these features per intent
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm font-semibold text-blue-900">Lead Intents</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">{leadIntents.length}</p>
              <p className="text-xs text-blue-700 mt-1">Intents marked as leads</p>
            </div>
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
              <p className="text-sm font-semibold text-indigo-900">With Qualification</p>
              <p className="text-3xl font-bold text-indigo-600 mt-2">{qualificationIntents.length}</p>
              <p className="text-xs text-indigo-700 mt-1">Intents using qualification</p>
            </div>
            <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
              <p className="text-sm font-semibold text-pink-900">With Nurturing</p>
              <p className="text-3xl font-bold text-pink-600 mt-2">{nurturingIntents.length}</p>
              <p className="text-xs text-pink-700 mt-1">Intents using nurturing</p>
            </div>
          </div>

          {leadIntents.length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">Lead Intents:</p>
              {leadIntents.map(intent => (
                <div key={intent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                  <div>
                    <p className="font-medium">{intent.name}</p>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        Priority: {intent.priority}
                      </Badge>
                      {intent.enable_lead_qualification && (
                        <Badge className="bg-indigo-500 text-xs">Qualification</Badge>
                      )}
                      {intent.enable_lead_nurturing && (
                        <Badge className="bg-pink-500 text-xs">Nurturing</Badge>
                      )}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate('/intents')}
                  >
                    Configure
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed">
              <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">No lead intents configured yet</p>
              <Button onClick={() => navigate('/intents')}>
                Configure Intents
              </Button>
            </div>
          )}

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-6">
            <h4 className="text-sm font-semibold text-amber-900 mb-2">How It Works</h4>
            <ul className="text-sm text-amber-800 space-y-1 list-disc list-inside">
              <li><strong>Global Settings</strong> must be enabled for the features to work</li>
              <li><strong>Per-Intent Settings</strong> control which intents use these features</li>
              <li>Both settings must be enabled for lead qualification/nurturing to activate</li>
              <li>You can enable/disable per intent in the Intents page</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LeadSettings;
