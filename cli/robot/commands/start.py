# cli/robot/commands/start.py
import pathlib
import textwrap
import typer
from typing_extensions import Annotated

# O dicionário FILES define a estrutura do projeto.
FILES = {
    'main.py': textwrap.dedent("""
        # main.py
        import robotkit
        import machine

        # --- Escreva seu código aqui ---
    """),

    'project.yaml': textwrap.dedent("""
        # project.yaml

        requirements:
            robotkit: true
            others: 
                # Adiciona outras bibliotecas de terceiros de /libs
                # - <file_name>.py
    """),

    'libs/__init__.py': '"""__init__.py"""',

    # For VSCode IDLE

    '.vscode/settings.json': textwrap.dedent("""
        {
            "python.analysis.extraPaths": [
                "./.vscode/fake_libs"
            ]
        }
    """),

    '.vscode/fake_libs/robot_kit/__init__.py': None,
    '.vscode/fake_libs/machine/__init__.py': None,
    '.vscode/fake_libs/rp2/__init__.py': None,
    '.vscode/fake_libs/time/__init__.py': None,
}

def run(vscode: Annotated[bool, typer.Option(help="Create a project for VSCode IDE", rich_help_panel="IDE")] = False):
    """Inicia um novo projeto."""
    project_root = pathlib.Path.cwd()

    for relative_path, content in FILES.items():
        file_path = project_root / relative_path

        if str(relative_path).split(r"/")[0] == ".vscode" and not vscode:
            break

        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            file_path.write_text((content or "").lstrip(), encoding="utf-8")
        except IOError as e:
            print(f"❌ Erro ao criar o arquivo {relative_path}: {e}")

    print("\n✅ Estrutura inicial de projeto criada com sucesso!")

# Para testar a função, você pode chamá-la aqui
if __name__ == '__main__':
    run()