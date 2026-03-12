import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Brain, CheckCircle2, Settings, Zap } from 'lucide-react';

const MeetingDetection = () => {
  const [threshold, setThreshold] = useState(0.6);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Meeting Detection</h1>
        <p className="text-gray-600 mt-1">Configure AI-powered meeting detection from emails</p>
      </div>

      {/* How it Works */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-600" />
            How Meeting Detection Works
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-gray-700">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <p><strong>AI Analysis:</strong> The Calendar Agent analyzes incoming emails to detect meeting-related content</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <p><strong>Date & Time Extraction:</strong> Automatically extracts exact date, time, and location details</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <p><strong>Calendar Creation:</strong> Creates events in your connected Google/Outlook calendar</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <p><strong>Conflict Detection:</strong> Checks for conflicts and handles rescheduling requests</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <p><strong>Auto-Reminders:</strong> Sends reminder emails 1 hour before meetings</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-600" />
            Detection Settings
          </CardTitle>
          <CardDescription>Configure how the AI detects and processes meetings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="threshold">Confidence Threshold</Label>
            <div className="flex items-center gap-4 mt-2">
              <Input
                id="threshold"
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="flex-1"
              />
              <Badge className="bg-purple-600 min-w-[60px] justify-center">
                {(threshold * 100).toFixed(0)}%
              </Badge>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Only create calendar events when AI confidence is above {(threshold * 100).toFixed(0)}%
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Zap className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900">Current Setting</p>
                <p className="text-sm text-blue-700 mt-1">
                  The Calendar Agent is actively monitoring emails and will automatically detect meetings with {(threshold * 100).toFixed(0)}% or higher confidence.
                </p>
              </div>
            </div>
          </div>

          <Button disabled className="w-full">
            Save Settings (Auto-saved)
          </Button>
        </CardContent>
      </Card>

      {/* Example Triggers */}
      <Card>
        <CardHeader>
          <CardTitle>Detection Keywords & Patterns</CardTitle>
          <CardDescription>The AI looks for these patterns in emails</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Meeting Keywords</h4>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">meeting</Badge>
                <Badge variant="secondary">call</Badge>
                <Badge variant="secondary">conference</Badge>
                <Badge variant="secondary">appointment</Badge>
                <Badge variant="secondary">schedule</Badge>
              </div>
            </div>
            
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Date Patterns</h4>
              <div className="space-y-1 text-sm text-gray-700">
                <p>• Tomorrow at 3pm</p>
                <p>• Next Monday</p>
                <p>• December 25th</p>
                <p>• 2025-01-15</p>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Location Hints</h4>
              <div className="space-y-1 text-sm text-gray-700">
                <p>• Zoom link</p>
                <p>• Conference room</p>
                <p>• Office address</p>
                <p>• Google Meet</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-900">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-8 h-8 text-green-600" />
              <div className="text-2xl font-bold text-green-900">Enabled</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900">AI Model</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-blue-900">Groq Llama 3.1</div>
            <p className="text-xs text-blue-700 mt-1">70B parameters</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-900">Threshold</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">{(threshold * 100).toFixed(0)}%</div>
            <p className="text-xs text-purple-700 mt-1">Confidence required</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MeetingDetection;