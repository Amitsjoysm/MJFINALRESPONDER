import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Activity, RefreshCw, Zap, Mail, Send, Clock } from 'lucide-react';
import { format } from 'date-fns';

const LiveMonitoring = () => {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    }
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadData = async () => {
    try {
      const [emailData, statsData] = await Promise.all([
        API.getEmails({ limit: 20 }),
        API.getEmailStats()
      ]);
      setEmails(emailData.slice(0, 20));
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartPolling = async () => {
    setIsPolling(true);
    try {
      await API.startPolling();
      toast.success('Email polling started');
      setTimeout(loadData, 2000);
    } catch (error) {
      toast.error('Failed to start polling');
    } finally {
      setIsPolling(false);
    }
  };

  const handleRefresh = () => {
    loadData();
    toast.success('Data refreshed');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'bg-green-500';
      case 'draft_ready': return 'bg-blue-500';
      case 'processing': return 'bg-yellow-500';
      case 'escalated': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading monitoring data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Monitoring</h1>
          <p className="text-gray-600 mt-1">Real-time email processing activity</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={autoRefresh}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? 'destructive' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className="w-4 h-4 mr-2" />
            {autoRefresh ? 'Stop Auto-Refresh' : 'Auto-Refresh (10s)'}
          </Button>
          <Button
            onClick={handleStartPolling}
            disabled={isPolling}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
          >
            <Zap className="w-4 h-4 mr-2" />
            Start Polling
          </Button>
        </div>
      </div>

      {/* Real-time Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900 flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Total Emails
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900">{stats?.total_emails || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-900 flex items-center gap-2">
              <Send className="w-4 h-4" />
              Sent
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-900">{stats?.sent_emails || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-yellow-900 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-900">{stats?.pending || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-900 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Active Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-900">{stats?.active_accounts || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Stream */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-600" />
              Recent Activity (Last 20)
            </span>
            {autoRefresh && (
              <Badge className="bg-green-500 animate-pulse">
                <Activity className="w-3 h-3 mr-1" />
                Live
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {emails.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No recent activity
              </div>
            ) : (
              emails.map((email, index) => (
                <div 
                  key={email.id} 
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(email.status)}`} />
                      <div>
                        <p className="font-medium text-gray-900">
                          {email.subject || '(No Subject)'}
                        </p>
                        <p className="text-sm text-gray-600">
                          From: {email.from_email}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {email.intent_name && (
                      <Badge variant="outline" className="bg-purple-50">
                        {email.intent_name}
                      </Badge>
                    )}
                    <Badge className={getStatusColor(email.status)}>
                      {email.status}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {email.received_at && format(new Date(email.received_at), 'HH:mm:ss')}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LiveMonitoring;