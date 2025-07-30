# cli/robot/commands/build.py
import typer
import yaml
import shutil
from pathlib import Path
import os
import re
import requests
from typing_extensions import Annotated


from robot.core.utils import run_shell_command 
# --- Constantes ---
PROJECT_CONFIG_FILE = "project.yaml"
BUILD_DIR = Path("build")
LIBS_DIR = Path("libs")
MAIN_FILE = Path("main.py")

# --- Configuração da Biblioteca 'robot-kit' ---
ROBOT_KIT_GITHUB_URL = "https://github.com/JordanoPaganini/robo-rp2-framework"
ROBOT_KIT_REPO_PATH = "micropython-lib"
ROBOT_KIT_DOWNLOAD_DIR = Path("robotkit")


def _parse_github_url(url: str) -> tuple[str, str] | None:
    """Extrai 'owner/repo' de uma URL do GitHub."""
    match = re.search(r"github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)", url)
    if match:
        owner_repo = match.group(1)
        return tuple(owner_repo.split('/'))
    return None


def _download_github_dir(owner: str, repo: str, repo_path: str, local_path: Path, repeat: bool = False):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}"
    if not repeat: typer.echo(f"-> Acessando API do GitHub para buscar '{repo_path}'...")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        contents = response.json()

        local_path.mkdir(parents=True, exist_ok=True)

        for item in contents:
            item_name = item["name"]
            item_path = local_path / item_name

            if item["type"] == "file":
                typer.echo(f"   - Baixando arquivo: {item_name}")
                file_url = item["download_url"]
                file_content = requests.get(file_url).content
                with open(item_path, "wb") as f:
                    f.write(file_content)
            elif item["type"] == "dir":
                _download_github_dir(owner, repo, item["path"], item_path, True)

    except requests.exceptions.RequestException as e:
        typer.secho(f"ERRO ao tentar baixar de '{api_url}': {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _compile_file(source_path: Path, output_dir: Path):
    if not source_path.exists():
        typer.secho(f"AVISO: Arquivo de origem '{source_path}' não encontrado. Pulando.", fg=typer.colors.YELLOW)
        return

    relative_path = source_path.name if source_path.name == "main.py" else source_path
    output_path = (output_dir / relative_path).with_suffix(".mpy") if relative_path != "main.py" else (output_dir / "code").with_suffix(".mpy")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = ["mpy-cross", "-o", str(output_path), str(source_path)]
    run_shell_command(command, f"Compilando {source_path}")


def run(
    download_lib: Annotated[bool, typer.Option(
        "--download-lib", "-dl", 
        help="Força o download da biblioteca 'robot_kit'"
    )] = False):
    """Gera o projeto pronto para deploy no RP2040."""

    typer.secho("Iniciando processo de build do projeto...", bold=True, fg=typer.colors.CYAN)

    files_to_compile = []

    if not shutil.which("mpy-cross"):
        typer.secho("ERRO: 'mpy-cross' não encontrado.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not os.path.exists(PROJECT_CONFIG_FILE):
        typer.secho(f"ERRO: Arquivo '{PROJECT_CONFIG_FILE}' não encontrado.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if MAIN_FILE.exists():
        files_to_compile.append(MAIN_FILE)
    else:
        typer.secho(f"ERRO: Arquivo '{MAIN_FILE}' não encontrado.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not BUILD_DIR.exists():
        BUILD_DIR.mkdir()

    with open(PROJECT_CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)

    requirements = config.get("requirements", {})

    # Baixar robot-kit se necessário
    if requirements.get("robotkit"):

        if not (BUILD_DIR / 'robotkit').exists() or download_lib:
            typer.echo("\nDependência 'robotkit' encontrada, baixando online.")
            if ROBOT_KIT_DOWNLOAD_DIR.exists():
                shutil.rmtree(ROBOT_KIT_DOWNLOAD_DIR)

            parsed_url = _parse_github_url(ROBOT_KIT_GITHUB_URL)
            if not parsed_url:
                typer.secho(f"ERRO: URL do GitHub inválida: {ROBOT_KIT_GITHUB_URL}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

            owner, repo = parsed_url
            _download_github_dir(owner, repo, ROBOT_KIT_REPO_PATH, ROBOT_KIT_DOWNLOAD_DIR)

            kit_files = list(ROBOT_KIT_DOWNLOAD_DIR.rglob("*.py"))

            if Path('robotkit/main.py')in kit_files:
                shutil.copy(ROBOT_KIT_DOWNLOAD_DIR / "main.py", BUILD_DIR / "main.py")
                kit_files.remove(Path('robotkit/main.py'))

            files_to_compile.extend(kit_files)
            typer.secho(f"   FINISH! 'robot-kit' baixado com sucesso.", fg=typer.colors.GREEN)

    # 4. Bibliotecas externas
    other_libs = requirements.get("others", [])
    if other_libs:
        typer.echo("\nDependências 'others' encontradas.")
        for lib_file in other_libs:
            file_path = LIBS_DIR / lib_file
            if file_path.exists():
                files_to_compile.append(file_path)
            else:
                typer.secho(f"AVISO: Biblioteca '{lib_file}' não encontrada em '{LIBS_DIR}'.", fg=typer.colors.YELLOW)

    # 5. Compilação

    typer.echo("\nIniciando compilação dos arquivos...")
    for file in files_to_compile:
        _compile_file(file, BUILD_DIR)


    # 6. Limpeza
    if ROBOT_KIT_DOWNLOAD_DIR.exists():
        shutil.rmtree(ROBOT_KIT_DOWNLOAD_DIR)

    typer.secho("\nProcesso de build concluído com sucesso!", bold=True, fg=typer.colors.BRIGHT_GREEN)


if __name__ == "__main__":
    run()
