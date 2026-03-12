import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  Zap, Send, CheckCircle2, AlertCircle, Mail, Target, Users, Calendar, 
  MessageSquare, TrendingUp, Clock, X, Check, AlertTriangle, Info,
  ArrowRight, Trash2, Play, RefreshCw
} from 'lucide-react';

const TestEmail = () => {
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [isReply, setIsReply] = useState(false);
  
  const [formData, setFormData] = useState({
    from_email: 'john.doe@techcompany.com',
    subject: 'Interested in pricing for our company',
    body: `Hi there,\n\nI'm interested in learning more about your pricing plans for our company.\n\nWe're a tech startup and we're looking for an email automation solution.\n\nCould you provide more details?\n\nThanks,\nJohn Doe\nCEO`
  });

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const status = await API.getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const handleSendMessage = async () => {
    setLoading(true);
    try {
      const response = await API.sendTestMessage({
        session_id: sessionId,
        from_email: formData.from_email,
        subject: formData.subject,
        body: formData.body,
        is_reply: isReply
      });
      
      setSessionId(response.session_id);
      setSessionData(response);
      setIsReply(true);  // Next message will be a reply
      
      // Clear body for next reply
      setFormData({
        ...formData,
        body: ''
      });
      
      toast.success('Message sent and processed!');
    } catch (error) {
      toast.error('Failed to send message: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    setSessionId(null);
    setSessionData(null);
    setIsReply(false);
    setFormData({
      from_email: 'john.doe@techcompany.com',
      subject: 'Interested in pricing for our company',
      body: `Hi there,\n\nI'm interested in learning more about your pricing plans for our company.\n\nWe're a tech startup and we're looking for an email automation solution.\n\nCould you provide more details?\n\nThanks,\nJohn Doe\nCEO`
    });
    toast.success('New test session started');
  };

  const handleDeleteSession = async () => {
    if (!sessionId) return;
    
    try {
      await API.deleteTestSession(sessionId);
      handleNewSession();
      toast.success('Test session deleted');
    } catch (error) {
      toast.error('Failed to delete session');
    }
  };

  const getActionIcon = (action) => {
    const icons = {
      intent_classified: <Target className="w-4 h-4" />,
      lead_processed: <Users className="w-4 h-4" />,
      followups_cancelled: <X className="w-4 h-4" />,
      meeting_detected: <Calendar className="w-4 h-4" />,
      draft_generated: <MessageSquare className="w-4 h-4" />,
      draft_validated: <CheckCircle2 className="w-4 h-4" />,
      followups_created: <Clock className="w-4 h-4" />
    };
    return icons[action] || <Info className="w-4 h-4" />;
  };

  const getActionColor = (action) => {
    const colors = {
      intent_classified: 'bg-blue-100 text-blue-700',
      lead_processed: 'bg-purple-100 text-purple-700',
      followups_cancelled: 'bg-red-100 text-red-700',
      meeting_detected: 'bg-green-100 text-green-700',
      draft_generated: 'bg-pink-100 text-pink-700',
      draft_validated: 'bg-emerald-100 text-emerald-700',
      followups_created: 'bg-amber-100 text-amber-700'
    };
    return colors[action] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🧪 Interactive Flow Test</h1>
          <p className="text-gray-600 mt-1">
            Test complete email conversations with full visibility into all agent actions
          </p>
        </div>
        {sessionId && (
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleNewSession}>
              <RefreshCw className="w-4 h-4 mr-2" />
              New Session
            </Button>
            <Button variant="outline" onClick={handleDeleteSession} className="text-red-600">
              <Trash2 className="w-4 h-4 mr-2" />
              Delete Session
            </Button>
          </div>
        )}
      </div>

      {/* System Status */}
      {systemStatus && (
        <Card className={systemStatus.ready ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              {systemStatus.ready ? (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              )}
              System Ready: {systemStatus.ready ? 'Yes' : 'Configuration Needed'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-white rounded p-2 border">
                <p className="text-xs text-gray-600">Intents</p>
                <p className="text-lg font-bold">{systemStatus.configuration.intents}</p>
              </div>
              <div className="bg-white rounded p-2 border">
                <p className="text-xs text-gray-600">Knowledge Base</p>
                <p className="text-lg font-bold">{systemStatus.configuration.knowledge_base}</p>
              </div>
              <div className="bg-white rounded p-2 border">
                <p className="text-xs text-gray-600">Qualification</p>
                <Badge className={systemStatus.configuration.global_qualification_enabled ? 'bg-green-500' : 'bg-gray-400'}>
                  {systemStatus.configuration.global_qualification_enabled ? 'ON' : 'OFF'}
                </Badge>
              </div>
              <div className="bg-white rounded p-2 border">
                <p className="text-xs text-gray-600">Nurturing</p>
                <Badge className={systemStatus.configuration.global_nurturing_enabled ? 'bg-green-500' : 'bg-gray-400'}>
                  {systemStatus.configuration.global_nurturing_enabled ? 'ON' : 'OFF'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Summary */}
      {sessionData && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader>
            <CardTitle className="text-sm">Test Session Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Messages</p>
                <p className="text-xl font-bold">{sessionData.summary.total_messages}</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Active Follow-ups</p>
                <p className="text-xl font-bold text-green-600">{sessionData.summary.active_followups}</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Cancelled Follow-ups</p>
                <p className="text-xl font-bold text-red-600">{sessionData.summary.cancelled_followups}</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Calendar Events</p>
                <p className="text-xl font-bold text-blue-600">{sessionData.summary.calendar_events}</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Lead Stage</p>
                <p className="text-sm font-bold">{sessionData.summary.lead_stage || 'N/A'}</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Lead Score</p>
                <p className="text-xl font-bold text-purple-600">{sessionData.summary.lead_score || 0}/100</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Message Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-purple-600" />
            {isReply ? 'Send Reply Message' : 'Send Initial Email'}
          </CardTitle>
          <CardDescription>
            {sessionId ? `Session ${sessionId.slice(0, 8)}... - Continue the conversation` : 'Start a new test conversation'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="from_email">From Email {isReply && '(same as previous)'}</Label>
            <Input
              id="from_email"
              value={formData.from_email}
              onChange={(e) => setFormData({...formData, from_email: e.target.value})}
              placeholder="john.doe@company.com"
              disabled={isReply}
            />
          </div>

          {!isReply && (
            <div>
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                value={formData.subject}
                onChange={(e) => setFormData({...formData, subject: e.target.value})}
                placeholder="Email subject"
              />
            </div>
          )}

          <div>
            <Label htmlFor="body">
              {isReply ? 'Reply Message' : 'Email Body'}
              {sessionData?.lead_info?.stage === 'awaiting_info' && (
                <span className="text-purple-600 font-medium ml-2">(Answer the qualification questions above)</span>
              )}
            </Label>
            <Textarea
              id="body"
              value={formData.body}
              onChange={(e) => setFormData({...formData, body: e.target.value})}
              placeholder={isReply ? "Your reply message..." : "Email content..."}
              rows={isReply ? 6 : 10}
            />
          </div>

          <div className="flex gap-3">
            <Button 
              onClick={handleSendMessage} 
              disabled={loading || !systemStatus?.ready || !formData.body}
              className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              {loading ? (
                <>
                  <Zap className="w-4 h-4 mr-2 animate-pulse" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  {isReply ? 'Send Reply & Continue Flow' : 'Send Email & Start Flow'}
                </>
              )}
            </Button>
            
            {sessionId && (
              <Button variant="outline" onClick={handleNewSession}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Conversation History */}
      {sessionData?.conversation_history && sessionData.conversation_history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-600" />
              Conversation History ({sessionData.conversation_history.length} messages)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sessionData.conversation_history.map((msg, idx) => (
              <div key={idx} className={`border rounded-lg p-4 ${
                msg.direction === 'inbound' ? 'bg-blue-50 border-blue-200' : 'bg-green-50 border-green-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge className={msg.direction === 'inbound' ? 'bg-blue-600' : 'bg-green-600'}>
                      {msg.direction === 'inbound' ? 'FROM CUSTOMER' : 'YOUR RESPONSE'}
                    </Badge>
                    <span className="text-xs text-gray-600">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-900 mb-1">{msg.subject}</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{msg.body}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Follow-ups */}
      {sessionData?.follow_ups && sessionData.follow_ups.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-600" />
              Follow-up Tasks ({sessionData.follow_ups.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sessionData.follow_ups.map((followup, idx) => (
                <div key={idx} className={`flex items-center justify-between p-3 rounded-lg border ${
                  followup.status === 'cancelled' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
                }`}>
                  <div className="flex items-center gap-3">
                    {followup.status === 'cancelled' ? (
                      <X className="w-5 h-5 text-red-600" />
                    ) : (
                      <Clock className="w-5 h-5 text-green-600" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Task ID: <code className="text-xs bg-white px-2 py-1 rounded">{followup.followup_id.slice(0, 8)}</code>
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        {followup.status === 'cancelled' ? (
                          <span className="text-red-700">Cancelled: {followup.reason}</span>
                        ) : (
                          <span>Scheduled: {followup.scheduled_date} ({followup.days_from_now} days from now)</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <Badge className={followup.status === 'cancelled' ? 'bg-red-500' : 'bg-green-500'}>
                    {followup.status.toUpperCase()}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lead Qualification Progress */}
      {sessionData?.lead_info && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              Lead Qualification Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-xs text-gray-600">Stage</p>
                <Badge className={
                  sessionData.lead_info.stage === 'qualified' ? 'bg-green-500' :
                  sessionData.lead_info.stage === 'unqualified' ? 'bg-red-500' :
                  sessionData.lead_info.stage === 'awaiting_info' ? 'bg-amber-500' :
                  'bg-blue-500'
                }>
                  {sessionData.lead_info.stage}
                </Badge>
              </div>
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-xs text-gray-600">Score</p>
                <p className="text-2xl font-bold text-purple-600">{sessionData.lead_info.score}/100</p>
              </div>
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-xs text-gray-600">Attempt</p>
                <p className="text-2xl font-bold">{sessionData.lead_info.attempt}/3</p>
              </div>
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-xs text-gray-600">Exchanges</p>
                <p className="text-2xl font-bold">{sessionData.lead_info.nurturing_exchanges}</p>
              </div>
            </div>
            
            {sessionData.lead_info.qualification_reasons && sessionData.lead_info.qualification_reasons.length > 0 && (
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-sm font-medium text-gray-900 mb-2">Qualification Analysis:</p>
                <div className="space-y-1">
                  {sessionData.lead_info.qualification_reasons.map((reason, idx) => (
                    <p key={idx} className="text-xs text-gray-700">• {reason}</p>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Calendar Events */}
      {sessionData?.calendar_events && sessionData.calendar_events.length > 0 && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-green-600" />
              Calendar Events ({sessionData.calendar_events.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sessionData.calendar_events.map((event, idx) => (
                <div key={idx} className="bg-white rounded-lg p-4 border border-green-200">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-semibold text-gray-900">{event.title}</p>
                      <p className="text-sm text-gray-600 mt-1">{event.start_time}</p>
                    </div>
                    <Badge className="bg-green-500">Created</Badge>
                  </div>
                  <div className="space-y-1 text-sm text-gray-700">
                    <p>📅 Duration: {event.duration} minutes</p>
                    <p>👥 Attendees: {event.attendees.join(', ')}</p>
                    <p>🔗 <a href={event.meet_link} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{event.meet_link}</a></p>
                    <p>⏰ Reminder: {event.reminder_time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Actions */}
      {sessionData?.agent_actions && sessionData.agent_actions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-600" />
              Agent Actions ({sessionData.agent_actions.length})
            </CardTitle>
            <CardDescription>All automated decisions and actions taken by the system</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sessionData.agent_actions.map((action, idx) => (
                <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg ${getActionColor(action.action)}`}>
                  <div className="mt-0.5">
                    {getActionIcon(action.action)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{action.action.replace(/_/g, ' ').toUpperCase()}</p>
                      <span className="text-xs opacity-75">{new Date(action.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="mt-2 space-y-1">
                      {Object.entries(action.details).map(([key, value]) => {
                        if (key === 'draft' || key === 'questions') return null;  // Skip large content
                        return (
                          <p key={key} className="text-sm">
                            <span className="opacity-75">{key.replace(/_/g, ' ')}:</span>{' '}
                            <span className="font-medium">
                              {Array.isArray(value) ? value.join(', ') : 
                               typeof value === 'boolean' ? (value ? '✓ Yes' : '✗ No') :
                               typeof value === 'object' ? JSON.stringify(value) :
                               value}
                            </span>
                          </p>
                        );
                      })}
                      
                      {/* Show draft in expandable section */}
                      {action.details.draft && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-sm font-medium hover:underline">
                            View Generated Draft ({action.details.length} chars)
                          </summary>
                          <div className="mt-2 p-3 bg-white bg-opacity-50 rounded border text-sm whitespace-pre-wrap">
                            {action.details.draft}
                          </div>
                        </details>
                      )}
                      
                      {/* Show questions */}
                      {action.details.questions && action.details.questions.length > 0 && (
                        <div className="mt-2 p-2 bg-white bg-opacity-50 rounded border">
                          <p className="text-sm font-medium mb-1">Questions Asked:</p>
                          {action.details.questions.map((q, i) => (
                            <p key={i} className="text-sm">• {q}</p>
                          ))}
                        </div>
                      )}
                      
                      {/* Show followup IDs */}
                      {action.details.followup_ids && action.details.followup_ids.length > 0 && (
                        <div className="mt-2 p-2 bg-white bg-opacity-50 rounded border">
                          <p className="text-sm font-medium mb-1">Task IDs:</p>
                          {action.details.followup_ids.map((id, i) => (
                            <code key={i} className="text-xs block bg-white px-2 py-1 rounded mb-1">{id}</code>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      {sessionData && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-sm text-blue-900">Quick Test Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button
                variant="outline"
                className="bg-white"
                onClick={() => setFormData({
                  ...formData,
                  body: `Company size: 75 employees\nBudget: $10,000 per month\nIndustry: Technology/SaaS\nTimeline: 2-3 months`
                })}
              >
                📝 Answer Qualification Questions
              </Button>
              <Button
                variant="outline"
                className="bg-white"
                onClick={() => setFormData({
                  ...formData,
                  body: `Sounds good! Can we schedule a call next Tuesday at 2 PM to discuss further?`
                })}
              >
                📅 Request Meeting
              </Button>
              <Button
                variant="outline"
                className="bg-white"
                onClick={() => setFormData({
                  ...formData,
                  body: `Actually, I need to reschedule. Can we do Wednesday at 3 PM instead?`
                })}
              >
                🔄 Reschedule Meeting
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-sm">How This Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-700">
            <p>✓ <strong>Send Initial Email</strong> → System responds + creates follow-up tasks</p>
            <p>✓ <strong>Send Reply</strong> → Follow-ups auto-cancelled + new response + new follow-ups</p>
            <p>✓ <strong>Answer Questions</strong> → Lead scored 0-100 → Qualified/Disqualified</p>
            <p>✓ <strong>Request Meeting</strong> → Calendar event created + reminder scheduled</p>
            <p>✓ <strong>Reschedule</strong> → Event updated + new reminders</p>
            <p className="text-gray-900 font-medium mt-3">💡 All agent actions are visible in real-time. No actual emails sent. Test data auto-cleaned.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TestEmail;
