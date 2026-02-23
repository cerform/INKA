import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import ru from './locales/ru.json';
import he from './locales/he.json';

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources: {
            en: { translation: en },
            ru: { translation: ru },
            he: { translation: he },
        },
        fallbackLng: 'en',
        interpolation: {
            escapeValue: false,
        },
    });

// Handle RTL for Hebrew
i18n.on('languageChanged', (lng) => {
    document.dir = lng === 'he' ? 'rtl' : 'ltr';
});

export default i18n;
