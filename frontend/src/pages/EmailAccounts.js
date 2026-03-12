import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';
import { toast } from 'sonner';
import { Mail, Plus, Trash2, Edit, CheckCircle2, XCircle, Globe } from 'lucide-react';

// Google Icon Component
const GoogleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

// Outlook Icon Component
const OutlookIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path fill="#0078D4" d="M24 7.6V4.8c0-.663-.537-1.2-1.2-1.2h-9.6V1.2c0-.663-.537-1.2-1.2-1.2H1.2C.537 0 0 .537 0 1.2v21.6c0 .663.537 1.2 1.2 1.2h10.8c.663 0 1.2-.537 1.2-1.2v-2.4h9.6c.663 0 1.2-.537 1.2-1.2V7.6zM6 6c2.21 0 4 2.015 4 4.5S8.21 15 6 15s-4-2.015-4-4.5S3.79 6 6 6zm8.4 12H1.2V1.2h10.8v20.4zm8.4-1.2h-7.2V8.4h7.2v8.4z"/>
  </svg>
);

const EmailAccounts = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  
  const [formData, setFormData] = useState({
    account_type: 'custom_smtp',
    email: '',
    password: '',
    smtp_host: '',
    smtp_port: '587',
    imap_host: '',
    imap_port: '993',
    persona: '',
    signature: ''
  });

  useEffect(() => {
    loadAccounts();
    
    // Check for OAuth success/error
    const success = searchParams.get('success');
    const error = searchParams.get('error');
    const email = searchParams.get('email');
    
    if (success === 'true' && email) {
      toast.success(`Successfully connected ${email}!`);
      // Clear URL params
      setSearchParams({});
    } else if (error) {
      toast.error(`OAuth failed: ${error}`);
      setSearchParams({});
    }
  }, []);

  const loadAccounts = async () => {
    try {
      const data = await API.getEmailAccounts();
      setAccounts(data);
    } catch (error) {
      toast.error('Failed to load email accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthConnect = async (provider) => {
    try {
      if (provider === 'gmail') {
        const data = await API.getGoogleOAuthUrl('email');
        window.location.href = data.url;
      } else if (provider === 'outlook') {
        const data = await API.getMicrosoftOAuthUrl('email');
        window.location.href = data.url;
      }
    } catch (error) {
      console.error('OAuth error:', error);
      toast.error('Failed to initiate OAuth flow');
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    try {
      await API.createEmailAccount(formData);
      toast.success('Email account added successfully');
      setDialogOpen(false);
      resetForm();
      loadAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add email account');
    }
  };

  const handleUpdateAccount = async (e) => {
    e.preventDefault();
    try {
      await API.updateEmailAccount(editingAccount.id, {
        persona: editingAccount.persona,
        signature: editingAccount.signature,
        auto_reply_enabled: editingAccount.auto_reply_enabled,
        is_active: editingAccount.is_active
      });
      toast.success('Account updated successfully');
      setEditDialogOpen(false);
      setEditingAccount(null);
      loadAccounts();
    } catch (error) {
      toast.error('Failed to update account');
    }
  };

  const handleDeleteAccount = async (accountId) => {
    if (!window.confirm('Are you sure you want to delete this account?')) return;
    
    try {
      await API.deleteEmailAccount(accountId);
      toast.success('Account deleted successfully');
      loadAccounts();
    } catch (error) {
      toast.error('Failed to delete account');
    }
  };

  const handleToggleActive = async (account) => {
    try {
      await API.updateEmailAccount(account.id, {
        is_active: !account.is_active
      });
      toast.success(`Account ${!account.is_active ? 'activated' : 'deactivated'}`);
      loadAccounts();
    } catch (error) {
      toast.error('Failed to update account status');
    }
  };

  const resetForm = () => {
    setFormData({
      account_type: 'custom_smtp',
      email: '',
      password: '',
      smtp_host: '',
      smtp_port: '587',
      imap_host: '',
      imap_port: '993',
      persona: '',
      signature: ''
    });
  };

  const openEditDialog = (account) => {
    setEditingAccount({...account});
    setEditDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading accounts...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Email Accounts</h1>
          <p className="text-gray-600 mt-1">Connect and manage your email accounts</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Account
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add Email Account</DialogTitle>
              <DialogDescription>Connect via OAuth or manual SMTP/IMAP configuration</DialogDescription>
            </DialogHeader>
            
            {/* OAuth Options */}
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Quick Connect (OAuth)</Label>
                <div className="flex gap-4 mt-3 justify-center">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          onClick={() => handleOAuthConnect('gmail')}
                          className="w-20 h-20 rounded-lg bg-white border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
                        >
                          <GoogleIcon className="w-12 h-12" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Connect with Google</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          onClick={() => handleOAuthConnect('outlook')}
                          className="w-20 h-20 rounded-lg bg-white border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
                        >
                          <OutlookIcon className="w-12 h-12" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Connect with Outlook</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-gray-500">Or manual configuration</span>
                </div>
              </div>

              {/* Manual SMTP Form */}
              <form onSubmit={handleManualSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label htmlFor="email">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      placeholder="your@email.com"
                      required
                    />
                  </div>
                  
                  <div className="col-span-2">
                    <Label htmlFor="password">Password/App Password *</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      placeholder="••••••••"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="smtp_host">SMTP Host *</Label>
                    <Input
                      id="smtp_host"
                      value={formData.smtp_host}
                      onChange={(e) => setFormData({...formData, smtp_host: e.target.value})}
                      placeholder="smtp.gmail.com"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="smtp_port">SMTP Port *</Label>
                    <Input
                      id="smtp_port"
                      value={formData.smtp_port}
                      onChange={(e) => setFormData({...formData, smtp_port: e.target.value})}
                      placeholder="587"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="imap_host">IMAP Host *</Label>
                    <Input
                      id="imap_host"
                      value={formData.imap_host}
                      onChange={(e) => setFormData({...formData, imap_host: e.target.value})}
                      placeholder="imap.gmail.com"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="imap_port">IMAP Port *</Label>
                    <Input
                      id="imap_port"
                      value={formData.imap_port}
                      onChange={(e) => setFormData({...formData, imap_port: e.target.value})}
                      placeholder="993"
                      required
                    />
                  </div>

                  <div className="col-span-2">
                    <Label htmlFor="persona">Persona (Optional)</Label>
                    <Textarea
                      id="persona"
                      value={formData.persona}
                      onChange={(e) => setFormData({...formData, persona: e.target.value})}
                      placeholder="e.g., Professional, friendly tone. Customer support representative..."
                      rows={3}
                    />
                  </div>

                  <div className="col-span-2">
                    <Label htmlFor="signature">Email Signature (Optional)</Label>
                    <Textarea
                      id="signature"
                      value={formData.signature}
                      onChange={(e) => setFormData({...formData, signature: e.target.value})}
                      placeholder="Best regards,&#10;John Doe&#10;Support Team"
                      rows={3}
                    />
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button type="submit" className="flex-1">Add Account</Button>
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Accounts List */}
      {accounts.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Mail className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Email Accounts</h3>
            <p className="text-gray-600 text-center mb-4">
              Get started by connecting your first email account
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Your First Account
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {accounts.map((account) => (
            <Card key={account.id} className={account.is_active ? 'border-green-200 bg-green-50/30' : 'border-gray-200'}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                      account.account_type === 'oauth_gmail' ? 'bg-gray-50' :
                      account.account_type === 'oauth_outlook' ? 'bg-gray-50' :
                      'bg-purple-100'
                    }`}>
                      {account.account_type === 'oauth_gmail' ? (
                        <GoogleIcon className="w-7 h-7" />
                      ) : account.account_type === 'oauth_outlook' ? (
                        <OutlookIcon className="w-7 h-7" />
                      ) : (
                        <Globe className="w-6 h-6 text-purple-600" />
                      )}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{account.email}</CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        <Badge variant={account.account_type.includes('oauth') ? 'default' : 'secondary'}>
                          {account.account_type === 'oauth_gmail' ? 'Gmail OAuth' :
                           account.account_type === 'oauth_outlook' ? 'Outlook OAuth' :
                           'Manual SMTP'}
                        </Badge>
                        {account.is_active ? (
                          <Badge className="bg-green-500">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            <XCircle className="w-3 h-3 mr-1" />
                            Inactive
                          </Badge>
                        )}
                      </CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {account.persona && (
                    <div className="text-sm">
                      <span className="font-medium text-gray-700">Persona:</span>
                      <p className="text-gray-600 mt-1 line-clamp-2">{account.persona}</p>
                    </div>
                  )}
                  
                  {account.signature && (
                    <div className="text-sm">
                      <span className="font-medium text-gray-700">Signature:</span>
                      <p className="text-gray-600 mt-1 whitespace-pre-wrap line-clamp-2">{account.signature}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t">
                    <div className="text-xs text-gray-500">
                      Auto-reply: {account.auto_reply_enabled ? 'Enabled' : 'Disabled'}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openEditDialog(account)}
                      className="flex-1"
                    >
                      <Edit className="w-4 h-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant={account.is_active ? 'outline' : 'default'}
                      onClick={() => handleToggleActive(account)}
                      className="flex-1"
                    >
                      {account.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteAccount(account.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Account Settings</DialogTitle>
            <DialogDescription>Update persona, signature, and auto-send settings</DialogDescription>
          </DialogHeader>
          
          {editingAccount && (
            <form onSubmit={handleUpdateAccount} className="space-y-4">
              <div>
                <Label htmlFor="edit_persona">Persona</Label>
                <Textarea
                  id="edit_persona"
                  value={editingAccount.persona || ''}
                  onChange={(e) => setEditingAccount({...editingAccount, persona: e.target.value})}
                  placeholder="Define the tone and style for AI responses..."
                  rows={4}
                />
              </div>

              <div>
                <Label htmlFor="edit_signature">Email Signature</Label>
                <Textarea
                  id="edit_signature"
                  value={editingAccount.signature || ''}
                  onChange={(e) => setEditingAccount({...editingAccount, signature: e.target.value})}
                  placeholder="Your email signature..."
                  rows={4}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_auto_reply"
                  checked={editingAccount.auto_reply_enabled || false}
                  onChange={(e) => setEditingAccount({...editingAccount, auto_reply_enabled: e.target.checked})}
                  className="w-4 h-4"
                />
                <Label htmlFor="edit_auto_reply" className="cursor-pointer">
                  Enable auto-reply for validated drafts
                </Label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={editingAccount.is_active || false}
                  onChange={(e) => setEditingAccount({...editingAccount, is_active: e.target.checked})}
                  className="w-4 h-4"
                />
                <Label htmlFor="edit_is_active" className="cursor-pointer">
                  Account is active
                </Label>
              </div>

              <div className="flex gap-3">
                <Button type="submit" className="flex-1">Save Changes</Button>
                <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EmailAccounts;
