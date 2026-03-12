import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { Send, Plus, Trash2, Edit, Play, Pause, Square, RotateCcw, Search, BarChart3, Calendar, Mail, Users, AlertCircle } from 'lucide-react';

const Campaigns = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState([]);
  const [filteredCampaigns, setFilteredCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentCampaign, setCurrentCampaign] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [contacts, setContacts] = useState([]);
  const [contactLists, setContactLists] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [emailAccounts, setEmailAccounts] = useState([]);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    contact_ids: [],
    contact_tags: [],
    list_ids: [],
    initial_template_id: '',
    follow_up_config: {
      enabled: true,
      count: 3,
      intervals: [2, 4, 6],
      template_ids: []
    },
    email_account_ids: [],
    daily_limit_per_account: 100,
    random_delay_min: 60,
    random_delay_max: 300,
    scheduled_start: '',
    scheduled_end: '',
    timezone: 'UTC',
    verify_emails: false
  });

  useEffect(() => {
    loadCampaigns();
    loadContacts();
    loadContactLists();
    loadTemplates();
    loadEmailAccounts();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredCampaigns(campaigns);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredCampaigns(
        campaigns.filter(
          campaign =>
            campaign.name.toLowerCase().includes(query) ||
            (campaign.description && campaign.description.toLowerCase().includes(query)) ||
            campaign.status.toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, campaigns]);

  const loadCampaigns = async () => {
    try {
      const data = await API.getCampaigns();
      setCampaigns(data);
      setFilteredCampaigns(data);
    } catch (error) {
      toast.error('Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const loadContacts = async () => {
    try {
      const data = await API.getCampaignContacts();
      setContacts(data);
    } catch (error) {
      console.error('Failed to load contacts:', error);
    }
  };

  const loadContactLists = async () => {
    try {
      const data = await API.getContactLists();
      setContactLists(data);
    } catch (error) {
      console.error('Failed to load contact lists:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const data = await API.getCampaignTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadEmailAccounts = async () => {
    try {
      const data = await API.getEmailAccounts();
      setEmailAccounts(data.filter(acc => acc.account_type === 'oauth_gmail' && acc.is_active));
    } catch (error) {
      console.error('Failed to load email accounts:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (formData.contact_ids.length === 0 && formData.contact_tags.length === 0 && formData.list_ids.length === 0) {
      toast.error('Please select at least one contact, list, or tag');
      return;
    }
    if (!formData.initial_template_id) {
      toast.error('Please select an initial template');
      return;
    }
    if (formData.email_account_ids.length === 0) {
      toast.error('Please select at least one email account');
      return;
    }

    const campaignData = {
      name: formData.name,
      description: formData.description || null,
      contact_ids: formData.contact_ids,
      contact_tags: formData.contact_tags,
      list_ids: formData.list_ids,
      initial_template_id: formData.initial_template_id,
      follow_up_config: formData.follow_up_config,
      email_account_ids: formData.email_account_ids,
      daily_limit_per_account: parseInt(formData.daily_limit_per_account),
      random_delay_min: parseInt(formData.random_delay_min),
      random_delay_max: parseInt(formData.random_delay_max),
      scheduled_start: formData.scheduled_start || null,
      scheduled_end: formData.scheduled_end || null,
      timezone: formData.timezone,
      verify_emails: formData.verify_emails
    };

    try {
      if (editMode) {
        await API.updateCampaign(currentCampaign.id, campaignData);
        toast.success('Campaign updated successfully');
      } else {
        await API.createCampaign(campaignData);
        toast.success('Campaign created successfully');
      }
      setDialogOpen(false);
      resetForm();
      loadCampaigns();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save campaign');
    }
  };

  const handleEdit = (campaign) => {
    setEditMode(true);
    setCurrentCampaign(campaign);
    setFormData({
      name: campaign.name,
      description: campaign.description || '',
      contact_ids: campaign.contact_ids,
      contact_tags: campaign.contact_tags,
      list_ids: campaign.list_ids || [],
      initial_template_id: campaign.initial_template_id,
      follow_up_config: campaign.follow_up_config,
      email_account_ids: campaign.email_account_ids,
      daily_limit_per_account: campaign.daily_limit_per_account,
      random_delay_min: campaign.random_delay_min,
      random_delay_max: campaign.random_delay_max,
      scheduled_start: campaign.scheduled_start || '',
      scheduled_end: campaign.scheduled_end || '',
      timezone: campaign.timezone,
      verify_emails: campaign.verify_emails
    });
    setDialogOpen(true);
  };

  const handleDelete = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) return;
    
    try {
      await API.deleteCampaign(campaignId);
      toast.success('Campaign deleted successfully');
      loadCampaigns();
    } catch (error) {
      toast.error('Failed to delete campaign');
    }
  };

  const handleStart = async (campaignId) => {
    if (!window.confirm('Start this campaign? Emails will begin sending based on your schedule.')) return;
    
    try {
      await API.startCampaign(campaignId);
      toast.success('Campaign started successfully');
      loadCampaigns();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start campaign');
    }
  };

  const handlePause = async (campaignId) => {
    try {
      await API.pauseCampaign(campaignId);
      toast.success('Campaign paused');
      loadCampaigns();
    } catch (error) {
      toast.error('Failed to pause campaign');
    }
  };

  const handleResume = async (campaignId) => {
    try {
      await API.resumeCampaign(campaignId);
      toast.success('Campaign resumed');
      loadCampaigns();
    } catch (error) {
      toast.error('Failed to resume campaign');
    }
  };

  const handleStop = async (campaignId) => {
    if (!window.confirm('Stop this campaign permanently? This action cannot be undone.')) return;
    
    try {
      await API.stopCampaign(campaignId);
      toast.success('Campaign stopped');
      loadCampaigns();
    } catch (error) {
      toast.error('Failed to stop campaign');
    }
  };

  const handleViewAnalytics = (campaignId) => {
    navigate(`/campaign/analytics/${campaignId}`);
  };

  const handleContactSelection = (contactId) => {
    const newContactIds = formData.contact_ids.includes(contactId)
      ? formData.contact_ids.filter(id => id !== contactId)
      : [...formData.contact_ids, contactId];
    setFormData({ ...formData, contact_ids: newContactIds });
  };

  const handleListSelection = (listId) => {
    const newListIds = formData.list_ids.includes(listId)
      ? formData.list_ids.filter(id => id !== listId)
      : [...formData.list_ids, listId];
    setFormData({ ...formData, list_ids: newListIds });
  };

  const handleEmailAccountSelection = (accountId) => {
    const newAccountIds = formData.email_account_ids.includes(accountId)
      ? formData.email_account_ids.filter(id => id !== accountId)
      : [...formData.email_account_ids, accountId];
    setFormData({ ...formData, email_account_ids: newAccountIds });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      contact_ids: [],
      contact_tags: [],
      list_ids: [],
      initial_template_id: '',
      follow_up_config: {
        enabled: true,
        count: 3,
        intervals: [2, 4, 6],
        template_ids: []
      },
      email_account_ids: [],
      daily_limit_per_account: 100,
      random_delay_min: 60,
      random_delay_max: 300,
      scheduled_start: '',
      scheduled_end: '',
      timezone: 'UTC',
      verify_emails: false
    });
    setEditMode(false);
    setCurrentCampaign(null);
  };

  const handleDialogClose = (open) => {
    if (!open) {
      resetForm();
    }
    setDialogOpen(open);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading campaigns...</div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Send className="w-8 h-8 text-purple-600" />
            Campaigns
          </h1>
          <p className="text-gray-500 mt-1">Create and manage your email campaigns</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600">
              <Plus className="w-4 h-4" />
              Create Campaign
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editMode ? 'Edit Campaign' : 'Create New Campaign'}</DialogTitle>
              <DialogDescription>
                {editMode ? 'Update campaign settings and configuration' : 'Set up a new email campaign'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Campaign Name *</Label>
                    <Input
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Q1 Outreach Campaign"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Description</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Brief description of this campaign..."
                      rows={2}
                    />
                  </div>
                </div>
              </div>

              {/* Contact Lists Selection */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Select Contact Lists (Recommended)</h3>
                {contactLists.length === 0 ? (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-blue-600" />
                    <span className="text-sm text-blue-800">No contact lists available. Create lists to organize your contacts easily.</span>
                  </div>
                ) : (
                  <div className="border rounded-lg p-4 max-h-48 overflow-y-auto">
                    {contactLists.map((list) => (
                      <label key={list.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.list_ids.includes(list.id)}
                          onChange={() => handleListSelection(list.id)}
                          className="rounded"
                        />
                        <span className="text-sm flex items-center gap-2 flex-1">
                          <Users className="w-4 h-4 text-blue-600" />
                          {list.name}
                          <span className="text-gray-500">({list.total_contacts} contacts)</span>
                        </span>
                      </label>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-500">{formData.list_ids.length} lists selected</p>
              </div>

              {/* Individual Contacts Selection */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Or Select Individual Contacts</h3>
                {contacts.length === 0 ? (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600" />
                    <span className="text-sm text-yellow-800">No contacts available. Please add contacts first.</span>
                  </div>
                ) : (
                  <div className="border rounded-lg p-4 max-h-48 overflow-y-auto">
                    {contacts.slice(0, 20).map((contact) => (
                      <label key={contact.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.contact_ids.includes(contact.id)}
                          onChange={() => handleContactSelection(contact.id)}
                          className="rounded"
                        />
                        <span className="text-sm">
                          {contact.first_name || contact.last_name ? `${contact.first_name || ''} ${contact.last_name || ''}`.trim() : contact.email}
                          <span className="text-gray-500 ml-2">({contact.email})</span>
                        </span>
                      </label>
                    ))}
                    {contacts.length > 20 && (
                      <p className="text-xs text-gray-500 mt-2">Showing first 20 contacts. {contacts.length - 20} more available.</p>
                    )}
                  </div>
                )}
                <p className="text-xs text-gray-500">{formData.contact_ids.length} individual contacts selected</p>
              </div>

              {/* Template Selection */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Email Template</h3>
                {templates.length === 0 ? (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600" />
                    <span className="text-sm text-yellow-800">No templates available. Please create a template first.</span>
                  </div>
                ) : (
                  <div>
                    <Label>Initial Template *</Label>
                    <select
                      required
                      value={formData.initial_template_id}
                      onChange={(e) => setFormData({ ...formData, initial_template_id: e.target.value })}
                      className="w-full p-2 border rounded-lg"
                    >
                      <option value="">Select a template...</option>
                      {templates.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.name} - {template.subject}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Follow-up Configuration */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Follow-up Settings</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Follow-up Count</Label>
                    <Input
                      type="number"
                      min="0"
                      max="10"
                      value={formData.follow_up_config.count}
                      onChange={(e) => {
                        const count = parseInt(e.target.value);
                        const newTemplateIds = [...formData.follow_up_config.template_ids];
                        // Adjust template_ids array to match count
                        if (count > newTemplateIds.length) {
                          // Add empty slots
                          while (newTemplateIds.length < count) {
                            newTemplateIds.push('');
                          }
                        } else if (count < newTemplateIds.length) {
                          // Remove extra slots
                          newTemplateIds.length = count;
                        }
                        setFormData({
                          ...formData,
                          follow_up_config: { 
                            ...formData.follow_up_config, 
                            count: count,
                            template_ids: newTemplateIds
                          }
                        });
                      }}
                    />
                  </div>
                  <div>
                    <Label>Intervals (days, comma-separated)</Label>
                    <Input
                      value={formData.follow_up_config.intervals.join(', ')}
                      onChange={(e) => setFormData({
                        ...formData,
                        follow_up_config: {
                          ...formData.follow_up_config,
                          intervals: e.target.value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v))
                        }
                      })}
                      placeholder="2, 4, 6"
                    />
                  </div>
                </div>

                {/* Follow-up Template Selection */}
                {formData.follow_up_config.count > 0 && (
                  <div className="space-y-3 mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700">Select Templates for Each Follow-up</h4>
                    {Array.from({ length: formData.follow_up_config.count }).map((_, index) => (
                      <div key={index} className="space-y-2">
                        <Label>Follow-up {index + 1} Template (after {formData.follow_up_config.intervals[index] || 0} days)</Label>
                        <select
                          className="w-full border border-gray-300 rounded-md p-2 text-sm"
                          value={formData.follow_up_config.template_ids[index] || ''}
                          onChange={(e) => {
                            const newTemplateIds = [...formData.follow_up_config.template_ids];
                            newTemplateIds[index] = e.target.value;
                            setFormData({
                              ...formData,
                              follow_up_config: {
                                ...formData.follow_up_config,
                                template_ids: newTemplateIds
                              }
                            });
                          }}
                        >
                          <option value="">Select a template...</option>
                          {templates
                            .filter(t => t.template_type.includes('follow_up') || t.template_type === 'initial')
                            .map((template) => (
                              <option key={template.id} value={template.id}>
                                {template.name} ({template.template_type})
                              </option>
                            ))}
                        </select>
                      </div>
                    ))}
                    {formData.follow_up_config.template_ids.some(id => !id) && (
                      <p className="text-xs text-amber-600 mt-2">
                        ⚠️ Please select templates for all follow-ups to enable automatic follow-up sending
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Email Accounts */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Email Accounts</h3>
                {emailAccounts.length === 0 ? (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600" />
                    <span className="text-sm text-yellow-800">No email accounts connected. Please connect an OAuth Gmail account first.</span>
                  </div>
                ) : (
                  <div className="border rounded-lg p-4">
                    {emailAccounts.map((account) => (
                      <label key={account.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.email_account_ids.includes(account.id)}
                          onChange={() => handleEmailAccountSelection(account.id)}
                          className="rounded"
                        />
                        <span className="text-sm">{account.email}</span>
                      </label>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-500">{formData.email_account_ids.length} accounts selected</p>
              </div>

              {/* Rate Limiting */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Rate Limiting & Delays</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Daily Limit per Account</Label>
                    <Input
                      type="number"
                      min="1"
                      max="1000"
                      value={formData.daily_limit_per_account}
                      onChange={(e) => setFormData({ ...formData, daily_limit_per_account: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Min Delay (seconds)</Label>
                    <Input
                      type="number"
                      min="10"
                      value={formData.random_delay_min}
                      onChange={(e) => setFormData({ ...formData, random_delay_min: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Max Delay (seconds)</Label>
                    <Input
                      type="number"
                      min="10"
                      value={formData.random_delay_max}
                      onChange={(e) => setFormData({ ...formData, random_delay_max: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* Scheduling */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Schedule (Optional)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Start Date & Time</Label>
                    <Input
                      type="datetime-local"
                      value={formData.scheduled_start}
                      onChange={(e) => setFormData({ ...formData, scheduled_start: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>End Date & Time</Label>
                    <Input
                      type="datetime-local"
                      value={formData.scheduled_end}
                      onChange={(e) => setFormData({ ...formData, scheduled_end: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => handleDialogClose(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={contacts.length === 0 || templates.length === 0 || emailAccounts.length === 0}>
                  {editMode ? 'Update Campaign' : 'Create Campaign'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search campaigns by name, description, or status..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Total Campaigns</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">{campaigns.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Running</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">
              {campaigns.filter(c => c.status === 'running').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Paused</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-yellow-600">
              {campaigns.filter(c => c.status === 'paused').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gray-600">
              {campaigns.filter(c => c.status === 'completed' || c.status === 'stopped').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Campaigns List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredCampaigns.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Send className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchQuery ? 'No campaigns match your search' : 'No campaigns yet. Create your first campaign to get started.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredCampaigns.map((campaign) => (
            <Card key={campaign.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">{campaign.name}</h3>
                      {getStatusBadge(campaign.status)}
                    </div>
                    {campaign.description && (
                      <p className="text-sm text-gray-600 mb-3">{campaign.description}</p>
                    )}
                    
                    {/* Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Contacts</p>
                          <p className="font-semibold">{campaign.total_contacts || campaign.contact_ids.length}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Sent</p>
                          <p className="font-semibold text-green-600">{campaign.emails_sent}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Pending</p>
                          <p className="font-semibold text-yellow-600">{campaign.emails_pending}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Reply Rate</p>
                          <p className="font-semibold text-purple-600">
                            {campaign.emails_sent > 0 ? Math.round((campaign.emails_replied / campaign.emails_sent) * 100) : 0}%
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                      <span>Accounts: {campaign.email_account_ids.length}</span>
                      <span>•</span>
                      <span>Limit: {campaign.daily_limit_per_account}/day</span>
                      <span>•</span>
                      <span>Delay: {campaign.random_delay_min}-{campaign.random_delay_max}s</span>
                      {campaign.follow_up_config.enabled && (
                        <>
                          <span>•</span>
                          <span>Follow-ups: {campaign.follow_up_config.count}</span>
                        </>
                      )}
                    </div>
                    
                    <p className="text-xs text-gray-400 mt-2">
                      Created: {new Date(campaign.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex flex-col gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewAnalytics(campaign.id)}
                      className="text-purple-600 hover:text-purple-700 hover:bg-purple-50 justify-start"
                    >
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Analytics
                    </Button>
                    
                    {campaign.status === 'draft' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleStart(campaign.id)}
                        className="text-green-600 hover:text-green-700 hover:bg-green-50 justify-start"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Start
                      </Button>
                    )}
                    
                    {campaign.status === 'running' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handlePause(campaign.id)}
                        className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50 justify-start"
                      >
                        <Pause className="w-4 h-4 mr-2" />
                        Pause
                      </Button>
                    )}
                    
                    {campaign.status === 'paused' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleResume(campaign.id)}
                        className="text-green-600 hover:text-green-700 hover:bg-green-50 justify-start"
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Resume
                      </Button>
                    )}
                    
                    {(campaign.status === 'running' || campaign.status === 'paused') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleStop(campaign.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 justify-start"
                      >
                        <Square className="w-4 h-4 mr-2" />
                        Stop
                      </Button>
                    )}
                    
                    {(campaign.status === 'draft' || campaign.status === 'scheduled') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(campaign)}
                        className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 justify-start"
                      >
                        <Edit className="w-4 h-4 mr-2" />
                        Edit
                      </Button>
                    )}
                    
                    {(campaign.status === 'draft' || campaign.status === 'completed' || campaign.status === 'stopped') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(campaign.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 justify-start"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default Campaigns;
