import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Mail, Send, Clock, CheckCircle2, XCircle, Eye, RefreshCw, Search, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';

const EmailProcessing = () => {
  const [emails, setEmails] = useState([]);
  const [filteredEmails, setFilteredEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadEmails();
  }, []);

  useEffect(() => {
    filterEmails();
  }, [emails, activeTab, searchQuery]);

  const loadEmails = async () => {
    try {
      const data = await API.getEmails();
      setEmails(data);
    } catch (error) {
      toast.error('Failed to load emails');
    } finally {
      setLoading(false);
    }
  };

  const filterEmails = () => {
    let filtered = emails;

    // Filter by tab
    if (activeTab === 'pending') {
      filtered = filtered.filter(e => e.status === 'draft_ready');
    } else if (activeTab === 'sent') {
      filtered = filtered.filter(e => e.status === 'sent');
    } else if (activeTab === 'escalated') {
      filtered = filtered.filter(e => e.status === 'escalated');
    }

    // Filter by search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        e =>
          e.subject?.toLowerCase().includes(query) ||
          e.from_email?.toLowerCase().includes(query) ||
          e.body?.toLowerCase().includes(query)
      );
    }

    setFilteredEmails(filtered);
  };

  const handleViewEmail = (email) => {
    setSelectedEmail(email);
    setViewDialogOpen(true);
  };

  const handleApproveDraft = async (emailId) => {
    try {
      await API.approveDraft(emailId);
      toast.success('Draft approved and sent');
      loadEmails();
      setViewDialogOpen(false);
    } catch (error) {
      toast.error('Failed to approve draft');
    }
  };

  const handleReprocess = async (emailId) => {
    try {
      await API.reprocessEmail(emailId);
      toast.success('Email reprocessing started');
      setTimeout(loadEmails, 2000);
    } catch (error) {
      toast.error('Failed to reprocess email');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'classifying':
        return <Badge variant="secondary"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Classifying</Badge>;
      case 'drafting':
        return <Badge variant="secondary"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Drafting</Badge>;
      case 'validating':
        return <Badge variant="secondary"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Validating</Badge>;
      case 'sending':
        return <Badge variant="secondary"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Sending</Badge>;
      case 'draft_ready':
        return <Badge className="bg-blue-500"><Clock className="w-3 h-3 mr-1" />Pending Review</Badge>;
      case 'sent':
        return <Badge className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />Sent</Badge>;
      case 'escalated':
        return <Badge variant="destructive"><AlertTriangle className="w-3 h-3 mr-1" />Escalated</Badge>;
      case 'error':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Error</Badge>;
      case 'processing':
        return <Badge variant="secondary"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Processing</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const stats = {
    total: emails.length,
    pending: emails.filter(e => e.status === 'draft_ready').length,
    sent: emails.filter(e => e.status === 'sent').length,
    escalated: emails.filter(e => e.status === 'escalated').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading emails...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Email Processing</h1>
        <p className="text-gray-600 mt-1">View processed emails and manage drafts</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-700">Total Emails</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900">Pending Review</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900">{stats.pending}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-900">Sent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-900">{stats.sent}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-900">Escalated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-900">{stats.escalated}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              placeholder="Search emails by subject, sender, or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">All Emails</TabsTrigger>
          <TabsTrigger value="pending">Pending Review ({stats.pending})</TabsTrigger>
          <TabsTrigger value="sent">Sent ({stats.sent})</TabsTrigger>
          <TabsTrigger value="escalated">Escalated ({stats.escalated})</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4 mt-6">
          {filteredEmails.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Mail className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Emails Found</h3>
                <p className="text-gray-600 text-center">
                  {searchQuery ? 'Try adjusting your search query' : 'Emails will appear here once they are processed'}
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredEmails.map((email) => (
              <Card key={email.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <CardTitle className="text-lg">{email.subject || '(No Subject)'}</CardTitle>
                        {getStatusBadge(email.status)}
                        {email.intent_name && (
                          <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                            {email.intent_name}
                          </Badge>
                        )}
                      </div>
                      <CardDescription className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                          <Mail className="w-4 h-4" />
                          From: {email.from_email}
                        </span>
                        <span>
                          {email.received_at && format(new Date(email.received_at), 'MMM dd, yyyy HH:mm')}
                        </span>
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-700 line-clamp-2">{email.body}</p>
                  </div>

                  {email.draft && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Send className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900">AI Generated Draft</span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-3 whitespace-pre-wrap">{email.draft}</p>
                    </div>
                  )}

                  {email.validation_issues && email.validation_issues.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span className="text-sm font-medium text-amber-900">Validation Issues</span>
                      </div>
                      <ul className="text-xs text-amber-800 list-disc list-inside">
                        {email.validation_issues.map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex gap-2 pt-2 border-t">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewEmail(email)}
                      className="flex-1"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Details
                    </Button>
                    {email.status === 'draft_ready' && (
                      <Button
                        size="sm"
                        className="flex-1 bg-green-600 hover:bg-green-700"
                        onClick={() => handleApproveDraft(email.id)}
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Approve & Send
                      </Button>
                    )}
                    {(email.status === 'escalated' || email.status === 'failed') && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleReprocess(email.id)}
                        className="flex-1"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Reprocess
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* View Email Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Email Details & Processing History</DialogTitle>
          </DialogHeader>
          
          {selectedEmail && (
            <div className="space-y-6">
              {/* Processing Status Banner */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-700">Current Status:</span>
                    {getStatusBadge(selectedEmail.status)}
                  </div>
                  {selectedEmail.is_reply && (
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      Reply Received - Follow-ups Cancelled
                    </Badge>
                  )}
                </div>
                {selectedEmail.error_message && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                    <p className="text-sm text-red-700"><strong>Error:</strong> {selectedEmail.error_message}</p>
                  </div>
                )}
              </div>

              {/* Intent Detection */}
              {selectedEmail.intent_name && (
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-600" />
                    Intent Detected
                  </h3>
                  <div className="flex items-center gap-4">
                    <Badge variant="outline" className="bg-yellow-50">{selectedEmail.intent_name}</Badge>
                    <span className="text-sm text-gray-600">
                      Confidence: <strong>{(selectedEmail.intent_confidence * 100).toFixed(1)}%</strong>
                    </span>
                  </div>
                </div>
              )}

              {/* Meeting Detection */}
              {selectedEmail.meeting_detected && (
                <div className="border border-purple-200 rounded-lg p-4 bg-purple-50">
                  <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-purple-600" />
                    Meeting Detected
                  </h3>
                  <span className="text-sm text-gray-600">
                    Confidence: <strong>{(selectedEmail.meeting_confidence * 100).toFixed(1)}%</strong>
                  </span>
                </div>
              )}

              {/* Original Email */}
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Mail className="w-5 h-5" />
                  Original Email
                  {selectedEmail.thread_id && (
                    <Badge variant="outline" className="text-xs">Thread: {selectedEmail.thread_id.slice(0, 8)}</Badge>
                  )}
                </h3>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">From:</span>
                      <p className="text-gray-900">{selectedEmail.from_email}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Date:</span>
                      <p className="text-gray-900">
                        {selectedEmail.received_at && format(new Date(selectedEmail.received_at), 'MMM dd, yyyy HH:mm:ss')}
                      </p>
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700 text-sm">Subject:</span>
                    <p className="text-gray-900 mt-1">{selectedEmail.subject || '(No Subject)'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700 text-sm">Body:</span>
                    <p className="text-gray-900 mt-1 whitespace-pre-wrap">{selectedEmail.body}</p>
                  </div>
                </div>
              </div>

              {/* Draft Response */}
              {selectedEmail.draft_content && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Send className="w-5 h-5 text-blue-600" />
                    AI Generated Draft
                    {selectedEmail.draft_validated && (
                      <Badge className="bg-green-600">Validated</Badge>
                    )}
                    {!selectedEmail.draft_validated && selectedEmail.validation_issues?.length > 0 && (
                      <Badge variant="destructive">Validation Failed</Badge>
                    )}
                  </h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-gray-900 whitespace-pre-wrap">{selectedEmail.draft_content}</p>
                  </div>
                  {selectedEmail.validation_issues && selectedEmail.validation_issues.length > 0 && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm font-medium text-red-700 mb-2">Validation Issues:</p>
                      <ul className="list-disc list-inside text-sm text-red-600">
                        {selectedEmail.validation_issues.map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Action History Timeline */}
              {selectedEmail.action_history && selectedEmail.action_history.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Processing Timeline</h3>
                  <div className="space-y-3">
                    {selectedEmail.action_history.map((action, idx) => (
                      <div key={idx} className="flex gap-3 items-start">
                        <div className={`w-2 h-2 rounded-full mt-2 ${
                          action.status === 'success' ? 'bg-green-500' : 
                          action.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
                        }`} />
                        <div className="flex-1 border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm capitalize">{action.action.replace(/_/g, ' ')}</span>
                            <span className="text-xs text-gray-500">
                              {format(new Date(action.timestamp), 'HH:mm:ss')}
                            </span>
                          </div>
                          {Object.keys(action.details || {}).length > 0 && (
                            <div className="mt-2 text-xs text-gray-600">
                              {Object.entries(action.details).map(([key, value]) => (
                                <div key={key} className="flex gap-2">
                                  <span className="font-medium">{key}:</span>
                                  <span>{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status & Actions */}
              <div className="flex items-center justify-between pt-4 border-t">
                <div className="text-sm text-gray-600">
                  Processed: {selectedEmail.processed ? 'Yes' : 'No'} | 
                  Replied: {selectedEmail.replied ? 'Yes' : 'No'}
                </div>
                {selectedEmail.status === 'draft_ready' && (
                  <Button
                    onClick={() => handleApproveDraft(selectedEmail.id)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Approve & Send Draft
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EmailProcessing;
