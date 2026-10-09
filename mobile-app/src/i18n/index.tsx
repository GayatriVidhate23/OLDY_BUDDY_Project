import { useState, createContext, useContext, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';

type LanguageCode = 'en' | 'hi' | 'mr';

const translations = {
  en: {
    hello: 'Hello',
    talkToBuddy: 'Talk to Buddy',
    myReminders: 'My Reminders',
    callFamily: 'Call Family',
    iNeedHelp: 'I Need Help',
    login: 'Login',
    signOut: 'Sign Out',
    elderGreeting: 'Hello, I am your Buddy',
    isMomOkay: 'Is Mom okay?',
    notSupported: 'Not supported in this app',
  },
  hi: {
    hello: 'नमस्ते',
    talkToBuddy: 'बडी से बात करें', // TODO: needs native-speaker review
    myReminders: 'मेरे रिमाइंडर', // TODO: needs native-speaker review
    callFamily: 'परिवार को कॉल करें', // TODO: needs native-speaker review
    iNeedHelp: 'मुझे मदद चाहिए', // TODO: needs native-speaker review
    login: 'लॉग इन करें', // TODO: needs native-speaker review
    signOut: 'साइन आउट', // TODO: needs native-speaker review
    elderGreeting: 'नमस्ते, मैं आपका बडी हूँ', // TODO: needs native-speaker review
    isMomOkay: 'क्या माँ ठीक हैं?', // TODO: needs native-speaker review
    notSupported: 'इस ऐप में समर्थित नहीं है', // TODO: needs native-speaker review
  },
  mr: {
    hello: 'नमस्कार',
    talkToBuddy: 'बडीशी बोला', // TODO: needs native-speaker review
    myReminders: 'माझे रिमाइंडर्स', // TODO: needs native-speaker review
    callFamily: 'कुटुंबाला कॉल करा', // TODO: needs native-speaker review
    iNeedHelp: 'मला मदत हवी आहे', // TODO: needs native-speaker review
    login: 'लॉग इन करा', // TODO: needs native-speaker review
    signOut: 'साइन आउट', // TODO: needs native-speaker review
    elderGreeting: 'नमस्कार, मी तुमचा बडी आहे', // TODO: needs native-speaker review
    isMomOkay: 'आई ठीक आहे का?', // TODO: needs native-speaker review
    notSupported: 'या अॅपमध्ये समर्थित नाही', // TODO: needs native-speaker review
  }
};

type Translations = typeof translations.en;

interface I18nContextType {
  lang: LanguageCode;
  t: (key: keyof Translations) => string;
  setLang: (lang: LanguageCode) => void;
}

export const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<LanguageCode>('en');
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    SecureStore.getItemAsync('language_pref').then((val) => {
      if (val === 'en' || val === 'hi' || val === 'mr') {
        setLangState(val);
      }
      setLoaded(true);
    });
  }, []);

  const setLang = async (newLang: LanguageCode) => {
    setLangState(newLang);
    await SecureStore.setItemAsync('language_pref', newLang);
  };

  const t = (key: keyof Translations) => {
    return translations[lang][key] || translations['en'][key];
  };

  if (!loaded) return null;

  return (
    <I18nContext.Provider value={{ lang, t, setLang }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useTranslation = () => {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useTranslation must be used within I18nProvider');
  return context;
};
