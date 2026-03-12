import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Users, Plus, Trash2, Edit, Upload, Download, Search, Mail, Building2, User, Linkedin } from 'lucide-react';

const CampaignContacts = () => {
  const [contacts, setContacts] = useState([]);
  const [filteredContacts, setFilteredContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentContact, setCurrentContact] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    title: '',
    company_name: '',
    linkedin_url: '',
    company_domain: '',
    custom_fields: {},
    tags: ''
  });

  useEffect(() => {
    loadContacts();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredContacts(contacts);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredContacts(
        contacts.filter(
          contact =>
            contact.email.toLowerCase().includes(query) ||
            (contact.first_name && contact.first_name.toLowerCase().includes(query)) ||
            (contact.last_name && contact.last_name.toLowerCase().includes(query)) ||
            (contact.company_name && contact.company_name.toLowerCase().includes(query)) ||
            contact.tags.some(tag => tag.toLowerCase().includes(query))
        )
      );
    }
  }, [searchQuery, contacts]);

  const loadContacts = async () => {
    try {
      const data = await API.getCampaignContacts();
      setContacts(data);
      setFilteredContacts(data);
    } catch (error) {
      toast.error('Failed to load contacts');
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

    const contactData = {
      email: formData.email,
      first_name: formData.first_name || null,
      last_name: formData.last_name || null,
      title: formData.title || null,
      company_name: formData.company_name || null,
      linkedin_url: formData.linkedin_url || null,
      company_domain: formData.company_domain || null,
      custom_fields: formData.custom_fields,
      tags: tagsArray
    };

    try {
      if (editMode) {
        await API.updateCampaignContact(currentContact.id, contactData);
        toast.success('Contact updated successfully');
      } else {
        await API.createCampaignContact(contactData);
        toast.success('Contact created successfully');
      }
      setDialogOpen(false);
      resetForm();
      loadContacts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save contact');
    }
  };

  const handleEdit = (contact) => {
    setEditMode(true);
    setCurrentContact(contact);
    setFormData({
      email: contact.email,
      first_name: contact.first_name || '',
      last_name: contact.last_name || '',
      title: contact.title || '',
      company_name: contact.company_name || '',
      linkedin_url: contact.linkedin_url || '',
      company_domain: contact.company_domain || '',
      custom_fields: contact.custom_fields || {},
      tags: contact.tags.join(', ')
    });
    setDialogOpen(true);
  };

  const handleDelete = async (contactId) => {
    if (!window.confirm('Are you sure you want to delete this contact?')) return;
    
    try {
      await API.deleteCampaignContact(contactId);
      toast.success('Contact deleted successfully');
      loadContacts();
    } catch (error) {
      toast.error('Failed to delete contact');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'text/csv') {
      setCsvFile(file);
    } else {
      toast.error('Please select a valid CSV file');
      e.target.value = null;
    }
  };

  const handleBulkUpload = async () => {
    if (!csvFile) {
      toast.error('Please select a CSV file');
      return;
    }

    setUploading(true);
    try {
      const result = await API.bulkUploadCampaignContacts(csvFile);
      toast.success(`Successfully imported ${result.success_count} contacts`);
      if (result.error_count > 0) {
        toast.warning(`${result.error_count} contacts failed to import`);
      }
      setUploadDialogOpen(false);
      setCsvFile(null);
      loadContacts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload contacts');
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      await API.downloadCampaignContactTemplate();
      toast.success('Template downloaded successfully');
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      first_name: '',
      last_name: '',
      title: '',
      company_name: '',
      linkedin_url: '',
      company_domain: '',
      custom_fields: {},
      tags: ''
    });
    setEditMode(false);
    setCurrentContact(null);
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
        <div className="text-gray-500">Loading contacts...</div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="w-8 h-8 text-purple-600" />
            Campaign Contacts
          </h1>
          <p className="text-gray-500 mt-1">Manage your campaign contact list</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={handleDownloadTemplate}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download Template
          </Button>
          <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <Upload className="w-4 h-4" />
                Bulk Upload
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Bulk Upload Contacts</DialogTitle>
                <DialogDescription>
                  Upload a CSV file to import multiple contacts at once
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>CSV File</Label>
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="mt-2"
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    File should include columns: email, first_name, last_name, title, company_name, linkedin_url, company_domain
                  </p>
                </div>
                <Button
                  onClick={handleBulkUpload}
                  disabled={!csvFile || uploading}
                  className="w-full"
                >
                  {uploading ? 'Uploading...' : 'Upload Contacts'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600">
                <Plus className="w-4 h-4" />
                Add Contact
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editMode ? 'Edit Contact' : 'Add New Contact'}</DialogTitle>
                <DialogDescription>
                  {editMode ? 'Update contact information' : 'Add a new contact to your campaign list'}
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="contact@example.com"
                    />
                  </div>
                  <div>
                    <Label>First Name</Label>
                    <Input
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <Label>Last Name</Label>
                    <Input
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      placeholder="Doe"
                    />
                  </div>
                  <div>
                    <Label>Title</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="CEO"
                    />
                  </div>
                  <div>
                    <Label>Company Name</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                      placeholder="Acme Inc"
                    />
                  </div>
                  <div>
                    <Label>Company Domain</Label>
                    <Input
                      value={formData.company_domain}
                      onChange={(e) => setFormData({ ...formData, company_domain: e.target.value })}
                      placeholder="acme.com"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>LinkedIn URL</Label>
                    <Input
                      value={formData.linkedin_url}
                      onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                      placeholder="https://linkedin.com/in/johndoe"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Tags (comma-separated)</Label>
                    <Input
                      value={formData.tags}
                      onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                      placeholder="lead, enterprise, tech"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => handleDialogClose(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">
                    {editMode ? 'Update Contact' : 'Create Contact'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search by email, name, company, or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Total Contacts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">{contacts.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Filtered Results</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gray-900">{filteredContacts.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Engagement Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">
              {contacts.length > 0 ? Math.round((contacts.filter(c => c.last_engagement).length / contacts.length) * 100) : 0}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Contacts List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredContacts.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchQuery ? 'No contacts match your search' : 'No contacts yet. Add your first contact or upload a CSV file.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredContacts.map((contact) => (
            <Card key={contact.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                        {contact.first_name ? contact.first_name[0].toUpperCase() : contact.email[0].toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-lg">
                            {contact.first_name || contact.last_name
                              ? `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
                              : 'No Name'}
                          </h3>
                          {contact.title && (
                            <Badge variant="outline" className="text-xs">{contact.title}</Badge>
                          )}
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4" />
                            <span>{contact.email}</span>
                          </div>
                          {contact.company_name && (
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4" />
                              <span>{contact.company_name}</span>
                              {contact.company_domain && (
                                <span className="text-gray-400">({contact.company_domain})</span>
                              )}
                            </div>
                          )}
                          {contact.linkedin_url && (
                            <div className="flex items-center gap-2">
                              <Linkedin className="w-4 h-4" />
                              <a
                                href={contact.linkedin_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                LinkedIn Profile
                              </a>
                            </div>
                          )}
                        </div>
                        {contact.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-3">
                            {contact.tags.map((tag, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {contact.last_engagement && (
                          <p className="text-xs text-gray-500 mt-2">
                            Last engaged: {new Date(contact.last_engagement).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(contact)}
                      className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(contact.id)}
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
    </div>
  );
};

export default CampaignContacts;
