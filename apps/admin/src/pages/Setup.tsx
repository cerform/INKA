import React, { useState } from 'react';
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
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

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
                setError('Введите корректный Bot Token от @BotFather');
                return false;
            }
            if (!config.apiSecretKey || config.apiSecretKey.length < 32) {
                setError('API Secret Key должен быть минимум 32 символа');
                return false;
            }
        }

        if (step === 2) {
            if (!config.databaseUrl || !config.databaseUrl.startsWith('postgresql://')) {
                setError('Введите корректный PostgreSQL URL');
                return false;
            }
        }

        if (step === 3) {
            if (!config.adminEmail || !config.adminEmail.includes('@')) {
                setError('Введите корректный email');
                return false;
            }
            if (!config.adminPassword || config.adminPassword.length < 8) {
                setError('Пароль должен быть минимум 8 символов');
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
                throw new Error(data.detail || 'Ошибка настройки');
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
                            <h2 className="text-2xl font-bold mb-2">Настройка завершена!</h2>
                            <p className="text-gray-600">Перенаправление на страницу входа...</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <Card className="w-full max-w-2xl">
                <CardHeader>
                    <CardTitle className="text-3xl">Настройка INKA Admin</CardTitle>
                    <CardDescription>
                        Шаг {step} из 3 - Первоначальная конфигурация системы
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
                            <h3 className="text-xl font-semibold">Telegram Bot & API</h3>

                            <div className="space-y-2">
                                <Label htmlFor="botToken">Bot Token</Label>
                                <Input
                                    id="botToken"
                                    placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                                    value={config.botToken}
                                    onChange={handleChange('botToken')}
                                />
                                <p className="text-sm text-gray-500">
                                    Получите токен у @BotFather в Telegram
                                </p>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <Label htmlFor="apiSecretKey">API Secret Key</Label>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={generateSecretKey}
                                    >
                                        Сгенерировать
                                    </Button>
                                </div>
                                <Input
                                    id="apiSecretKey"
                                    type="password"
                                    placeholder="Минимум 32 символа"
                                    value={config.apiSecretKey}
                                    onChange={handleChange('apiSecretKey')}
                                />
                                <p className="text-sm text-gray-500">
                                    Используется для шифрования JWT токенов
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Database Configuration */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-semibold">База Данных</h3>

                            <div className="space-y-2">
                                <Label htmlFor="databaseUrl">PostgreSQL URL</Label>
                                <Input
                                    id="databaseUrl"
                                    placeholder="postgresql://user:password@host:5432/dbname"
                                    value={config.databaseUrl}
                                    onChange={handleChange('databaseUrl')}
                                />
                                <p className="text-sm text-gray-500">
                                    Для Cloud SQL используйте формат: postgresql://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="gcpProjectId">Google Cloud Project ID (опционально)</Label>
                                <Input
                                    id="gcpProjectId"
                                    placeholder="my-project-id"
                                    value={config.gcpProjectId}
                                    onChange={handleChange('gcpProjectId')}
                                />
                                <p className="text-sm text-gray-500">
                                    Для интеграции с Google Cloud Storage и Secret Manager
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Admin Account */}
                    {step === 3 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-semibold">Аккаунт Администратора</h3>

                            <div className="space-y-2">
                                <Label htmlFor="adminEmail">Email</Label>
                                <Input
                                    id="adminEmail"
                                    type="email"
                                    placeholder="admin@example.com"
                                    value={config.adminEmail}
                                    onChange={handleChange('adminEmail')}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="adminPassword">Пароль</Label>
                                <Input
                                    id="adminPassword"
                                    type="password"
                                    placeholder="Минимум 8 символов"
                                    value={config.adminPassword}
                                    onChange={handleChange('adminPassword')}
                                />
                            </div>

                            <Alert>
                                <AlertDescription>
                                    Этот аккаунт будет иметь полный доступ к системе. Сохраните пароль в надежном месте.
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
                            Назад
                        </Button>

                        {step < 3 ? (
                            <Button onClick={handleNext} disabled={loading}>
                                Далее
                            </Button>
                        ) : (
                            <Button onClick={handleSubmit} disabled={loading}>
                                {loading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Настройка...
                                    </>
                                ) : (
                                    'Завершить настройку'
                                )}
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
