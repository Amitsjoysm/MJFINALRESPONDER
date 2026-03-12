import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Mail, Send, AlertTriangle, Users, Activity, Zap, Settings, CheckCircle2 } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, statusData] = await Promise.all([
        API.getEmailStats(),
        API.getSystemStatus()
      ]);
      setStats(statsData);
      setSystemStatus(statusData);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleStartPolling = async () => {
    setPolling(true);
    try {
      await API.startPolling();
      toast.success('Email polling started');
      setTimeout(loadData, 2000);
    } catch (error) {
      toast.error('Failed to start polling');
    } finally {
      setPolling(false);
    }
  };

  const handleStopPolling = async () => {
    setPolling(true);
    try {
      await API.stopPolling();
      toast.success('Email polling stopped');
      setTimeout(loadData, 2000);
    } catch (error) {
      toast.error('Failed to stop polling');
    } finally {
      setPolling(false);
    }
  };

  const handleTestProcessing = async () => {
    try {
      const result = await API.testEmailProcessing();
      toast.success(`Test successful! Used ${result.total_tokens_used} tokens`);
    } catch (error) {
      toast.error('Test failed');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div data-testid="dashboard" className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Monitor your automated email assistant performance</p>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-3">
        <Button
          data-testid="start-polling-btn"
          onClick={handleStartPolling}
          disabled={polling}
          className="bg-green-600 hover:bg-green-700"
        >
          <Activity className="w-4 h-4 mr-2" />
          Live Polling
        </Button>
        <Button
          data-testid="stop-polling-btn"
          onClick={handleStopPolling}
          disabled={polling}
          className="bg-gray-600 hover:bg-gray-700"
        >
          Stop Polling
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-blue-900">Total Emails</CardTitle>
            <Mail className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900" data-testid="total-emails">{stats?.total_emails || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-green-900">Sent Emails</CardTitle>
            <Send className="h-5 w-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-900" data-testid="sent-emails">{stats?.sent_emails || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-amber-900">Escalated</CardTitle>
            <AlertTriangle className="h-5 w-5 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-900" data-testid="escalated">{stats?.escalated || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-purple-900">Active Accounts</CardTitle>
            <Users className="h-5 w-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-900" data-testid="active-accounts">
              {stats?.active_accounts || 0}/{stats?.total_accounts || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-purple-600" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            data-testid="live-monitoring-btn"
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 justify-start"
            onClick={handleStartPolling}
          >
            <Activity className="w-4 h-4 mr-2" />
            Live Email Monitoring
          </Button>
          <Button
            data-testid="test-processing-btn"
            variant="outline"
            className="w-full justify-start"
            onClick={handleTestProcessing}
          >
            <Zap className="w-4 h-4 mr-2" />
            Test Email Processing
          </Button>
          <Button
            data-testid="manage-intents-btn"
            variant="outline"
            className="w-full justify-start"
            onClick={() => window.location.href = '/intents'}
          >
            <Settings className="w-4 h-4 mr-2" />
            Manage Intents
          </Button>
          <Button
            data-testid="setup-accounts-btn"
            variant="outline"
            className="w-full justify-start"
            onClick={() => window.location.href = '/email-accounts'}
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Setup Email Accounts
          </Button>
        </CardContent>
      </Card>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <StatusRow label="Email Polling" status={systemStatus?.email_polling} />
            <StatusRow label="Email Accounts" status={systemStatus?.email_accounts} />
            <StatusRow label="Intent Detection" status={systemStatus?.intent_detection} />
            <StatusRow label="AI Processing" status={systemStatus?.ai_processing} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const StatusRow = ({ label, status }) => {
  const getStatusColor = (status) => {
    if (typeof status === 'string') {
      if (status.includes('active') || status === 'online') return 'bg-green-500';
      if (status.includes('setup needed') || status === 'offline') return 'bg-amber-500';
      return 'bg-gray-500';
    }
    return 'bg-gray-500';
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">{status}</span>
        <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
      </div>
    </div>
  );
};

export default Dashboard;
