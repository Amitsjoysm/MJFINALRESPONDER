import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { UserPlus, Clock, Trash2, CheckCircle2, XCircle, Eye, Mail, Calendar, User, MessageSquare } from 'lucide-react';
import { format } from 'date-fns';

const FollowUps = () => {
  const [followUps, setFollowUps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFollowUp, setSelectedFollowUp] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  useEffect(() => {
    loadFollowUps();
  }, []);

  const loadFollowUps = async () => {
    try {
      const data = await API.getFollowUps();
      setFollowUps(data);
    } catch (error) {
      toast.error('Failed to load follow-ups');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (followUpId) => {
    if (!window.confirm('Are you sure you want to cancel this follow-up?')) return;
    
    try {
      await API.deleteFollowUp(followUpId);
      toast.success('Follow-up cancelled');
      loadFollowUps();
      setShowDetailsModal(false);
    } catch (error) {
      toast.error('Failed to cancel follow-up');
    }
  };

  const handleViewDetails = async (followUpId) => {
    setDetailsLoading(true);
    setShowDetailsModal(true);
    try {
      const details = await API.getFollowUp(followUpId);
      setSelectedFollowUp(details);
    } catch (error) {
      toast.error('Failed to load follow-up details');
      setShowDetailsModal(false);
    } finally {
      setDetailsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'sent') {
      return (
        <Badge className="bg-green-500">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Sent
        </Badge>
      );
    }
    if (status === 'cancelled') {
      return (
        <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" />
          Cancelled
        </Badge>
      );
    }
    return (
      <Badge className="bg-blue-500">
        <Clock className="w-3 h-3 mr-1" />
        Scheduled
      </Badge>
    );
  };

  const stats = {
    total: followUps.length,
    scheduled: followUps.filter(f => f.status === 'pending').length,
    sent: followUps.filter(f => f.status === 'sent').length,
    cancelled: followUps.filter(f => f.status === 'cancelled').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading follow-ups...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Follow-ups</h1>
        <p className="text-gray-600 mt-1">Manage scheduled follow-up emails</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-700">Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900">Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900">{stats.scheduled}</div>
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
            <CardTitle className="text-sm font-medium text-red-900">Cancelled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-900">{stats.cancelled}</div>
          </CardContent>
        </Card>
      </div>

      {/* Follow-ups List */}
      {followUps.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <UserPlus className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Follow-ups</h3>
            <p className="text-gray-600 text-center">
              Follow-ups are automatically scheduled based on email responses
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {followUps.map((followUp) => (
            <Card key={followUp.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle className="text-lg">{followUp.subject}</CardTitle>
                      {getStatusBadge(followUp.status)}
                    </div>
                    <CardDescription className="space-y-1">
                      {followUp.original_email && (
                        <>
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4" />
                            <span>Original: {followUp.original_email.subject}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4" />
                            <span>From: {followUp.original_email.from_email}</span>
                          </div>
                        </>
                      )}
                      {followUp.scheduled_at && (
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4" />
                          <span>Scheduled: {format(new Date(followUp.scheduled_at), 'MMM dd, yyyy HH:mm')}</span>
                        </div>
                      )}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {followUp.body && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-900 whitespace-pre-wrap line-clamp-3">
                      {followUp.body}
                    </p>
                  </div>
                )}

                <div className="flex items-center justify-between pt-2 border-t gap-2">
                  <div className="text-sm text-gray-600">
                    {followUp.status === 'sent' && followUp.sent_at && (
                      <span>Sent: {format(new Date(followUp.sent_at), 'MMM dd, yyyy HH:mm')}</span>
                    )}
                    {followUp.status === 'cancelled' && followUp.cancelled_reason && (
                      <span className="text-red-600">Cancelled: {followUp.cancelled_reason}</span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewDetails(followUp.id)}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Details
                    </Button>
                    {followUp.status === 'pending' && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDelete(followUp.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Follow-up Details</DialogTitle>
            <DialogDescription>
              Complete information about this follow-up email
            </DialogDescription>
          </DialogHeader>

          {detailsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-500">Loading details...</div>
            </div>
          ) : selectedFollowUp ? (
            <div className="space-y-6">
              {/* Status and Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-700">Status</Label>
                  <div className="mt-2">{getStatusBadge(selectedFollowUp.status)}</div>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-700">Thread ID</Label>
                  <div className="mt-2 text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded border">
                    {selectedFollowUp.thread_id || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Timing Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Scheduled At
                  </Label>
                  <div className="mt-2 text-sm text-gray-900">
                    {format(new Date(selectedFollowUp.scheduled_at), 'MMMM dd, yyyy HH:mm:ss')}
                  </div>
                </div>
                {selectedFollowUp.sent_at && (
                  <div>
                    <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Sent At
                    </Label>
                    <div className="mt-2 text-sm text-gray-900">
                      {format(new Date(selectedFollowUp.sent_at), 'MMMM dd, yyyy HH:mm:ss')}
                    </div>
                  </div>
                )}
              </div>

              {/* Follow-up Content */}
              <div>
                <Label className="text-sm font-medium text-gray-700">Subject</Label>
                <div className="mt-2 text-sm text-gray-900 bg-gray-50 p-3 rounded border">
                  {selectedFollowUp.subject}
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Follow-up Message
                </Label>
                <div className="mt-2 text-sm text-gray-900 bg-gray-50 p-4 rounded border whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {selectedFollowUp.body || 'No message content'}
                </div>
              </div>

              {/* Cancellation Reason */}
              {selectedFollowUp.status === 'cancelled' && selectedFollowUp.cancelled_reason && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <Label className="text-sm font-medium text-red-900 flex items-center gap-2">
                    <XCircle className="w-4 h-4" />
                    Cancellation Reason
                  </Label>
                  <div className="mt-2 text-sm text-red-700">
                    {selectedFollowUp.cancelled_reason}
                  </div>
                </div>
              )}

              {/* Original Email */}
              {selectedFollowUp.original_email && (
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4">Original Email</h3>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-medium text-gray-700">From</Label>
                        <div className="mt-2 text-sm text-gray-900">
                          {selectedFollowUp.original_email.from_email}
                        </div>
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-gray-700">Received At</Label>
                        <div className="mt-2 text-sm text-gray-900">
                          {selectedFollowUp.original_email.received_at ? 
                            format(new Date(selectedFollowUp.original_email.received_at), 'MMM dd, yyyy HH:mm') 
                            : 'N/A'}
                        </div>
                      </div>
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-gray-700">Subject</Label>
                      <div className="mt-2 text-sm text-gray-900 bg-blue-50 p-3 rounded border border-blue-200">
                        {selectedFollowUp.original_email.subject}
                      </div>
                    </div>

                    {selectedFollowUp.original_email.intent_name && (
                      <div>
                        <Label className="text-sm font-medium text-gray-700">Detected Intent</Label>
                        <div className="mt-2">
                          <Badge className="bg-purple-500">
                            {selectedFollowUp.original_email.intent_name}
                          </Badge>
                        </div>
                      </div>
                    )}

                    <div>
                      <Label className="text-sm font-medium text-gray-700">Original Message</Label>
                      <div className="mt-2 text-sm text-gray-900 bg-blue-50 p-4 rounded border border-blue-200 whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {selectedFollowUp.original_email.body || 'No content'}
                      </div>
                    </div>

                    {selectedFollowUp.original_email.replied && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="flex items-center gap-2 text-green-700">
                          <CheckCircle2 className="w-4 h-4" />
                          <span className="text-sm font-medium">Auto-reply was sent for this email</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Email Account Info */}
              {selectedFollowUp.email_account && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <Label className="text-sm font-medium text-gray-700">Email Account</Label>
                  <div className="mt-2 text-sm text-gray-900">
                    {selectedFollowUp.email_account.email}
                    <Badge className="ml-2" variant="outline">
                      {selectedFollowUp.email_account.account_type}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                {selectedFollowUp.status === 'pending' && (
                  <Button
                    variant="destructive"
                    onClick={() => handleDelete(selectedFollowUp.id)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Cancel Follow-up
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={() => setShowDetailsModal(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FollowUps;