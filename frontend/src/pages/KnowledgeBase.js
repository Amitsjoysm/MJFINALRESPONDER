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
import { Database, Plus, Trash2, Edit, CheckCircle2, XCircle, Search, FileText } from 'lucide-react';

const KnowledgeBase = () => {
  const [entries, setEntries] = useState([]);
  const [filteredEntries, setFilteredEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentEntry, setCurrentEntry] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    tags: '',
    is_active: true
  });

  useEffect(() => {
    loadEntries();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredEntries(entries);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredEntries(
        entries.filter(
          entry =>
            entry.title.toLowerCase().includes(query) ||
            entry.content.toLowerCase().includes(query) ||
            entry.tags.some(tag => tag.toLowerCase().includes(query))
        )
      );
    }
  }, [searchQuery, entries]);

  const loadEntries = async () => {
    try {
      const data = await API.getKnowledgeBase();
      setEntries(data);
      setFilteredEntries(data);
    } catch (error) {
      toast.error('Failed to load knowledge base');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const tagsArray = formData.tags
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0);

    const entryData = {
      title: formData.title,
      content: formData.content,
      tags: tagsArray,
      is_active: formData.is_active
    };

    try {
      if (editMode) {
        await API.updateKnowledgeBase(currentEntry.id, entryData);
        toast.success('Knowledge base entry updated');
      } else {
        await API.createKnowledgeBase(entryData);
        toast.success('Knowledge base entry created');
      }
      setDialogOpen(false);
      resetForm();
      loadEntries();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save entry');
    }
  };

  const handleEdit = (entry) => {
    setEditMode(true);
    setCurrentEntry(entry);
    setFormData({
      title: entry.title,
      content: entry.content,
      tags: entry.tags.join(', '),
      is_active: entry.is_active
    });
    setDialogOpen(true);
  };

  const handleDelete = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this knowledge base entry?')) return;
    
    try {
      await API.deleteKnowledgeBase(entryId);
      toast.success('Entry deleted successfully');
      loadEntries();
    } catch (error) {
      toast.error('Failed to delete entry');
    }
  };

  const handleToggleActive = async (entry) => {
    try {
      await API.updateKnowledgeBase(entry.id, {
        is_active: !entry.is_active
      });
      toast.success(`Entry ${!entry.is_active ? 'activated' : 'deactivated'}`);
      loadEntries();
    } catch (error) {
      toast.error('Failed to update entry');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      tags: '',
      is_active: true
    });
    setEditMode(false);
    setCurrentEntry(null);
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
        <div className="text-gray-500">Loading knowledge base...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-600 mt-1">Build your knowledge base for AI-powered responses</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Entry
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editMode ? 'Edit Entry' : 'Add Knowledge Base Entry'}</DialogTitle>
              <DialogDescription>
                Add information that the AI can use to generate contextual responses
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  placeholder="e.g., Product Pricing Information"
                  required
                />
              </div>

              <div>
                <Label htmlFor="content">Content *</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  placeholder="Enter detailed information that the AI should know about this topic..."
                  rows={12}
                  required
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  This content will be used to generate contextual responses
                </p>
              </div>

              <div>
                <Label htmlFor="tags">Tags (comma-separated)</Label>
                <Input
                  id="tags"
                  value={formData.tags}
                  onChange={(e) => setFormData({...formData, tags: e.target.value})}
                  placeholder="pricing, features, support, billing"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Tags help the AI find relevant information
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="w-4 h-4"
                />
                <Label htmlFor="is_active" className="cursor-pointer">
                  Entry is active
                </Label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">
                  {editMode ? 'Update Entry' : 'Add Entry'}
                </Button>
                <Button type="button" variant="outline" onClick={() => handleDialogClose(false)}>
                  Cancel
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
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              placeholder="Search knowledge base..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900">Total Entries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900">{entries.length}</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-900">Active Entries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-900">
              {entries.filter(e => e.is_active).length}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-900">Total Tags</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-900">
              {new Set(entries.flatMap(e => e.tags)).size}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Entries List */}
      {filteredEntries.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {searchQuery ? 'No Results Found' : 'No Knowledge Base Entries'}
            </h3>
            <p className="text-gray-600 text-center mb-4">
              {searchQuery 
                ? 'Try adjusting your search query'
                : 'Add your first knowledge base entry to enhance AI responses'
              }
            </p>
            {!searchQuery && (
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Entry
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredEntries.map((entry) => (
            <Card 
              key={entry.id} 
              className={`transition-all ${entry.is_active ? 'border-purple-200 bg-purple-50/30' : 'border-gray-200 opacity-60'}`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-purple-600" />
                      <CardTitle className="text-lg">{entry.title}</CardTitle>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge 
                        variant={entry.is_active ? 'default' : 'secondary'}
                        className={entry.is_active ? 'bg-purple-600' : ''}
                      >
                        {entry.is_active ? (
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
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-700 line-clamp-4 whitespace-pre-wrap">
                    {entry.content}
                  </p>
                </div>

                {entry.tags.length > 0 && (
                  <div>
                    <Label className="text-xs font-medium text-gray-500 uppercase">Tags</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {entry.tags.map((tag, idx) => (
                        <Badge key={idx} variant="secondary" className="bg-gray-100 text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-2 border-t">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(entry)}
                    className="flex-1"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant={entry.is_active ? 'outline' : 'default'}
                    onClick={() => handleToggleActive(entry)}
                    className="flex-1"
                  >
                    {entry.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(entry.id)}
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

export default KnowledgeBase;
