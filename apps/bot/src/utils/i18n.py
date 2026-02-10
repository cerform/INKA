import os
from fluent.runtime import FluentBundle, FluentResourceLoader

class I18nService:
    def __init__(self, locales_path: str, default_locale: str = "en"):
        self.loader = FluentResourceLoader(os.path.join(locales_path, "{locale}"))
        self.default_locale = default_locale
        self.bundles = {}
        self._load_bundles(["en", "ru"])

    def _load_bundles(self, locales: list[str]):
        for locale in locales:
            bundle = FluentBundle([locale])
            resource = self.loader.get_resource("messages.ftl", locale)
            if resource:
                bundle.add_resource(resource)
                self.bundles[locale] = bundle

    def get(self, key: str, locale: str | None = None, **kwargs) -> str:
        locale = locale or self.default_locale
        bundle = self.bundles.get(locale, self.bundles.get(self.default_locale))
        
        if not bundle:
            return key
            
        message = bundle.get_message(key)
        if not message or not message.value:
            return key
            
        params = {k: str(v) for k, v in kwargs.items()}
        errors = []
        result = bundle.format_pattern(message.value, params, errors)
        return result

# Initialize i18n
locales_dir = os.path.dirname(__file__)
i18n = I18nService(locales_dir)
gettext = i18n.get
