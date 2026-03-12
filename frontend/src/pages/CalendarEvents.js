import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { Calendar, Clock, MapPin, Users, CheckCircle2, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

const CalendarEvents = () => {
  const [events, setEvents] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [allEvents, upcoming] = await Promise.all([
        API.getCalendarEvents(),
        API.getUpcomingEvents(24)
      ]);
      setEvents(allEvents);
      setUpcomingEvents(upcoming);
    } catch (error) {
      toast.error('Failed to load calendar events');
    } finally {
      setLoading(false);
    }
  };

  const getEventBadge = (event) => {
    if (event.detected_from_email) {
      return (
        <Badge className="bg-blue-500">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          AI Detected
        </Badge>
      );
    }
    return <Badge variant="secondary">Manual</Badge>;
  };

  const displayEvents = activeTab === 'upcoming' ? upcomingEvents : events;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading calendar events...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Calendar Events</h1>
        <p className="text-gray-600 mt-1">View and manage your calendar events</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900">Total Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900">{events.length}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-900">Upcoming (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-900">{upcomingEvents.length}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-900">AI Detected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-900">
              {events.filter(e => e.detected_from_email).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="all">All Events ({events.length})</TabsTrigger>
          <TabsTrigger value="upcoming">Upcoming 24h ({upcomingEvents.length})</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4 mt-6">
          {displayEvents.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Calendar className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Events Found</h3>
                <p className="text-gray-600 text-center">
                  Calendar events will appear here once detected from emails or created manually
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {displayEvents.map((event) => (
                <Card key={event.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{event.title}</CardTitle>
                        <div className="flex items-center gap-2 mt-2">
                          {getEventBadge(event)}
                          {event.confidence && (
                            <Badge variant="outline" className="text-xs">
                              Confidence: {(event.confidence * 100).toFixed(0)}%
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-start gap-2 text-sm">
                      <Clock className="w-4 h-4 text-gray-500 mt-0.5" />
                      <div>
                        <p className="text-gray-900 font-medium">
                          {event.start_time && format(new Date(event.start_time), 'MMM dd, yyyy HH:mm')}
                        </p>
                        <p className="text-gray-600 text-xs">
                          to {event.end_time && format(new Date(event.end_time), 'HH:mm')}
                        </p>
                      </div>
                    </div>

                    {event.location && (
                      <div className="flex items-start gap-2 text-sm">
                        <MapPin className="w-4 h-4 text-gray-500 mt-0.5" />
                        <p className="text-gray-700">{event.location}</p>
                      </div>
                    )}

                    {event.description && (
                      <div className="text-sm text-gray-600">
                        <p className="line-clamp-2">{event.description}</p>
                      </div>
                    )}

                    {event.attendees && event.attendees.length > 0 && (
                      <div className="flex items-start gap-2 text-sm">
                        <Users className="w-4 h-4 text-gray-500 mt-0.5" />
                        <p className="text-gray-700">{event.attendees.length} attendee(s)</p>
                      </div>
                    )}

                    {event.reminder_sent && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-2">
                        <p className="text-xs text-green-800">
                          <CheckCircle2 className="w-3 h-3 inline mr-1" />
                          Reminder sent
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CalendarEvents;