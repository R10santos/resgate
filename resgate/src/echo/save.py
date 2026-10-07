"""Checkpoints entre capítulos; leitura defensiva e escrita atômica."""
import json
import os
from pathlib import Path


class SaveSlot:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Eco7' / 'campanha.json'
        self.warning = ''

    def read(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('version') != 1:
                return None
            chapter = data.get('chapter')
            if type(chapter) is not int or not 0 <= chapter <= 4:
                return None
            flags = data.get('flags', {})
            if not isinstance(flags, dict):
                return None
            clean = {k: flags[k] for k in ('teo', 'ivo', 'maia', 'broadcast') if type(flags.get(k)) is bool}
            if flags.get('protocol') in ('preserve', 'purge'):
                clean['protocol'] = flags['protocol']
            if flags.get('difficulty') in ('explore', 'normal', 'survival'):
                clean['difficulty'] = flags['difficulty']
            for module in ('weapon', 'armor', 'reactor'):
                if type(flags.get(module)) is int and 0 <= flags[module] <= 5:
                    clean[module] = flags[module]
            logs = data.get('logs', [])
            if not isinstance(logs, list):
                return None
            return {'chapter': chapter, 'flags': clean, 'logs': [s for s in logs if isinstance(s, str) and len(s) < 40]}
        except (OSError, ValueError, TypeError):
            return None

    def write(self, chapter, flags, logs):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix('.tmp')
            tmp.write_text(json.dumps(dict(version=1, chapter=chapter, flags=flags, logs=logs), ensure_ascii=False), encoding='utf-8')
            tmp.replace(self.path)
            self.warning = ''
        except OSError:
            self.warning = 'Não foi possível salvar em disco. O checkpoint continua nesta sessão.'
