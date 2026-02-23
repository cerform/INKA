import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, Loader2 } from 'lucide-react';

interface SetupConfig {
    botToken: string;
    apiSecretKey: string;
    databaseUrl: string;
    gcpProjectId: string;
    adminEmail: string;
    adminPassword: string;
}

export default function SetupWizard() {
    const { t, i18n } = useTranslation();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const changeLanguage = (lng: string) => {
        i18n.changeLanguage(lng);
    };

    const [config, setConfig] = useState<SetupConfig>({
        botToken: '',
        apiSecretKey: '',
        databaseUrl: '',
        gcpProjectId: '',
        adminEmail: '',
        adminPassword: '',
    });

    const handleChange = (field: keyof SetupConfig) => (e: React.ChangeEvent<HTMLInputElement>) => {
        setConfig({ ...config, [field]: e.target.value });
    };

    const generateSecretKey = () => {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        const key = btoa(String.fromCharCode(...array));
        setConfig({ ...config, apiSecretKey: key });
    };

    const validateStep = () => {
        setError('');

        if (step === 1) {
            if (!config.botToken || !config.botToken.includes(':')) {
                setError(t('setup.error_bot_token'));
                return false;
            }
            if (!config.apiSecretKey || config.apiSecretKey.length < 32) {
                setError(t('setup.error_secret_key'));
                return false;
            }
        }

        if (step === 2) {
            if (!config.databaseUrl || !config.databaseUrl.startsWith('postgresql://')) {
                setError(t('setup.error_db_url'));
                return false;
            }
        }

        if (step === 3) {
            if (!config.adminEmail || !config.adminEmail.includes('@')) {
                setError(t('setup.error_email'));
                return false;
            }
            if (!config.adminPassword || config.adminPassword.length < 8) {
                setError(t('setup.error_password'));
                return false;
            }
        }

        return true;
    };

    const handleNext = () => {
        if (validateStep()) {
            setStep(step + 1);
        }
    };

    const handleSubmit = async () => {
        if (!validateStep()) return;

        setLoading(true);
        setError('');

        try {
            const response = await fetch('/api/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || t('setup.error_setup'));
            }

            setSuccess(true);
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
                <Card className="w-full max-w-md">
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
                            <h2 className="text-2xl font-bold mb-2">{t('setup.success_title')}</h2>
                            <p className="text-gray-600">{t('setup.success_message')}</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <Card className="w-full max-w-2xl">
                <CardHeader className="relative">
                    <div className="absolute top-6 right-6 flex gap-2">
                        <Button variant="ghost" size="sm" onClick={() => changeLanguage('ru')}>RU</Button>
                        <Button variant="ghost" size="sm" onClick={() => changeLanguage('he')}>HE</Button>
                        <Button variant="ghost" size="sm" onClick={() => changeLanguage('en')}>EN</Button>
                    </div>
                    <CardTitle className="text-3xl">{t('setup.title')}</CardTitle>
                    <CardDescription>
                        {t('setup.step_count', { step })}
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-6">
                    {/* Progress Bar */}
                    <div className="flex gap-2">
                        {[1, 2, 3].map((s) => (
                            <div
                                key={s}
                                className={`h-2 flex-1 rounded-full ${s <= step ? 'bg-blue-500' : 'bg-gray-200'
                                    }`}
                            />
                        ))}
                    </div>

                    {error && (
                        <Alert variant="destructive">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    {/* Step 1: Bot & API Configuration */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-semibold">{t('setup.bot_api_title')}</h3>

                            <div className="space-y-2">
                                <Label htmlFor="botToken">{t('setup.bot_token')}</Label>
                                <Input
                                    id="botToken"
                                    placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                                    value={config.botToken}
                                    onChange={handleChange('botToken')}
                                />
                                <p className="text-sm text-gray-500">
                                    {t('setup.bot_token_hint')}
                                </p>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <Label htmlFor="apiSecretKey">{t('setup.api_secret')}</Label>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={generateSecretKey}
                                    >
                                        {t('setup.generate')}
                                    </Button>
                                </div>
                                <Input
                                    id="apiSecretKey"
                                    type="password"
                                    placeholder="Min 32 chars"
                                    value={config.apiSecretKey}
                                    onChange={handleChange('apiSecretKey')}
                                />
                                <p className="text-sm text-gray-500">
                                    {t('setup.api_secret_hint')}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Database Configuration */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-semibold">{t('setup.database_title')}</h3>

                            <div className="space-y-2">
                                <Label htmlFor="databaseUrl">{t('setup.db_url')}</Label>
                                <Input
                                    id="databaseUrl"
                                    placeholder="postgresql://user:password@host:5432/dbname"
                                    value={config.databaseUrl}
                                    onChange={handleChange('databaseUrl')}
                                />
                                <p className="text-sm text-gray-500">
                                    {t('setup.db_url_hint')}
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="gcpProjectId">{t('setup.gcp_project')}</Label>
                                <Input
                                    id="gcpProjectId"
                                    placeholder="my-project-id"
                                    value={config.gcpProjectId}
                                    onChange={handleChange('gcpProjectId')}
                                />
                                <p className="text-sm text-gray-500">
                                    {t('setup.gcp_project_hint')}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Admin Account */}
                    {step === 3 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-semibold">{t('setup.admin_account_title')}</h3>

                            <div className="space-y-2">
                                <Label htmlFor="adminEmail">{t('setup.email')}</Label>
                                <Input
                                    id="adminEmail"
                                    type="email"
                                    placeholder="admin@example.com"
                                    value={config.adminEmail}
                                    onChange={handleChange('adminEmail')}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="adminPassword">{t('setup.password')}</Label>
                                <Input
                                    id="adminPassword"
                                    type="password"
                                    placeholder="Min 8 chars"
                                    value={config.adminPassword}
                                    onChange={handleChange('adminPassword')}
                                />
                            </div>

                            <Alert>
                                <AlertDescription>
                                    {t('setup.admin_alert')}
                                </AlertDescription>
                            </Alert>
                        </div>
                    )}

                    {/* Navigation Buttons */}
                    <div className="flex justify-between pt-4">
                        <Button
                            variant="outline"
                            onClick={() => setStep(step - 1)}
                            disabled={step === 1 || loading}
                        >
                            {t('setup.back')}
                        </Button>

                        {step < 3 ? (
                            <Button onClick={handleNext} disabled={loading}>
                                {t('setup.next')}
                            </Button>
                        ) : (
                            <Button onClick={handleSubmit} disabled={loading}>
                                {loading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        {t('setup.setting_up')}
                                    </>
                                ) : (
                                    t('setup.finish')
                                )}
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
