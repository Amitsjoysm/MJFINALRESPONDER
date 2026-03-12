import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Error logging function
const logError = (error, context) => {
  const errorData = {
    message: error.message,
    context,
    status: error.response?.status,
    data: error.response?.data,
    timestamp: new Date().toISOString(),
    url: error.config?.url
  };
  
  console.error('API Error:', errorData);
  
  // In production, send to error tracking service
  // You can also send to backend: 
  // axios.post('/errors/log', errorData).catch(() => {});
  
  return errorData;
};

class API {
  constructor() {
    this.axios = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout
    });

    // Add auth token to requests
    this.axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        logError(error, 'request_interceptor');
        return Promise.reject(error);
      }
    );

    // Enhanced error handling
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        // Log all errors
        logError(error, 'response_interceptor');
        
        // Handle different error types
        if (error.response) {
          // Server responded with error status
          const status = error.response.status;
          const detail = error.response.data?.detail || error.response.data?.message || 'An error occurred';
          
          switch (status) {
            case 401:
              // Clear invalid token
              localStorage.removeItem('token');
              if (!window.location.pathname.includes('/auth') && !window.location.pathname.includes('/login')) {
                toast.error('Session expired. Please login again.');
                window.location.href = '/';
              }
              break;
            
            case 403:
              toast.error('Access denied');
              break;
            
            case 404:
              toast.error('Resource not found');
              break;
            
            case 500:
              toast.error(`Server error: ${detail}`);
              break;
            
            case 503:
              toast.error('Service temporarily unavailable');
              break;
            
            default:
              toast.error(detail);
          }
        } else if (error.request) {
          // Request made but no response received
          toast.error('Network error. Please check your connection.');
        } else {
          // Something else happened
          toast.error('An unexpected error occurred');
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Wrapper method to handle errors gracefully
  async _safeRequest(requestFn, context) {
    try {
      return await requestFn();
    } catch (error) {
      logError(error, context);
      throw error;
    }
  }

  // Auth
  async register(data) {
    return this._safeRequest(async () => {
      const response = await this.axios.post('/auth/register', data);
      return response.data;
    }, 'register');
  }

  async login(data) {
    return this._safeRequest(async () => {
      const response = await this.axios.post('/auth/login', data);
      return response.data;
    }, 'login');
  }

  async getProfile() {
    const response = await this.axios.get('/auth/me');
    return response.data;
  }

  async getQuota() {
    const response = await this.axios.get('/auth/quota');
    return response.data;
  }

  // Email Accounts
  async getEmailAccounts() {
    const response = await this.axios.get('/email-accounts');
    return response.data;
  }

  async createEmailAccount(data) {
    const response = await this.axios.post('/email-accounts', data);
    return response.data;
  }

  async updateEmailAccount(id, data) {
    const response = await this.axios.patch(`/email-accounts/${id}`, data);
    return response.data;
  }

  async deleteEmailAccount(id) {
    const response = await this.axios.delete(`/email-accounts/${id}`);
    return response.data;
  }

  async testEmailAccount(id) {
    const response = await this.axios.post(`/email-accounts/${id}/test`);
    return response.data;
  }

  // Emails
  async getEmails(params) {
    const response = await this.axios.get('/emails', { params });
    return response.data;
  }

  async getEmail(id) {
    const response = await this.axios.get(`/emails/${id}`);
    return response.data;
  }

  async getEmailStats() {
    const response = await this.axios.get('/emails/stats');
    return response.data;
  }

  async sendEmail(data) {
    const response = await this.axios.post('/emails/send', data);
    return response.data;
  }

  async approveDraft(id) {
    const response = await this.axios.post(`/emails/${id}/approve-draft`);
    return response.data;
  }

  async reprocessEmail(id) {
    const response = await this.axios.post(`/emails/${id}/reprocess`);
    return response.data;
  }

  // Intents
  async getIntents() {
    const response = await this.axios.get('/intents');
    return response.data;
  }

  async createIntent(data) {
    const response = await this.axios.post('/intents', data);
    return response.data;
  }

  async updateIntent(id, data) {
    const response = await this.axios.patch(`/intents/${id}`, data);
    return response.data;
  }

  async deleteIntent(id) {
    const response = await this.axios.delete(`/intents/${id}`);
    return response.data;
  }

  // Knowledge Base
  async getKnowledgeBase() {
    const response = await this.axios.get('/knowledge-base');
    return response.data;
  }

  async createKnowledgeBase(data) {
    const response = await this.axios.post('/knowledge-base', data);
    return response.data;
  }

  async updateKnowledgeBase(id, data) {
    const response = await this.axios.patch(`/knowledge-base/${id}`, data);
    return response.data;
  }

  async deleteKnowledgeBase(id) {
    const response = await this.axios.delete(`/knowledge-base/${id}`);
    return response.data;
  }

  // Calendar
  async getCalendarProviders() {
    const response = await this.axios.get('/calendar/providers');
    return response.data;
  }

  async deleteCalendarProvider(id) {
    const response = await this.axios.delete(`/calendar/providers/${id}`);
    return response.data;
  }

  async getCalendarEvents() {
    const response = await this.axios.get('/calendar/events');
    return response.data;
  }

  async createCalendarEvent(data) {
    const response = await this.axios.post('/calendar/events', data);
    return response.data;
  }

  async getUpcomingEvents(hours = 24) {
    const response = await this.axios.get(`/calendar/events/upcoming?hours=${hours}`);
    return response.data;
  }

  // Follow-ups
  async getFollowUps() {
    const response = await this.axios.get('/follow-ups');
    return response.data;
  }

  async getFollowUp(id) {
    const response = await this.axios.get(`/follow-ups/${id}`);
    return response.data;
  }

  async createFollowUp(data) {
    const response = await this.axios.post('/follow-ups', data);
    return response.data;
  }

  async deleteFollowUp(id) {
    const response = await this.axios.delete(`/follow-ups/${id}`);
    return response.data;
  }

  // OAuth
  async getGoogleOAuthUrl(accountType = 'email') {
    const response = await this.axios.get(`/oauth/google/url?account_type=${accountType}`);
    return response.data;
  }

  async handleGoogleCallback(code, state, accountType = 'email') {
    const response = await this.axios.post(`/oauth/google/callback?code=${code}&state=${state}&account_type=${accountType}`);
    return response.data;
  }

  async getMicrosoftOAuthUrl(accountType = 'email') {
    const response = await this.axios.get(`/oauth/microsoft/url?account_type=${accountType}`);
    return response.data;
  }

  async handleMicrosoftCallback(code, state, accountType = 'email') {
    const response = await this.axios.post(`/oauth/microsoft/callback?code=${code}&state=${state}&account_type=${accountType}`);
    return response.data;
  }

  // System
  async getSystemStatus() {
    const response = await this.axios.get('/system/status');
    return response.data;
  }

  async testEmailProcessing() {
    const response = await this.axios.post('/system/test-email-processing');
    return response.data;
  }

  async startPolling() {
    const response = await this.axios.post('/system/start-polling');
    return response.data;
  }

  async stopPolling() {
    const response = await this.axios.post('/system/stop-polling');
    return response.data;
  }

  // Campaign Contacts
  async getCampaignContacts(params = {}) {
    const response = await this.axios.get('/campaign/contacts', { params });
    return response.data;
  }

  async getCampaignContact(id) {
    const response = await this.axios.get(`/campaign/contacts/${id}`);
    return response.data;
  }

  async createCampaignContact(data) {
    const response = await this.axios.post('/campaign/contacts', data);
    return response.data;
  }

  async updateCampaignContact(id, data) {
    const response = await this.axios.put(`/campaign/contacts/${id}`, data);
    return response.data;
  }

  async deleteCampaignContact(id) {
    const response = await this.axios.delete(`/campaign/contacts/${id}`);
    return response.data;
  }

  async bulkUploadContacts(formData) {
    const response = await this.axios.post('/campaign/contacts/bulk-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async downloadContactTemplate() {
    const response = await this.axios.get('/campaign/contacts/template/download', {
      responseType: 'blob',
    });
    return response.data;
  }

  // Campaign Templates
  async getCampaignTemplates(params = {}) {
    const response = await this.axios.get('/campaign/templates', { params });
    return response.data;
  }

  async getCampaignTemplate(id) {
    const response = await this.axios.get(`/campaign/templates/${id}`);
    return response.data;
  }

  async createCampaignTemplate(data) {
    const response = await this.axios.post('/campaign/templates', data);
    return response.data;
  }

  async updateCampaignTemplate(id, data) {
    const response = await this.axios.put(`/campaign/templates/${id}`, data);
    return response.data;
  }

  async deleteCampaignTemplate(id) {
    const response = await this.axios.delete(`/campaign/templates/${id}`);
    return response.data;
  }

  // Campaigns
  async getCampaigns(params = {}) {
    const response = await this.axios.get('/campaign/campaigns', { params });
    return response.data;
  }

  async getCampaign(id) {
    const response = await this.axios.get(`/campaign/campaigns/${id}`);
    return response.data;
  }

  async createCampaign(data) {
    const response = await this.axios.post('/campaign/campaigns', data);
    return response.data;
  }

  async updateCampaign(id, data) {
    const response = await this.axios.put(`/campaign/campaigns/${id}`, data);
    return response.data;
  }

  async deleteCampaign(id) {
    const response = await this.axios.delete(`/campaign/campaigns/${id}`);
    return response.data;
  }

  async startCampaign(id) {
    const response = await this.axios.post(`/campaign/campaigns/${id}/start`);
    return response.data;
  }

  async pauseCampaign(id) {
    const response = await this.axios.post(`/campaign/campaigns/${id}/pause`);
    return response.data;
  }

  async resumeCampaign(id) {
    const response = await this.axios.post(`/campaign/campaigns/${id}/resume`);
    return response.data;
  }

  async stopCampaign(id) {
    const response = await this.axios.post(`/campaign/campaigns/${id}/stop`);
    return response.data;
  }

  async getCampaignAnalytics(id) {
    const response = await this.axios.get(`/campaign/campaigns/${id}/analytics`);
    return response.data;
  }

  // Contact Lists
  async getContactLists(params = {}) {
    const response = await this.axios.get('/campaign/lists', { params });
    return response.data;
  }

  async getContactList(id) {
    const response = await this.axios.get(`/campaign/lists/${id}`);
    return response.data;
  }

  async createContactList(data) {
    const response = await this.axios.post('/campaign/lists', data);
    return response.data;
  }

  async updateContactList(id, data) {
    const response = await this.axios.put(`/campaign/lists/${id}`, data);
    return response.data;
  }

  async deleteContactList(id) {
    const response = await this.axios.delete(`/campaign/lists/${id}`);
    return response.data;
  }

  async addContactsToList(id, contactIds) {
    const response = await this.axios.post(`/campaign/lists/${id}/add-contacts`, {
      contact_ids: contactIds
    });
    return response.data;
  }

  async removeContactsFromList(id, contactIds) {
    const response = await this.axios.post(`/campaign/lists/${id}/remove-contacts`, {
      contact_ids: contactIds
    });
    return response.data;
  }

  async getListContacts(id) {
    const response = await this.axios.get(`/campaign/lists/${id}/contacts`);
    return response.data;
  }

  // ============ Inbound Leads API ============
  
  async getLeads(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const response = await this.axios.get(`/leads${queryString ? '?' + queryString : ''}`);
    return response.data;
  }

  async getLeadDetail(leadId) {
    const response = await this.axios.get(`/leads/${leadId}`);
    return response.data;
  }

  async updateLead(leadId, data) {
    const response = await this.axios.put(`/leads/${leadId}`, data);
    return response.data;
  }

  async updateLeadStage(leadId, data) {
    const response = await this.axios.post(`/leads/${leadId}/stage`, data);
    return response.data;
  }

  async getLeadEmails(leadId) {
    const response = await this.axios.get(`/leads/${leadId}/emails`);
    return response.data;
  }

  async getLeadStats() {
    const response = await this.axios.get('/leads/stats/summary');
    return response.data;
  }

  // ============ HubSpot Integration API ============
  
  async startHubSpotOAuth() {
    const token = localStorage.getItem('token');
    const response = await this.axios.get('/hubspot/start-oauth', {
      params: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }

  async getHubSpotStatus() {
    const token = localStorage.getItem('token');
    const response = await this.axios.get('/hubspot/status', {
      params: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }

  async disconnectHubSpot() {
    const token = localStorage.getItem('token');
    const response = await this.axios.post('/hubspot/disconnect', {}, {
      params: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }

  async syncLeadsToHubSpot(leadIds = null) {
    const token = localStorage.getItem('token');
    const response = await this.axios.post('/hubspot/sync-leads', { lead_ids: leadIds }, {
      params: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }

  // Admin HubSpot APIs
  async adminEnableHubSpotForUser(userId, reason = null) {
    const token = localStorage.getItem('token');
    const response = await this.axios.post(`/hubspot/admin/enable-for-user`, { reason }, {
      params: { 
        Authorization: `Bearer ${token}`,
        target_user_id: userId 
      }
    });
    return response.data;
  }

  async adminDisableHubSpotForUser(userId, reason) {
    const token = localStorage.getItem('token');
    const response = await this.axios.post(`/hubspot/admin/disable-for-user`, { reason }, {
      params: { 
        Authorization: `Bearer ${token}`,
        target_user_id: userId 
      }
    });
    return response.data;
  }

  async adminGetHubSpotConnections(skip = 0, limit = 100) {
    const token = localStorage.getItem('token');
    const response = await this.axios.get('/hubspot/admin/connections', {
      params: { 
        Authorization: `Bearer ${token}`,
        skip,
        limit 
      }
    });
    return response.data;
  }

  // Lead Qualification Criteria
  async getQualificationCriteria() {
    const response = await this.axios.get('/lead-qualification-criteria');
    return response.data;
  }

  async getQualificationCriteriaById(id) {
    const response = await this.axios.get(`/lead-qualification-criteria/${id}`);
    return response.data;
  }

  async createQualificationCriteria(data) {
    const response = await this.axios.post('/lead-qualification-criteria', data);
    return response.data;
  }

  async updateQualificationCriteria(id, data) {
    const response = await this.axios.put(`/lead-qualification-criteria/${id}`, data);
    return response.data;
  }

  async deleteQualificationCriteria(id) {
    const response = await this.axios.delete(`/lead-qualification-criteria/${id}`);
    return response.data;
  }

  // Lead Nurturing Config
  async getNurturingConfigs() {
    const response = await this.axios.get('/lead-nurturing-config');
    return response.data;
  }

  async getNurturingConfigById(id) {
    const response = await this.axios.get(`/lead-nurturing-config/${id}`);
    return response.data;
  }

  async createNurturingConfig(data) {
    const response = await this.axios.post('/lead-nurturing-config', data);
    return response.data;
  }

  async updateNurturingConfig(id, data) {
    const response = await this.axios.put(`/lead-nurturing-config/${id}`, data);
    return response.data;
  }

  async deleteNurturingConfig(id) {
    const response = await this.axios.delete(`/lead-nurturing-config/${id}`);
    return response.data;
  }

  // User Settings (for global toggles)
  async updateUserSettings(data) {
    const response = await this.axios.put('/auth/settings', data);
    return response.data;
  }

  // Test Flow APIs
  async testCompleteFlow(data) {
    const response = await this.axios.post('/test/complete-flow', data);
    return response.data;
  }

  async getSystemStatus() {
    const response = await this.axios.get('/test/system-status');
    return response.data;
  }

  // Test Session APIs (Multi-turn conversation testing)
  async sendTestMessage(data) {
    const response = await this.axios.post('/test-session/send-message', data);
    return response.data;
  }

  async getTestSession(sessionId) {
    const response = await this.axios.get(`/test-session/session/${sessionId}`);
    return response.data;
  }

  async deleteTestSession(sessionId) {
    const response = await this.axios.delete(`/test-session/session/${sessionId}`);
    return response.data;
  }
}

export default new API();
