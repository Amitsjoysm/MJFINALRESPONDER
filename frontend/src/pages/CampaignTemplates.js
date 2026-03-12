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
import { FileText, Plus, Trash2, Edit, Search, Eye, Copy } from 'lucide-react';

const CampaignTemplates = () => {
  const [templates, setTemplates] = useState([]);
  const [filteredTemplates, setFilteredTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    body: '',
    description: ''
  });

  const availableTags = [
    { tag: '{{first_name}}', desc: 'Contact\'s first name' },
    { tag: '{{last_name}}', desc: 'Contact\'s last name' },
    { tag: '{{email}}', desc: 'Contact\'s email' },
    { tag: '{{title}}', desc: 'Contact\'s job title' },
    { tag: '{{company_name}}', desc: 'Company name' },
    { tag: '{{company_domain}}', desc: 'Company domain' },
    { tag: '{{linkedin_url}}', desc: 'LinkedIn URL' }
  ];

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredTemplates(templates);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredTemplates(
        templates.filter(
          template =>
            template.name.toLowerCase().includes(query) ||
            template.subject.toLowerCase().includes(query) ||
            (template.description && template.description.toLowerCase().includes(query))
        )
      );
    }
  }, [searchQuery, templates]);

  const loadTemplates = async () => {
    try {
      const data = await API.getCampaignTemplates();
      setTemplates(data);
      setFilteredTemplates(data);
    } catch (error) {
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const templateData = {
      name: formData.name,
      subject: formData.subject,
      body: formData.body,
      description: formData.description || null
    };

    try {
      if (editMode) {
        await API.updateCampaignTemplate(currentTemplate.id, templateData);
        toast.success('Template updated successfully');
      } else {
        await API.createCampaignTemplate(templateData);
        toast.success('Template created successfully');
      }
      setDialogOpen(false);
      resetForm();
      loadTemplates();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save template');
    }
  };

  const handleEdit = (template) => {
    setEditMode(true);
    setCurrentTemplate(template);
    setFormData({
      name: template.name,
      subject: template.subject,
      body: template.body,
      description: template.description || ''
    });
    setDialogOpen(true);
  };

  const handleDelete = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    
    try {
      await API.deleteCampaignTemplate(templateId);
      toast.success('Template deleted successfully');
      loadTemplates();
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const handlePreview = (template) => {
    setPreviewTemplate(template);
    setPreviewDialogOpen(true);
  };

  const insertTag = (tag) => {
    const textarea = document.querySelector('textarea[name="body"]');
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = formData.body;
      const before = text.substring(0, start);
      const after = text.substring(end, text.length);
      setFormData({ ...formData, body: before + tag + after });
      
      // Set cursor position after inserted tag
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + tag.length;
        textarea.focus();
      }, 0);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const resetForm = () => {
    setFormData({
      name: '',
      subject: '',
      body: '',
      description: ''
    });
    setEditMode(false);
    setCurrentTemplate(null);
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
        <div className="text-gray-500">Loading templates...</div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <FileText className="w-8 h-8 text-purple-600" />
            Campaign Templates
          </h1>
          <p className="text-gray-500 mt-1">Create personalized email templates with dynamic tags</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600">
              <Plus className="w-4 h-4" />
              Create Template
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editMode ? 'Edit Template' : 'Create New Template'}</DialogTitle>
              <DialogDescription>
                {editMode ? 'Update template content and personalization tags' : 'Create a new email template with personalization tags'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2 space-y-4">
                  <div>
                    <Label>Template Name *</Label>
                    <Input
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="My Campaign Template"
                    />
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Input
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Brief description of this template"
                    />
                  </div>
                  <div>
                    <Label>Subject Line *</Label>
                    <Input
                      required
                      value={formData.subject}
                      onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                      placeholder="Hi {{first_name}}, let's connect!"
                    />
                  </div>
                  <div>
                    <Label>Email Body *</Label>
                    <Textarea
                      name="body"
                      required
                      value={formData.body}
                      onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                      placeholder="Hi {{first_name}},\n\nI noticed you work at {{company_name}}...\n\nBest regards"
                      rows={12}
                      className="font-mono text-sm"
                    />
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-semibold">Available Tags</Label>
                    <p className="text-xs text-gray-500 mt-1 mb-3">Click to insert into template</p>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {availableTags.map((item, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => insertTag(item.tag)}
                          className="w-full text-left p-3 border rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                        >
                          <div className="font-mono text-sm text-purple-600 font-semibold">{item.tag}</div>
                          <div className="text-xs text-gray-500 mt-1">{item.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => handleDialogClose(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editMode ? 'Update Template' : 'Create Template'}
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
              placeholder="Search templates by name, subject, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Total Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">{templates.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Filtered Results</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gray-900">{filteredTemplates.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Templates List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredTemplates.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchQuery ? 'No templates match your search' : 'No templates yet. Create your first template to get started.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredTemplates.map((template) => (
            <Card key={template.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">{template.name}</h3>
                      <Badge variant="outline" className="text-xs">
                        {template.body.match(/{{\w+}}/g)?.length || 0} tags
                      </Badge>
                    </div>
                    {template.description && (
                      <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                    )}
                    <div className="space-y-2">
                      <div>
                        <span className="text-xs font-semibold text-gray-500">SUBJECT:</span>
                        <p className="text-sm text-gray-900 mt-1 font-medium">{template.subject}</p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500">PREVIEW:</span>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {template.body.substring(0, 150)}{template.body.length > 150 ? '...' : ''}
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-3">
                      Created: {new Date(template.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handlePreview(template)}
                      className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(template)}
                      className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(template.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Preview Dialog */}
      <Dialog open={previewDialogOpen} onOpenChange={setPreviewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Template Preview: {previewTemplate?.name}</DialogTitle>
            <DialogDescription>
              This is how your template looks with personalization tags
            </DialogDescription>
          </DialogHeader>
          {previewTemplate && (
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-semibold">Subject</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(previewTemplate.subject)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
                <div className="p-3 bg-gray-50 rounded border">
                  <p className="text-sm font-medium">{previewTemplate.subject}</p>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-semibold">Body</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(previewTemplate.body)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
                <div className="p-4 bg-gray-50 rounded border whitespace-pre-wrap">
                  <p className="text-sm">{previewTemplate.body}</p>
                </div>
              </div>
              {previewTemplate.body.match(/{{\w+}}/g) && (
                <div>
                  <Label className="text-sm font-semibold">Personalization Tags Used</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {[...new Set(previewTemplate.body.match(/{{\w+}}/g))].map((tag, idx) => (
                      <Badge key={idx} variant="secondary">{tag}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CampaignTemplates;
