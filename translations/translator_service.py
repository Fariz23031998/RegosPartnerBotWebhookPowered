from pathlib import Path
import json
from typing import Dict


class TranslatorService:
    _cache: Dict[str, dict] = {}  # Class-level cache
    _locales_dir = Path(__file__).parent / ''

    def __init__(self):
        # Load default language at startup
        self._load_language("en")
        self._load_language("ru")
        self._load_language("uz")

    def _load_language(self, lang: str):
        """Load language file into memory (only once)"""
        if lang not in self._cache:
            file_path = self._locales_dir / f'{lang}.json'
            with open(file_path, 'r', encoding='utf-8') as f:
                self._cache[lang] = json.load(f)

    def get_language_translations(self, lang: str) -> Dict[str, str]:
        self._load_language(lang)
        return self._cache[lang]


    def get_language_version(self, lang: str) -> dict:
        self._load_language(lang)
        return {"version": self._cache[lang]['version'], "last_updated": self._cache[lang]['last_updated']}


    def get(self, key: str, lang: str = None) -> str:
        return self._cache[lang]["translations"].get(key, key)

    def clear_cache(self):
        """Useful for hot-reloading in development"""
        self._cache.clear()

# translator_service = TranslatorService()
# test = translator_service.get('exchange_rate', 'ru')
# print(test)

