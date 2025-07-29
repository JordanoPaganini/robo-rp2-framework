# cli/cli.py
import os
import importlib.util
import typer
from pathlib import Path
import logging

# Configurando o logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Inciando o app do Typer
app = typer.Typer(add_completion=False, help=True)

# Caminho para a pasta de comandos
_PROJECT_DIR = Path(__file__).parent
commands_path = os.path.join(_PROJECT_DIR, "commands")

def load_commands():
    """Carrega automaticamente todos os comandos da pasta /commands"""
    for file in os.listdir(commands_path):
        try:
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]  # Remove a extensão .py
                file_path = os.path.join(commands_path, file)

                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    if hasattr(module, "run"):
                        app.command(name=module_name)(module.run)
                    else:
                        raise AttributeError(f"O módulo {module_name} não possui a função 'run()'.")

                except Exception as e:
                    logger.error(f"Erro ao carregar o comando '{module_name}': {e}")

        except:
            print()

# Carrega e registra os comandos
load_commands()

if __name__ == "__main__":
    app()