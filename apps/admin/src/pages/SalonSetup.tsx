import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './SalonSetup.css';

interface WorkSchedule {
  day_of_week: string;
  is_working: boolean;
  start_time: string;
  end_time: string;
}

interface FormData {
  salon_name: string;
  specialization: string;
  work_start_time: string;
  work_end_time: string;
  timezone: string;
  telegram_bot_token: string;
  work_schedule: WorkSchedule[];
}

const DAYS_OF_WEEK = [
  'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
];

const TIMEZONES = [
  'UTC', 'Europe/London', 'Europe/Paris', 'Europe/Moscow', 
  'Asia/Tel_Aviv', 'Asia/Dubai', 'Asia/Bangkok', 'America/New_York'
];

const SPECIALIZATIONS = ['tattoo', 'piercing', 'nailArt', 'beauty', 'multiple'];

export const SalonSetup: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>({
    salon_name: '',
    specialization: 'tattoo',
    work_start_time: '09:00',
    work_end_time: '21:00',
    timezone: 'UTC',
    telegram_bot_token: '',
    work_schedule: DAYS_OF_WEEK.map(day => ({
      day_of_week: day,
      is_working: day !== 'sunday',
      start_time: '09:00',
      end_time: '21:00'
    }))
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleScheduleChange = (dayIndex: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      work_schedule: prev.work_schedule.map((schedule, idx) =>
        idx === dayIndex ? { ...schedule, [field]: value } : schedule
      )
    }));
  };

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  const handleNext = () => {
    if (step === 1) {
      if (!formData.salon_name.trim()) {
        setError(t('setup.validation.salonNameRequired'));
        return;
      }
    }
    if (step === 4) {
      if (formData.telegram_bot_token && formData.telegram_bot_token.length < 20) {
        setError(t('setup.validation.invalidBotToken'));
        return;
      }
    }
    setError(null);
    setStep(step + 1);
  };

  const handlePrev = () => {
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/setup/salon-init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Setup failed');
      }

      const data = await response.json();
      setApiKey(data.data.api_key);
      setStep(5);
    } catch (err) {
      setError(t('setup.error'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  return (
    <div className="setup-container">
      {/* Language Selector */}
      <div className="language-selector">
        <button
          onClick={() => handleLanguageChange('en')}
          className={i18n.language === 'en' ? 'active' : ''}
        >
          English
        </button>
        <button
          onClick={() => handleLanguageChange('ru')}
          className={i18n.language === 'ru' ? 'active' : ''}
        >
          Русский
        </button>
        <button
          onClick={() => handleLanguageChange('he')}
          className={i18n.language === 'he' ? 'active' : ''}
        >
          עברית
        </button>
      </div>

      <div className="setup-card">
        <h1>{t('setup.title')}</h1>
        <p className="subtitle">{t('setup.subtitle')}</p>

        {/* Progress Indicator */}
        <div className="progress-bar">
          <div className="progress" style={{ width: `${(step / 5) * 100}%` }} />
        </div>

        {error && <div className="error-message">{error}</div>}

        {/* Step 1: Basic Information */}
        {step === 1 && (
          <div className="step">
            <h2>{t('setup.step1')}</h2>
            <div className="form-group">
              <label htmlFor="salon_name">{t('setup.salonName')}</label>
              <input
                type="text"
                id="salon_name"
                name="salon_name"
                value={formData.salon_name}
                onChange={handleChange}
                placeholder={t('setup.salonNamePlaceholder')}
              />
            </div>
            <div className="form-group">
              <label htmlFor="timezone">{t('setup.timezone')}</label>
              <select
                id="timezone"
                name="timezone"
                value={formData.timezone}
                onChange={handleChange}
              >
                {TIMEZONES.map(tz => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Step 2: Specializations */}
        {step === 2 && (
          <div className="step">
            <h2>{t('setup.step2')}</h2>
            <p>{t('setup.specialization')}</p>
            <div className="checkbox-group">
              {SPECIALIZATIONS.map(spec => (
                <label key={spec} className="checkbox-label">
                  <input
                    type="radio"
                    name="specialization"
                    value={spec}
                    checked={formData.specialization === spec}
                    onChange={handleChange}
                  />
                  <span>{t(`setup.${spec}`)}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Work Schedule */}
        {step === 3 && (
          <div className="step">
            <h2>{t('setup.step3')}</h2>
            <div className="schedule-container">
              {formData.work_schedule.map((schedule, idx) => (
                <div key={idx} className="schedule-item">
                  <label className="day-label">
                    <input
                      type="checkbox"
                      checked={schedule.is_working}
                      onChange={(e) => handleScheduleChange(idx, 'is_working', e.target.checked)}
                    />
                    <span>{t(`setup.${schedule.day_of_week}`)}</span>
                  </label>
                  {schedule.is_working && (
                    <div className="time-inputs">
                      <input
                        type="time"
                        value={schedule.start_time}
                        onChange={(e) => handleScheduleChange(idx, 'start_time', e.target.value)}
                      />
                      <span>-</span>
                      <input
                        type="time"
                        value={schedule.end_time}
                        onChange={(e) => handleScheduleChange(idx, 'end_time', e.target.value)}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Integration Keys */}
        {step === 4 && (
          <div className="step">
            <h2>{t('setup.step4')}</h2>
            <div className="form-group">
              <label htmlFor="telegram_bot_token">{t('setup.telegramBotToken')}</label>
              <input
                type="text"
                id="telegram_bot_token"
                name="telegram_bot_token"
                value={formData.telegram_bot_token}
                onChange={handleChange}
                placeholder={t('setup.botTokenPlaceholder')}
              />
              <small>Optional - you can add this later</small>
            </div>
          </div>
        )}

        {/* Step 5: Success */}
        {step === 5 && (
          <div className="step success-step">
            <h2>✅ {t('setup.success')}</h2>
            {apiKey && (
              <div className="api-key-display">
                <p>{t('setup.apiKey')}</p>
                <div className="api-key-box">
                  <code>{apiKey}</code>
                  <button onClick={() => copyToClipboard(apiKey)}>
                    {t('setup.copyApiKey')}
                  </button>
                </div>
                <p className="warning">{t('setup.apiKeyInfo')}</p>
              </div>
            )}
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="button-group">
          {step > 1 && step < 5 && (
            <button onClick={handlePrev} className="btn btn-secondary">
              {t('setup.prev')}
            </button>
          )}
          {step < 4 && (
            <button onClick={handleNext} className="btn btn-primary">
              {t('setup.next')}
            </button>
          )}
          {step === 4 && (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="btn btn-success"
            >
              {loading ? t('setup.saving') : t('setup.finish')}
            </button>
          )}
          {step === 5 && (
            <button onClick={() => window.location.href = '/dashboard'} className="btn btn-success">
              Go to Dashboard
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SalonSetup;
