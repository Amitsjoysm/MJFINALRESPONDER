import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  UserPlus, Building2, Mail, Phone, Briefcase, ChevronRight,
  Filter, Search, TrendingUp, Calendar, Activity, Target, RefreshCw, Link as LinkIcon
} from 'lucide-react';

const InboundLeads = () => {
  const { user } = useAuth();
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [hubspotStatus, setHubspotStatus] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    stage: '',
    priority: '',
    search: ''
  });

  useEffect(() => {
    loadLeads();
    loadStats();
    loadHubSpotStatus();
  }, [filters]);

  const loadHubSpotStatus = async () => {
    try {
      const status = await API.getHubSpotStatus();
      setHubspotStatus(status);
    } catch (error) {
      console.error('Failed to load HubSpot status:', error);
    }
  };

  const handleSyncToHubSpot = async (leadIds = null) => {
    if (!user.hubspot_connected) {
      toast.error('Please connect your HubSpot account in Settings first');
      return;
    }

    setSyncing(true);
    try {
      const response = await API.syncLeadsToHubSpot(leadIds);
      toast.success(response.message || 'Sync started successfully');
      
      // Reload leads after a few seconds to show updated sync status
      setTimeout(() => {
        loadLeads();
      }, 3000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync leads to HubSpot');
    } finally {
      setSyncing(false);
    }
  };

  const loadLeads = async () => {
    try {
      const params = {};
      if (filters.stage) params.stage = filters.stage;
      if (filters.priority) params.priority = filters.priority;
      if (filters.search) params.search = filters.search;
      
      const data = await API.getLeads(params);
      setLeads(data);
    } catch (error) {
      toast.error('Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await API.getLeadStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadLeadDetails = async (leadId) => {
    try {
      const data = await API.getLeadDetail(leadId);
      setSelectedLead(data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load lead details');
    }
  };

  const handleStageChange = async (leadId, newStage, reason = '') => {
    try {
      await API.updateLeadStage(leadId, { stage: newStage, reason, performed_by: 'user' });
      toast.success('Lead stage updated');
      loadLeads();
      loadStats();
      if (selectedLead && selectedLead.id === leadId) {
        loadLeadDetails(leadId);
      }
    } catch (error) {
      toast.error('Failed to update lead stage');
    }
  };

  const handleUpdateLead = async (leadId, updateData) => {
    try {
      await API.updateLead(leadId, updateData);
      toast.success('Lead updated successfully');
      loadLeads();
      if (selectedLead && selectedLead.id === leadId) {
        loadLeadDetails(leadId);
      }
      setEditDialogOpen(false);
    } catch (error) {
      toast.error('Failed to update lead');
    }
  };

  const getStageColor = (stage) => {
    const colors = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      qualified: 'bg-purple-100 text-purple-800',
      converted: 'bg-green-100 text-green-800',
      lost: 'bg-gray-100 text-gray-800'
    };
    return colors[stage] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-600',
      medium: 'bg-blue-100 text-blue-600',
      high: 'bg-orange-100 text-orange-600',
      urgent: 'bg-red-100 text-red-600'
    };
    return colors[priority] || 'bg-gray-100 text-gray-600';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading leads...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Target className="w-8 h-8 text-blue-600" />
            Inbound Leads
          </h1>
          <p className="text-gray-500 mt-1">
            Track and manage your inbound sales leads
          </p>
        </div>
        <div className="flex items-center gap-3">
          {user?.hubspot_enabled && (
            <>
              {hubspotStatus?.connected ? (
                <Button
                  onClick={() => handleSyncToHubSpot()}
                  disabled={syncing}
                  className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white flex items-center gap-2"
                >
                  {syncing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      Sync to HubSpot
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => window.location.href = '/settings'}
                  className="flex items-center gap-2"
                >
                  <LinkIcon className="w-4 h-4" />
                  Connect HubSpot
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Leads</p>
                  <p className="text-2xl font-bold">{stats.total_leads}</p>
                </div>
                <UserPlus className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Avg Score</p>
                  <p className={`text-2xl font-bold ${getScoreColor(stats.average_score)}`}>
                    {stats.average_score}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Meetings</p>
                  <p className="text-2xl font-bold">{stats.meetings_scheduled}</p>
                </div>
                <Calendar className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Conversion Rate</p>
                  <p className="text-2xl font-bold">{stats.conversion_rate}%</p>
                </div>
                <Target className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Name, email, company..."
                  value={filters.search}
                  onChange={(e) => setFilters({...filters, search: e.target.value})}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div>
              <Label>Stage</Label>
              <select
                value={filters.stage}
                onChange={(e) => setFilters({...filters, stage: e.target.value})}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Stages</option>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
                <option value="converted">Converted</option>
                <option value="lost">Lost</option>
              </select>
            </div>

            <div>
              <Label>Priority</Label>
              <select
                value={filters.priority}
                onChange={(e) => setFilters({...filters, priority: e.target.value})}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={() => setFilters({ stage: '', priority: '', search: '' })}
                variant="outline"
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stage Pipeline */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Pipeline Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(stats.by_stage).map(([stage, count]) => (
                <div key={stage} className="text-center">
                  <div className={`inline-flex px-4 py-2 rounded-full ${getStageColor(stage)} font-semibold mb-2`}>
                    {count}
                  </div>
                  <p className="text-sm text-gray-600 capitalize">{stage}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leads List */}
      <Card>
        <CardHeader>
          <CardTitle>All Leads ({leads.length})</CardTitle>
          <CardDescription>Click on a lead to view details and manage</CardDescription>
        </CardHeader>
        <CardContent>
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <UserPlus className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No leads found</p>
              <p className="text-sm text-gray-400 mt-2">
                Leads will appear here when emails match your inbound lead intents
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {leads.map((lead) => (
                <div
                  key={lead.id}
                  className="p-4 border rounded-lg hover:border-blue-500 cursor-pointer transition-colors"
                  onClick={() => loadLeadDetails(lead.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">
                          {lead.lead_name || 'Unknown Name'}
                        </h3>
                        <Badge className={getStageColor(lead.stage)}>
                          {lead.stage}
                        </Badge>
                        <Badge className={getPriorityColor(lead.priority)}>
                          {lead.priority}
                        </Badge>
                        <span className={`font-bold ${getScoreColor(lead.score)}`}>
                          Score: {lead.score}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                          <Mail className="w-4 h-4" />
                          {lead.lead_email}
                        </div>
                        
                        {lead.company_name && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Building2 className="w-4 h-4" />
                            {lead.company_name}
                          </div>
                        )}
                        
                        {lead.job_title && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Briefcase className="w-4 h-4" />
                            {lead.job_title}
                          </div>
                        )}
                        
                        {lead.phone && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Phone className="w-4 h-4" />
                            {lead.phone}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                        <span>📧 {lead.emails_received} received / {lead.emails_sent} sent</span>
                        {lead.meeting_scheduled && (
                          <span className="text-green-600">📅 Meeting Scheduled</span>
                        )}
                        <span>Created {new Date(lead.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lead Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedLead && (
            <div>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <span>{selectedLead.lead_name || 'Unknown Name'}</span>
                  <Badge className={getStageColor(selectedLead.stage)}>
                    {selectedLead.stage}
                  </Badge>
                  <Badge className={getPriorityColor(selectedLead.priority)}>
                    {selectedLead.priority}
                  </Badge>
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-6 mt-6">
                {/* Lead Score */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-500">Lead Score</p>
                    <p className={`text-3xl font-bold ${getScoreColor(selectedLead.score)}`}>
                      {selectedLead.score}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Engagement</p>
                    <p className="text-xl font-semibold">
                      {selectedLead.emails_received + selectedLead.emails_sent} interactions
                    </p>
                  </div>
                </div>

                {/* Contact Information */}
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Mail className="w-5 h-5" />
                    Contact Information
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <Label>Email</Label>
                      <p className="mt-1">{selectedLead.lead_email}</p>
                    </div>
                    {selectedLead.phone && (
                      <div>
                        <Label>Phone</Label>
                        <p className="mt-1">{selectedLead.phone}</p>
                      </div>
                    )}
                    {selectedLead.company_name && (
                      <div>
                        <Label>Company</Label>
                        <p className="mt-1">{selectedLead.company_name}</p>
                      </div>
                    )}
                    {selectedLead.job_title && (
                      <div>
                        <Label>Job Title</Label>
                        <p className="mt-1">{selectedLead.job_title}</p>
                      </div>
                    )}
                    {selectedLead.industry && (
                      <div>
                        <Label>Industry</Label>
                        <p className="mt-1">{selectedLead.industry}</p>
                      </div>
                    )}
                    {selectedLead.company_size && (
                      <div>
                        <Label>Company Size</Label>
                        <p className="mt-1">{selectedLead.company_size}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Interests & Requirements */}
                {(selectedLead.specific_interests || selectedLead.requirements) && (
                  <div>
                    <h3 className="font-semibold mb-3">Interests & Requirements</h3>
                    {selectedLead.specific_interests && (
                      <div className="mb-3">
                        <Label>Interests</Label>
                        <p className="text-sm mt-1">{selectedLead.specific_interests}</p>
                      </div>
                    )}
                    {selectedLead.requirements && (
                      <div>
                        <Label>Requirements</Label>
                        <p className="text-sm mt-1">{selectedLead.requirements}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Stage Management */}
                <div>
                  <h3 className="font-semibold mb-3">Stage Management</h3>
                  <div className="flex gap-2">
                    {['new', 'contacted', 'qualified', 'converted'].map((stage) => (
                      <Button
                        key={stage}
                        size="sm"
                        variant={selectedLead.stage === stage ? 'default' : 'outline'}
                        onClick={() => handleStageChange(selectedLead.id, stage)}
                        disabled={selectedLead.stage === stage}
                      >
                        {stage.charAt(0).toUpperCase() + stage.slice(1)}
                      </Button>
                    ))}
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => {
                        const reason = prompt('Reason for marking as lost:');
                        if (reason) handleStageChange(selectedLead.id, 'lost', reason);
                      }}
                    >
                      Mark as Lost
                    </Button>
                  </div>
                </div>

                {/* Activity Timeline */}
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Activity Timeline
                  </h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {selectedLead.activities && selectedLead.activities.length > 0 ? (
                      selectedLead.activities.slice().reverse().map((activity, idx) => (
                        <div key={idx} className="flex gap-3 text-sm border-l-2 border-gray-200 pl-4">
                          <div className="flex-1">
                            <p className="font-medium">{activity.description}</p>
                            <p className="text-xs text-gray-500">
                              {new Date(activity.timestamp).toLocaleString()} • by {activity.performed_by}
                            </p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No activities yet</p>
                    )}
                  </div>
                </div>

                {/* Notes */}
                {selectedLead.notes && (
                  <div>
                    <Label>Notes</Label>
                    <p className="text-sm mt-1 p-3 bg-gray-50 rounded">{selectedLead.notes}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InboundLeads;
