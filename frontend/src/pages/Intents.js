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
import { Target, Plus, Trash2, Edit, CheckCircle2, XCircle, ArrowUp, ArrowDown } from 'lucide-react';

const Intents = () => {
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentIntent, setCurrentIntent] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    keywords: '',
    prompt: '',
    priority: 1,
    auto_send: false,
    is_inbound_lead: false,
    enable_lead_qualification: false,
    enable_lead_nurturing: false,
    is_active: true
  });

  useEffect(() => {
    loadIntents();
  }, []);

  const loadIntents = async () => {
    try {
      const data = await API.getIntents();
      setIntents(data.sort((a, b) => b.priority - a.priority));
    } catch (error) {
      toast.error('Failed to load intents');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const keywordsArray = formData.keywords
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0);

    if (keywordsArray.length === 0) {
      toast.error('Please provide at least one keyword');
      return;
    }

    const intentData = {
      name: formData.name,
      description: formData.description,
      keywords: keywordsArray,
      prompt: formData.prompt,
      priority: parseInt(formData.priority),
      auto_send: formData.auto_send,
      is_inbound_lead: formData.is_inbound_lead,
      enable_lead_qualification: formData.enable_lead_qualification,
      enable_lead_nurturing: formData.enable_lead_nurturing,
      is_active: formData.is_active
    };

    try {
      if (editMode) {
        await API.updateIntent(currentIntent.id, intentData);
        toast.success('Intent updated successfully');
      } else {
        await API.createIntent(intentData);
        toast.success('Intent created successfully');
      }
      setDialogOpen(false);
      resetForm();
      loadIntents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save intent');
    }
  };

  const handleEdit = (intent) => {
    setEditMode(true);
    setCurrentIntent(intent);
    setFormData({
      name: intent.name,
      description: intent.description || '',
      keywords: intent.keywords.join(', '),
      prompt: intent.prompt,
      priority: intent.priority,
      auto_send: intent.auto_send || false,
      is_inbound_lead: intent.is_inbound_lead || false,
      enable_lead_qualification: intent.enable_lead_qualification || false,
      enable_lead_nurturing: intent.enable_lead_nurturing || false,
      is_active: intent.is_active
    });
    setDialogOpen(true);
  };

  const handleDelete = async (intentId) => {
    if (!window.confirm('Are you sure you want to delete this intent?')) return;
    
    try {
      await API.deleteIntent(intentId);
      toast.success('Intent deleted successfully');
      loadIntents();
    } catch (error) {
      toast.error('Failed to delete intent');
    }
  };

  const handleToggleActive = async (intent) => {
    try {
      await API.updateIntent(intent.id, {
        is_active: !intent.is_active
      });
      toast.success(`Intent ${!intent.is_active ? 'activated' : 'deactivated'}`);
      loadIntents();
    } catch (error) {
      toast.error('Failed to update intent');
    }
  };

  const handlePriorityChange = async (intent, direction) => {
    const newPriority = direction === 'up' ? intent.priority + 1 : intent.priority - 1;
    try {
      await API.updateIntent(intent.id, { priority: newPriority });
      toast.success('Priority updated');
      loadIntents();
    } catch (error) {
      toast.error('Failed to update priority');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      keywords: '',
      prompt: '',
      priority: 1,
      auto_send: false,
      is_inbound_lead: false,
      enable_lead_qualification: false,
      enable_lead_nurturing: false,
      is_active: true
    });
    setEditMode(false);
    setCurrentIntent(null);
  };

  const handleDialogClose = (open) => {
    if (!open) {
      resetForm();
    }
    setDialogOpen(open);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading intents...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Email Intents</h1>
          <p className="text-gray-600 mt-1">Define intents for AI-powered email classification and responses</p>
        </div>
        <Button 
          onClick={() => setDialogOpen(true)}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Intent
        </Button>
      </div>

      {/* Info Banner for Lead Management */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Target className="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-indigo-900 mb-1">
                Lead Qualification & Nurturing Controls
              </p>
              <p className="text-xs text-indigo-700">
                When creating or editing an intent, mark it as <strong>"Inbound Lead"</strong> to reveal Lead Qualification and Lead Nurturing options. 
                These features help you automatically qualify leads and gather information through contextual questions. 
                <span className="text-indigo-800 font-medium"> Note:</span> Global settings must also be enabled in <strong>Lead Controls</strong> page.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editMode ? 'Edit Intent' : 'Create New Intent'}</DialogTitle>
              <DialogDescription>
                Define how the AI should recognize and respond to specific types of emails
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="name">Intent Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Customer Support Request"
                  required
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Brief description of this intent"
                />
              </div>

              <div>
                <Label htmlFor="keywords">Keywords (comma-separated) *</Label>
                <Input
                  id="keywords"
                  value={formData.keywords}
                  onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                  placeholder="support, help, issue, problem, bug"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter keywords that help identify this intent
                </p>
              </div>

              <div>
                <Label htmlFor="prompt">Response Guidelines/Prompt *</Label>
                <Textarea
                  id="prompt"
                  value={formData.prompt}
                  onChange={(e) => setFormData({...formData, prompt: e.target.value})}
                  placeholder="Provide detailed instructions for the AI on how to respond to this type of email..."
                  rows={6}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Define how the AI should craft responses for this intent
                </p>
              </div>

              <div>
                <Label htmlFor="priority">Priority (1-10)</Label>
                <Input
                  id="priority"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.priority}
                  onChange={(e) => setFormData({...formData, priority: e.target.value})}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Higher priority intents are matched first
                </p>
              </div>

              <div className="space-y-3 pt-6">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="auto_send"
                    checked={formData.auto_send}
                    onChange={(e) => setFormData({...formData, auto_send: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="auto_send" className="cursor-pointer">
                    Auto-send replies for this intent
                  </Label>
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_inbound_lead"
                    checked={formData.is_inbound_lead}
                    onChange={(e) => setFormData({...formData, is_inbound_lead: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="is_inbound_lead" className="cursor-pointer">
                    Mark as Inbound Lead intent
                  </Label>
                </div>
                <p className="text-xs text-gray-500 ml-6">
                  Emails matching this intent will be tracked as inbound leads with detailed information extraction
                </p>
                
                {formData.is_inbound_lead && (
                  <div className="ml-6 space-y-3 pt-2 pl-4 border-l-2 border-purple-200">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="enable_lead_qualification"
                        checked={formData.enable_lead_qualification}
                        onChange={(e) => setFormData({...formData, enable_lead_qualification: e.target.checked})}
                        className="w-4 h-4"
                      />
                      <Label htmlFor="enable_lead_qualification" className="cursor-pointer text-sm">
                        Enable Lead Qualification
                      </Label>
                    </div>
                    <p className="text-xs text-gray-500 ml-6">
                      Automatically qualify leads by asking questions and scoring their responses (0-100)
                    </p>
                    
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="enable_lead_nurturing"
                        checked={formData.enable_lead_nurturing}
                        onChange={(e) => setFormData({...formData, enable_lead_nurturing: e.target.checked})}
                        className="w-4 h-4"
                      />
                      <Label htmlFor="enable_lead_nurturing" className="cursor-pointer text-sm">
                        Enable Lead Nurturing
                      </Label>
                    </div>
                    <p className="text-xs text-gray-500 ml-6">
                      Ask 1-2 contextual questions per email to gather more information about the lead
                    </p>
                  </div>
                )}
                
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="is_active" className="cursor-pointer">
                    Intent is active
                  </Label>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">
                  {editMode ? 'Update Intent' : 'Create Intent'}
                </Button>
                <Button type="button" variant="outline" onClick={() => handleDialogClose(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

      {/* Intents List */}
      {intents.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Intents Configured</h3>
            <p className="text-gray-600 text-center mb-4">
              Create your first intent to enable AI-powered email classification
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Intent
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {intents.map((intent, index) => (
            <Card 
              key={intent.id} 
              className={`transition-all ${intent.is_active ? 'border-purple-200 bg-purple-50/30' : 'border-gray-200 opacity-60'}`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <CardTitle className="text-xl">{intent.name}</CardTitle>
                      <Badge 
                        variant={intent.is_active ? 'default' : 'secondary'}
                        className={intent.is_active ? 'bg-purple-600' : ''}
                      >
                        {intent.is_active ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Active
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3 h-3 mr-1" />
                            Inactive
                          </>
                        )}
                      </Badge>
                      <Badge variant="outline">
                        Priority: {intent.priority}
                      </Badge>
                      {intent.auto_send && (
                        <Badge className="bg-green-500">
                          Auto-Send
                        </Badge>
                      )}
                      {intent.is_inbound_lead && (
                        <Badge className="bg-blue-500">
                          Lead
                        </Badge>
                      )}
                      {intent.enable_lead_qualification && (
                        <Badge className="bg-indigo-500">
                          Qualification
                        </Badge>
                      )}
                      {intent.enable_lead_nurturing && (
                        <Badge className="bg-pink-500">
                          Nurturing
                        </Badge>
                      )}
                    </div>
                    {intent.description && (
                      <CardDescription className="mt-2">{intent.description}</CardDescription>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handlePriorityChange(intent, 'up')}
                      disabled={index === 0}
                    >
                      <ArrowUp className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handlePriorityChange(intent, 'down')}
                      disabled={index === intents.length - 1}
                    >
                      <ArrowDown className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium text-gray-700">Keywords</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {intent.keywords.map((keyword, idx) => (
                      <Badge key={idx} variant="secondary" className="bg-gray-100">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium text-gray-700">Response Guidelines</Label>
                  <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-3">
                      {intent.prompt}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(intent)}
                    className="flex-1"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant={intent.is_active ? 'outline' : 'default'}
                    onClick={() => handleToggleActive(intent)}
                    className="flex-1"
                  >
                    {intent.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(intent.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Intents;
