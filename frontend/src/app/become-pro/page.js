'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiGet, apiPost, apiPatch, apiPatchForm } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { CATEGORIES, KYC_DOC_TYPES, LOCATION_DOC_TYPES } from '@/lib/constants';
import { Check, ArrowRight, ArrowLeft, Upload, Loader2, ShieldCheck } from 'lucide-react';
import styles from './becomePro.module.css';

const STEPS = ['Personal Info', 'Service Info', 'KYC', 'PCC', 'Skills', 'Location'];

export default function BecomeProPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [appStatus, setAppStatus] = useState(null);
  const [applicationStarted, setApplicationStarted] = useState(false);

  const [form, setForm] = useState({
    // Personal
    full_name: '', date_of_birth: '', phone_number: '', bio: '',
    // Service
    service_category: '', years_of_experience: 0, portfolio_link: '',
    // KYC
    kyc_document_type: '', kyc_document_number: '',
    kyc_document_front: null, kyc_document_back: null, selfie_with_id: null,
    // PCC
    pcc_document: null, pcc_issue_date: '', pcc_issuing_authority: '',
    // Skills
    skill_certificate_1: null, skill_certificate_2: null, skill_certificate_3: null,
    // Location
    address_line1: '', address_line2: '', city: '', state: '', pincode: '',
    location_document_type: '', location_document: null,
  });

  useEffect(() => {
    const checkStatus = async () => {
      const { data, error } = await apiGet('/status/');
      if (data) {
        setAppStatus(data);
        if (['draft', 'resubmission_required'].includes(data.status)) {
          setApplicationStarted(true);
        }
      }
      setLoading(false);
    };
    checkStatus();
  }, []);

  const handleStartApplication = async () => {
    setSubmitting(true);
    const { data, error } = await apiPost('/apply/', {});
    setSubmitting(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to start application.');
      return;
    }

    setApplicationStarted(true);
    toast.success('Application started!');
  };

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (files) {
      setForm(prev => ({ ...prev, [name]: files[0] }));
    } else {
      setForm(prev => ({ ...prev, [name]: value }));
    }
  };

  const stepEndpoints = [
    '/step/personal/', '/step/service/', '/step/kyc/',
    '/step/pcc/', '/step/skills/', '/step/location/',
  ];

  const getStepFields = (stepIndex) => {
    switch (stepIndex) {
      case 0: return ['full_name', 'date_of_birth', 'phone_number', 'bio'];
      case 1: return ['service_category', 'years_of_experience', 'portfolio_link'];
      case 2: return ['kyc_document_type', 'kyc_document_number', 'kyc_document_front', 'kyc_document_back', 'selfie_with_id'];
      case 3: return ['pcc_document', 'pcc_issue_date', 'pcc_issuing_authority'];
      case 4: return ['skill_certificate_1', 'skill_certificate_2', 'skill_certificate_3'];
      case 5: return ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'location_document_type', 'location_document'];
      default: return [];
    }
  };

  const saveStep = async () => {
    const fields = getStepFields(step);
    const hasFile = fields.some(f => form[f] instanceof File);

    setSubmitting(true);

    let result;
    if (hasFile) {
      const fd = new FormData();
      fields.forEach(f => {
        if (form[f] !== null && form[f] !== undefined && form[f] !== '') {
          fd.append(f, form[f]);
        }
      });
      result = await apiPatchForm(stepEndpoints[step], fd);
    } else {
      const body = {};
      fields.forEach(f => { if (form[f] !== '' && form[f] !== null) body[f] = form[f]; });
      result = await apiPatch(stepEndpoints[step], body);
    }

    setSubmitting(false);

    if (result.error) {
      toast.error(typeof result.error === 'string' ? result.error : 'Failed to save. Check your inputs.');
      return false;
    }

    toast.success('Saved!');
    return true;
  };

  const handleNext = async () => {
    const saved = await saveStep();
    if (saved && step < STEPS.length - 1) setStep(step + 1);
  };

  const handleSubmitApplication = async () => {
    const saved = await saveStep();
    if (!saved) return;

    setSubmitting(true);
    const { error } = await apiPost('/submit/', {});
    setSubmitting(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to submit.');
      return;
    }

    toast.success('Application submitted! We\'ll review it and get back to you soon.');
    router.push('/browse');
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="container container--narrow">
          <div className="skeleton" style={{ height: 300 }} />
        </div>
      </div>
    );
  }

  // Show status if already submitted
  if (appStatus && !['draft', 'resubmission_required'].includes(appStatus.status)) {
    return (
      <div className={styles.page}>
        <div className="container container--narrow">
          <div className={styles.statusCard}>
            <ShieldCheck size={48} style={{ color: 'var(--color-success)' }} />
            <h2 className="display-md" style={{ marginTop: 16 }}>Application {appStatus.status.replace('_', ' ')}</h2>
            <p className="text-md text-muted" style={{ marginTop: 8 }}>
              {appStatus.status === 'submitted' && 'Your application is being reviewed. We\'ll notify you soon.'}
              {appStatus.status === 'under_review' && 'Our team is currently reviewing your application.'}
              {appStatus.status === 'approved' && 'Congratulations! Your application has been approved.'}
              {appStatus.status === 'rejected' && `Your application was rejected. Reason: ${appStatus.rejection_reason || 'Not specified'}`}
            </p>
            <div className={styles.verifyGrid}>
              {['kyc_verified', 'pcc_verified', 'skills_verified', 'location_verified'].map(key => (
                <div key={key} className={`${styles.verifyItem} ${appStatus[key] ? styles.verified : ''}`}>
                  <Check size={16} />
                  <span>{key.replace('_verified', '').replace('_', ' ').toUpperCase()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Start Application
  if (!applicationStarted) {
    return (
      <div className={styles.page}>
        <div className="container container--narrow">
          <div className={styles.startCard}>
            <h1 className="display-md">Become a HireHub Pro</h1>
            <p className="text-lg text-muted" style={{ marginTop: 12, maxWidth: 480 }}>
              Join our network of verified professionals. Complete the application form
              and start earning on your own terms.
            </p>
            <button
              className="btn btn--accent btn--lg"
              onClick={handleStartApplication}
              disabled={submitting}
              style={{ marginTop: 28 }}
            >
              {submitting ? 'Starting…' : 'Start Application'} <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className="container container--narrow">
        <h1 className="display-md" style={{ marginBottom: 8 }}>Pro Application</h1>
        <p className="text-md text-muted" style={{ marginBottom: 32 }}>Step {step + 1} of {STEPS.length}: {STEPS[step]}</p>

        {/* Step Indicator */}
        <div className="step-indicator">
          {STEPS.map((s, i) => (
            <div key={s} style={{ display: 'contents' }}>
              <button
                className={`step-dot ${i < step ? 'step-dot--done' : i === step ? 'step-dot--active' : 'step-dot--upcoming'}`}
                onClick={() => i < step && setStep(i)}
                style={{ cursor: i < step ? 'pointer' : 'default' }}
              >
                {i < step ? <Check size={14} /> : i + 1}
              </button>
              {i < STEPS.length - 1 && (
                <div className={`step-line ${i < step ? 'step-line--done' : ''}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Forms */}
        <div className={styles.stepForm}>
          {step === 0 && (
            <>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input className="form-input" name="full_name" value={form.full_name} onChange={handleChange} placeholder="Your full name" />
              </div>
              <div className="form-group">
                <label className="form-label">Date of Birth</label>
                <input className="form-input" name="date_of_birth" type="date" value={form.date_of_birth} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">Phone Number</label>
                <input className="form-input" name="phone_number" value={form.phone_number} onChange={handleChange} placeholder="+91 9876543210" />
              </div>
              <div className="form-group">
                <label className="form-label">Bio</label>
                <textarea className="form-input" name="bio" value={form.bio} onChange={handleChange} placeholder="Tell clients about yourself and your experience" rows={3} />
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <div className="form-group">
                <label className="form-label">Service Category</label>
                <select className="form-input" name="service_category" value={form.service_category} onChange={handleChange}>
                  <option value="">Select a category</option>
                  {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Years of Experience</label>
                <input className="form-input" name="years_of_experience" type="number" min="0" value={form.years_of_experience} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">Portfolio Link (optional)</label>
                <input className="form-input" name="portfolio_link" type="url" value={form.portfolio_link} onChange={handleChange} placeholder="https://..." />
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="form-group">
                <label className="form-label">Document Type</label>
                <select className="form-input" name="kyc_document_type" value={form.kyc_document_type} onChange={handleChange}>
                  <option value="">Select document type</option>
                  {KYC_DOC_TYPES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Document Number</label>
                <input className="form-input" name="kyc_document_number" value={form.kyc_document_number} onChange={handleChange} placeholder="XXXX-XXXX-XXXX" />
              </div>
              {['kyc_document_front', 'kyc_document_back', 'selfie_with_id'].map(field => (
                <div className="form-group" key={field}>
                  <label className="form-label">{field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</label>
                  <label className={styles.fileInput}>
                    <Upload size={16} />
                    {form[field]?.name || 'Choose file'}
                    <input type="file" name={field} accept="image/*" onChange={handleChange} className="sr-only" />
                  </label>
                </div>
              ))}
            </>
          )}

          {step === 3 && (
            <>
              <div className="form-group">
                <label className="form-label">PCC Document</label>
                <label className={styles.fileInput}>
                  <Upload size={16} />
                  {form.pcc_document?.name || 'Choose file'}
                  <input type="file" name="pcc_document" accept="image/*,.pdf" onChange={handleChange} className="sr-only" />
                </label>
              </div>
              <div className="form-group">
                <label className="form-label">Issue Date</label>
                <input className="form-input" name="pcc_issue_date" type="date" value={form.pcc_issue_date} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">Issuing Authority</label>
                <input className="form-input" name="pcc_issuing_authority" value={form.pcc_issuing_authority} onChange={handleChange} placeholder="e.g. District Magistrate, Delhi" />
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <p className="text-sm text-muted" style={{ marginBottom: 16 }}>Upload up to 3 skill certificates or qualification documents.</p>
              {['skill_certificate_1', 'skill_certificate_2', 'skill_certificate_3'].map((field, i) => (
                <div className="form-group" key={field}>
                  <label className="form-label">Certificate {i + 1} {i > 0 ? '(optional)' : ''}</label>
                  <label className={styles.fileInput}>
                    <Upload size={16} />
                    {form[field]?.name || 'Choose file'}
                    <input type="file" name={field} accept="image/*,.pdf" onChange={handleChange} className="sr-only" />
                  </label>
                </div>
              ))}
            </>
          )}

          {step === 5 && (
            <>
              <div className="form-group">
                <label className="form-label">Address Line 1</label>
                <input className="form-input" name="address_line1" value={form.address_line1} onChange={handleChange} placeholder="House/Flat number, Street" />
              </div>
              <div className="form-group">
                <label className="form-label">Address Line 2 (optional)</label>
                <input className="form-input" name="address_line2" value={form.address_line2} onChange={handleChange} placeholder="Landmark, Area" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="form-group">
                  <label className="form-label">City</label>
                  <input className="form-input" name="city" value={form.city} onChange={handleChange} />
                </div>
                <div className="form-group">
                  <label className="form-label">State</label>
                  <input className="form-input" name="state" value={form.state} onChange={handleChange} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Pincode</label>
                <input className="form-input" name="pincode" value={form.pincode} onChange={handleChange} maxLength={6} />
              </div>
              <div className="form-group">
                <label className="form-label">Address Proof Type</label>
                <select className="form-input" name="location_document_type" value={form.location_document_type} onChange={handleChange}>
                  <option value="">Select document</option>
                  {LOCATION_DOC_TYPES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Address Proof</label>
                <label className={styles.fileInput}>
                  <Upload size={16} />
                  {form.location_document?.name || 'Choose file'}
                  <input type="file" name="location_document" accept="image/*,.pdf" onChange={handleChange} className="sr-only" />
                </label>
              </div>
            </>
          )}
        </div>

        {/* Navigation */}
        <div className={styles.stepNav}>
          {step > 0 && (
            <button className="btn btn--outline" onClick={() => setStep(step - 1)}>
              <ArrowLeft size={16} /> Back
            </button>
          )}
          <div style={{ flex: 1 }} />
          {step < STEPS.length - 1 ? (
            <button className="btn btn--primary" onClick={handleNext} disabled={submitting}>
              {submitting ? <Loader2 size={16} className={styles.spinner} /> : null}
              Save & Continue <ArrowRight size={16} />
            </button>
          ) : (
            <button className="btn btn--accent btn--lg" onClick={handleSubmitApplication} disabled={submitting}>
              {submitting ? <Loader2 size={16} className={styles.spinner} /> : null}
              Submit Application
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
