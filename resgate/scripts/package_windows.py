"""Empacota fonte e executável existente, sem caches ou versões antigas do exe."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = ROOT / 'dist/Eco7.exe'
    if not executable.is_file():
        raise SystemExit('Gere dist/Eco7.exe antes de empacotar.')
    paths = [ROOT / name for name in ('main.py', 'README.md', 'requirements.txt', 'requirements-build.txt',
                                     'iniciar.cmd', 'jogar.bat', 'gerar-executavel.bat', 'Eco7.spec')]
    paths.append(executable)
    for folder in ('src', 'tests', 'scripts', 'docs', 'LICENCAS', '.vscode'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    output = ROOT.parent / 'Eco7-Windows.zip'
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, 'Eco7/' + path.relative_to(ROOT).as_posix())
    with ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit('Arquivo inválido no pacote: ' + bad)
    print(f'{output} | {output.stat().st_size:,} bytes | {len(paths)} arquivos')


if __name__ == '__main__':
    main()
