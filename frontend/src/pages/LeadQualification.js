import React, { useState, useEffect } from 'react';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import { Target, Plus, Edit2, Trash2, Save, X } from 'lucide-react';

const LeadQualification = () => {
  const [criteria, setCriteria] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    criteria_type: 'score_based',
    rules: [],
    questions: [],
    min_qualification_score: 60,
    max_exchanges: 3,
    auto_disqualify_on_fail: true
  });

  useEffect(() => {
    fetchCriteria();
  }, []);

  const fetchCriteria = async () => {
    try {
      setInitialLoading(true);
      const data = await API.getQualificationCriteria();
      setCriteria(data);
    } catch (error) {
      console.error('Error loading qualification criteria:', error);
      toast.error('Failed to load qualification criteria');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      if (editing) {
        await API.updateQualificationCriteria(editing, formData);
        toast.success('Criteria updated');
      } else {
        await API.createQualificationCriteria(formData);
        toast.success('Criteria created');
      }
      fetchCriteria();
      setShowForm(false);
      setEditing(null);
      resetForm();
    } catch (error) {
      toast.error('Failed to save');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this criteria?')) return;
    try {
      await API.deleteQualificationCriteria(id);
      toast.success('Deleted');
      fetchCriteria();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleEdit = (item) => {
    setEditing(item.id);
    setFormData({
      name: item.name,
      description: item.description || '',
      criteria_type: item.criteria_type,
      rules: item.rules || [],
      questions: item.questions || [],
      min_qualification_score: item.min_qualification_score || 60,
      max_exchanges: item.max_exchanges || 3,
      auto_disqualify_on_fail: item.auto_disqualify_on_fail !== undefined ? item.auto_disqualify_on_fail : true
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      criteria_type: 'score_based',
      rules: [],
      questions: [],
      min_qualification_score: 60,
      max_exchanges: 3,
      auto_disqualify_on_fail: true
    });
  };

  const addQuestion = () => {
    setFormData({
      ...formData,
      questions: [
        ...formData.questions,
        {
          question_id: `q_${Date.now()}`,
          question_text: '',
          question_key: `question_${formData.questions.length + 1}`,
          context_keywords: [],
          expected_answer_type: 'text',
          weight: 1.0,
          is_required: true,
          priority: formData.questions.length + 1,
          max_asks: 2,
          qualifying_answers: [],
          disqualifying_answers: []
        }
      ]
    });
  };

  const updateQuestion = (index, field, value) => {
    const updated = [...formData.questions];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, questions: updated });
  };

  const removeQuestion = (index) => {
    setFormData({ ...formData, questions: formData.questions.filter((_, i) => i !== index) });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Lead Qualification</h1>
          <p className="text-gray-600 mt-1">Define criteria to qualify/disqualify leads (0-100 scoring, threshold: 60)</p>
        </div>
        <Button onClick={() => setShowForm(true)} className="bg-purple-600">
          <Plus className="w-4 h-4 mr-2" />
          New Criteria
        </Button>
      </div>

      {initialLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading qualification criteria...</p>
          </div>
        </div>
      ) : (
        <>
          {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editing ? 'Edit' : 'Create'} Criteria</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              placeholder="Criteria Name"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
            <Textarea
              placeholder="Description (optional)"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows={2}
            />
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Min Score</Label>
                <Input type="number" value={formData.min_qualification_score} onChange={(e) => setFormData({...formData, min_qualification_score: parseInt(e.target.value)})} />
              </div>
              <div>
                <Label>Max Exchanges</Label>
                <Input type="number" value={formData.max_exchanges} onChange={(e) => setFormData({...formData, max_exchanges: parseInt(e.target.value)})} />
              </div>
              <div className="pt-6">
                <label className="flex items-center gap-2">
                  <Switch checked={formData.auto_disqualify_on_fail} onCheckedChange={(c) => setFormData({...formData, auto_disqualify_on_fail: c})} />
                  <span className="text-sm">Auto-disqualify</span>
                </label>
              </div>
            </div>

            <div className="border-t pt-4">
              <div className="flex justify-between mb-3">
                <Label>Questions</Label>
                <Button size="sm" variant="outline" onClick={addQuestion}>
                  <Plus className="w-4 h-4 mr-1" /> Add Question
                </Button>
              </div>
              
              <div className="space-y-3">
                {formData.questions.map((q, idx) => (
                  <div key={idx} className="border rounded p-4 space-y-3 bg-gray-50">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-gray-700">Question {idx + 1}</span>
                      <Button size="sm" variant="ghost" onClick={() => removeQuestion(idx)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    <div>
                      <Label className="text-xs text-gray-600">Question Text</Label>
                      <Input 
                        placeholder="e.g., What is your company size?" 
                        value={q.question_text} 
                        onChange={(e) => updateQuestion(idx, 'question_text', e.target.value)} 
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs text-gray-600">Question Key</Label>
                        <Input 
                          placeholder="e.g., company_size" 
                          value={q.question_key} 
                          onChange={(e) => updateQuestion(idx, 'question_key', e.target.value)} 
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-gray-600">Weight (0.0-1.0)</Label>
                        <Input 
                          type="number" 
                          placeholder="e.g., 0.25" 
                          value={q.weight} 
                          onChange={(e) => updateQuestion(idx, 'weight', parseFloat(e.target.value))} 
                          step="0.05"
                          min="0"
                          max="1"
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={q.is_required} 
                        onCheckedChange={(checked) => updateQuestion(idx, 'is_required', checked)} 
                      />
                      <Label className="text-sm">Required Question</Label>
                    </div>
                    
                    <div className="space-y-2 border-t pt-3">
                      <div>
                        <Label className="text-xs text-gray-600">✅ Qualifying Answers (Optional)</Label>
                        <p className="text-xs text-gray-500 mb-1">Comma-separated answers that qualify the lead (e.g., "51-200, 201-500, enterprise")</p>
                        <Input 
                          placeholder="Leave empty to accept any answer" 
                          value={(q.qualifying_answers || []).join(', ')} 
                          onChange={(e) => updateQuestion(idx, 'qualifying_answers', e.target.value ? e.target.value.split(',').map(s => s.trim()) : [])} 
                        />
                      </div>
                      
                      <div>
                        <Label className="text-xs text-gray-600">❌ Disqualifying Answers (Optional)</Label>
                        <p className="text-xs text-gray-500 mb-1">Comma-separated answers that disqualify the lead (e.g., "1-10, self-employed, freelancer")</p>
                        <Input 
                          placeholder="Leave empty if no disqualifying answers" 
                          value={(q.disqualifying_answers || []).join(', ')} 
                          onChange={(e) => updateQuestion(idx, 'disqualifying_answers', e.target.value ? e.target.value.split(',').map(s => s.trim()) : [])} 
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleSave} disabled={loading || !formData.name}>
                <Save className="w-4 h-4 mr-2" />
                Save
              </Button>
              <Button variant="outline" onClick={() => { setShowForm(false); setEditing(null); resetForm(); }}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {criteria.map((item) => (
        <Card key={item.id}>
          <CardHeader>
            <div className="flex justify-between">
              <div>
                <CardTitle>{item.name}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handleEdit(item)}>
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleDelete(item.id)}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-3">
              <div>
                <Label className="text-xs">Type</Label>
                <p className="text-sm font-medium">{item.criteria_type}</p>
              </div>
              <div>
                <Label className="text-xs">Min Score</Label>
                <p className="text-sm font-medium">{item.min_qualification_score}/100</p>
              </div>
              <div>
                <Label className="text-xs">Questions</Label>
                <p className="text-sm font-medium">{item.questions?.length || 0}</p>
              </div>
              <div>
                <Label className="text-xs">Enabled</Label>
                <Badge className={item.is_enabled ? 'bg-green-500' : 'bg-gray-400'}>{item.is_enabled ? 'Yes' : 'No'}</Badge>
              </div>
            </div>
            {item.questions?.length > 0 && (
              <div className="bg-purple-50 rounded p-3 space-y-2">
                <p className="text-sm font-semibold mb-2">Questions:</p>
                {item.questions.map((q, i) => (
                  <div key={i} className="bg-white rounded p-2 border">
                    <p className="text-sm font-medium text-gray-900">• {q.question_text}</p>
                    <div className="text-xs text-gray-600 mt-1 space-y-1">
                      <p>Key: <span className="font-mono">{q.question_key}</span> | Weight: {(q.weight * 100).toFixed(0)}% | {q.is_required ? '✓ Required' : '○ Optional'}</p>
                      {q.qualifying_answers && q.qualifying_answers.length > 0 && (
                        <p className="text-green-700">✅ Qualifying: {q.qualifying_answers.join(', ')}</p>
                      )}
                      {q.disqualifying_answers && q.disqualifying_answers.length > 0 && (
                        <p className="text-red-700">❌ Disqualifying: {q.disqualifying_answers.join(', ')}</p>
                      )}
                      {(!q.qualifying_answers || q.qualifying_answers.length === 0) && (!q.disqualifying_answers || q.disqualifying_answers.length === 0) && (
                        <p className="text-blue-700">ℹ️ Any answer accepted</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
        </>
      )}
    </div>
  );
};

export default LeadQualification;
