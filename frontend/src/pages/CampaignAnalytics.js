import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Mail, Send, Eye, MessageSquare, AlertTriangle, 
  TrendingUp, Users, Calendar, Clock, BarChart3, Activity
} from 'lucide-react';

const CampaignAnalytics = () => {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCampaign();
    loadAnalytics();
  }, [campaignId]);

  const loadCampaign = async () => {
    try {
      const data = await API.getCampaign(campaignId);
      setCampaign(data);
    } catch (error) {
      toast.error('Failed to load campaign');
      navigate('/campaign/campaigns');
    }
  };

  const loadAnalytics = async () => {
    try {
      const data = await API.getCampaignAnalytics(campaignId);
      setAnalytics(data);
    } catch (error) {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', label: 'Draft' },
      scheduled: { color: 'bg-blue-100 text-blue-800', label: 'Scheduled' },
      running: { color: 'bg-green-100 text-green-800', label: 'Running' },
      paused: { color: 'bg-yellow-100 text-yellow-800', label: 'Paused' },
      completed: { color: 'bg-purple-100 text-purple-800', label: 'Completed' },
      stopped: { color: 'bg-gray-100 text-gray-800', label: 'Stopped' }
    };
    const config = statusConfig[status] || statusConfig.draft;
    return <Badge className={`${config.color}`}>{config.label}</Badge>;
  };

  if (loading || !campaign) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    );
  }

  const totalSent = campaign.emails_sent;
  const openRate = totalSent > 0 ? Math.round((campaign.emails_opened / totalSent) * 100) : 0;
  const replyRate = totalSent > 0 ? Math.round((campaign.emails_replied / totalSent) * 100) : 0;
  const bounceRate = totalSent > 0 ? Math.round((campaign.emails_bounced / totalSent) * 100) : 0;
  const successRate = totalSent > 0 ? Math.round(((totalSent - campaign.emails_failed - campaign.emails_bounced) / totalSent) * 100) : 0;

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/campaign/campaigns')}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{campaign.name}</h1>
            {getStatusBadge(campaign.status)}
          </div>
          <p className="text-gray-500 mt-1">Campaign analytics and performance metrics</p>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Users className="w-4 h-4" />
              Total Contacts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">{campaign.total_contacts || campaign.contact_ids.length}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Send className="w-4 h-4" />
              Emails Sent
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">{campaign.emails_sent}</p>
            <p className="text-xs text-gray-500 mt-1">
              {campaign.emails_pending} pending
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Replies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">{campaign.emails_replied}</p>
            <p className="text-xs text-gray-500 mt-1">
              {replyRate}% reply rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-red-600">{campaign.emails_failed + campaign.emails_bounced}</p>
            <p className="text-xs text-gray-500 mt-1">
              {campaign.emails_failed} failed, {campaign.emails_bounced} bounced
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Open Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2">
              <p className="text-4xl font-bold text-purple-600">{openRate}%</p>
              <TrendingUp className="w-5 h-5 text-green-500 mb-2" />
            </div>
            <p className="text-sm text-gray-600 mt-2">{campaign.emails_opened} emails opened</p>
            <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                style={{ width: `${openRate}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Reply Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2">
              <p className="text-4xl font-bold text-blue-600">{replyRate}%</p>
              <TrendingUp className="w-5 h-5 text-green-500 mb-2" />
            </div>
            <p className="text-sm text-gray-600 mt-2">{campaign.emails_replied} replies received</p>
            <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                style={{ width: `${replyRate}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2">
              <p className="text-4xl font-bold text-green-600">{successRate}%</p>
              <TrendingUp className="w-5 h-5 text-green-500 mb-2" />
            </div>
            <p className="text-sm text-gray-600 mt-2">Delivered successfully</p>
            <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                style={{ width: `${successRate}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Email Status Breakdown
          </CardTitle>
          <CardDescription>Detailed view of all email statuses</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="font-medium">Sent Successfully</span>
              </div>
              <span className="text-lg font-bold text-green-600">{campaign.emails_sent}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                <span className="font-medium">Pending</span>
              </div>
              <span className="text-lg font-bold text-yellow-600">{campaign.emails_pending}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-purple-500 rounded-full" />
                <span className="font-medium">Opened</span>
              </div>
              <span className="text-lg font-bold text-purple-600">{campaign.emails_opened}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-blue-500 rounded-full" />
                <span className="font-medium">Replied</span>
              </div>
              <span className="text-lg font-bold text-blue-600">{campaign.emails_replied}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-orange-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-orange-500 rounded-full" />
                <span className="font-medium">Bounced</span>
              </div>
              <span className="text-lg font-bold text-orange-600">{campaign.emails_bounced}</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="font-medium">Failed</span>
              </div>
              <span className="text-lg font-bold text-red-600">{campaign.emails_failed}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Campaign Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Campaign Configuration
          </CardTitle>
          <CardDescription>Current campaign settings and parameters</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Sending Settings</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Email Accounts:</span>
                  <span className="font-medium">{campaign.email_account_ids.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Daily Limit per Account:</span>
                  <span className="font-medium">{campaign.daily_limit_per_account}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Delay Range:</span>
                  <span className="font-medium">{campaign.random_delay_min}-{campaign.random_delay_max}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Email Verification:</span>
                  <span className="font-medium">{campaign.verify_emails ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Follow-up Configuration</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Follow-ups Enabled:</span>
                  <span className="font-medium">{campaign.follow_up_config.enabled ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Follow-up Count:</span>
                  <span className="font-medium">{campaign.follow_up_config.count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Intervals (days):</span>
                  <span className="font-medium">{campaign.follow_up_config.intervals.join(', ')}</span>
                </div>
              </div>
            </div>
          </div>

          {campaign.scheduled_start && (
            <div className="mt-6 pt-6 border-t">
              <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Schedule
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">Start:</span>
                  <span className="font-medium">{new Date(campaign.scheduled_start).toLocaleString()}</span>
                </div>
                {campaign.scheduled_end && (
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-600">End:</span>
                    <span className="font-medium">{new Date(campaign.scheduled_end).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Timeline</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Created:</span>
                <span className="font-medium">{new Date(campaign.created_at).toLocaleString()}</span>
              </div>
              {campaign.started_at && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Started:</span>
                  <span className="font-medium">{new Date(campaign.started_at).toLocaleString()}</span>
                </div>
              )}
              {campaign.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Completed:</span>
                  <span className="font-medium">{new Date(campaign.completed_at).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analytics Data if available */}
      {analytics && (
        <Card>
          <CardHeader>
            <CardTitle>Additional Analytics</CardTitle>
            <CardDescription>Extended performance metrics and insights</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analytics.email_type_breakdown && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Email Type Breakdown</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Initial:</span>
                      <span className="font-medium">{analytics.email_type_breakdown.initial || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Follow-ups:</span>
                      <span className="font-medium">{analytics.email_type_breakdown.follow_up || 0}</span>
                    </div>
                  </div>
                </div>
              )}
              {analytics.engagement_timeline && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Engagement Timeline</h4>
                  <p className="text-sm text-gray-600">
                    Most activity in {analytics.engagement_timeline.peak_day || 'first week'}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CampaignAnalytics;
