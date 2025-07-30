# cli/robot/commands/deploy.py
import typer
import shutil
from pathlib import Path
from typing_extensions import Annotated
import serial
import time
import textwrap

# Importa as funções da pasta 'core' e o comando 'build'
from robot.core import utils
from robot.commands import build, monitor

BUILD_DIR = Path("build")


def _clear_flash(port: str, baudrate: int) -> bool:
    """
    Envia um script via REPL para apagar todos os arquivos e pastas do RP2040.
    """
    cleanup_script = textwrap.dedent("""
        import os
        def delete_all(path="."):
            for name in os.listdir(path):
                full_path = path + "/" + name
                try:
                    if os.stat(full_path)[0] & 0x4000:
                        delete_all(full_path)
                        os.rmdir(full_path)
                    else:
                        os.remove(full_path)
                except Exception as e:
                    print("Erro:", full_path, e)
        delete_all()
        print("LIMPEZA_CONCLUIDA")
    """).strip()

    try:
        with serial.Serial(port, baudrate=baudrate, timeout=1) as ser:
            # Aguarda REPL
            time.sleep(2)
            ser.write(b"\r\x03")  # CTRL-C para interromper execução atual
            time.sleep(0.5)
            ser.write(b"\x05")    # CTRL-E para entrar no modo paste
            time.sleep(0.2)
            
            for line in cleanup_script.splitlines():
                ser.write(line.encode('utf-8') + b'\r\n')
                time.sleep(0.05)
            
            ser.write(b"\x0d")  # Enter para finalizar o modo paste e executar
            ser.write(b"\x04")  # CTRL-D para dar um soft-rebot
            time.sleep(1)

            # Lê a resposta
            output = b""
            while ser.in_waiting:
                output += ser.read(ser.in_waiting)
                time.sleep(0.25)

            if b"LIMPEZA_CONCLUIDA" in output:
                return True
            else:
                #print(output.decode(errors="ignore")) # For debug
                return False
    except Exception as e:
        #print(e) # For debug
        return False

def run(
    com_port: Annotated[str, typer.Option(
        "--com", 
        help="Especifica a porta COM do RP2040 (ex: COM3 ou /dev/ttyACM0).",
    )] = "",
    baudrate: Annotated[int, typer.Option(
        "--baudrate",
        help="Taxa de transmissão serial (baudrate). Padrão: 115200."
    )] = 115200,
    clear_rp: Annotated[bool, typer.Option(
        "--clear",
        help="Limpa todos os arquivos do RP2040 antes de fazer o deploy",
    )] = False,
    build_before: Annotated[bool, typer.Option(
        "-b", "--build", 
        help="Executa o comando 'build' antes de fazer o deploy."
    )] = False,
    monitor_after: Annotated[bool, typer.Option(
        "-m", 
        "--monitor", 
        help="Abre o monitor do RP2040 após finalizar o deploy."
    )] = False
):
    """
    Faz o deploy dos arquivos compilados da pasta 'build' para o RP2040.
    """
    typer.secho("Iniciando processo de deploy...", bold=True, fg=typer.colors.CYAN)

    # 1. Executa o build se a flag -b/--build for passada
    if build_before:
        typer.echo("\nOpção --build detectada. Executando o build...")
        try:
            build.run()
            typer.secho("Build concluído. Continuando com o deploy...", fg=typer.colors.CYAN)
        except typer.Exit:
            typer.secho("O processo de build falhou. Deploy abortado.", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    # 2. Verifica se a ferramenta mpremote está instalada
    if not shutil.which("mpremote"):
        typer.secho("ERRO: 'mpremote' não foi encontrado no seu sistema.", fg=typer.colors.RED)
        typer.echo("Instale com: pip install mpremote")
        raise typer.Exit(code=1)

    # 3. Verifica se a pasta 'build' existe
    if not BUILD_DIR.exists() or not any(BUILD_DIR.iterdir()):
        typer.secho(f"ERRO: A pasta '{BUILD_DIR}' está vazia ou não existe.", fg=typer.colors.RED)
        typer.echo("Execute o comando 'build' primeiro ou use a opção -b / --build.")
        raise typer.Exit(code=1)

    # 4. Determina a porta COM
    target_port = com_port
    if not target_port:
        target_port = utils.find_rp2040_port()
        if target_port:
            typer.secho(f"\nDispositivo encontrado em: {target_port}", fg=typer.colors.BRIGHT_BLACK)
        else:
            typer.secho("ERRO: Nenhum dispositivo RP2040 encontrado.", fg=typer.colors.RED)
            typer.echo("Verifique a conexão ou especifique a porta com a opção --com.")
            raise typer.Exit(code=1)
    else:
        typer.secho(f"\nUsando porta especificada: {target_port}", fg=typer.colors.BRIGHT_BLACK)

    if clear_rp:
        typer.echo("\nOpção --clear detectada. Limpando o RP2040...")
        try:
            if not _clear_flash(target_port, baudrate): raise typer.Exit()
            typer.secho("Arquivos limpos. Continuando o deploy...", fg=typer.colors.CYAN)
        except typer.Exit:
            typer.secho("O processo de clear falhou. Deploy abortado.", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    # 5. Copia os arquivos para o dispositivo usando mpremote
    typer.echo(f"\nIniciando a cópia dos arquivos de '{BUILD_DIR}' para o dispositivo...")
    copy_command = ["mpremote", "connect", target_port, "cp", "-r", f"{BUILD_DIR}/.", ":"]
    utils.run_shell_command(copy_command, "Copiando arquivos")

    # 6. Faz um soft-reset para que o novo código seja executado
    reset_command = ["mpremote", "connect", target_port, "reset"]
    utils.run_shell_command(reset_command, "Reiniciando o dispositivo")

    typer.secho("\nDeploy concluído com sucesso!", bold=True, fg=typer.colors.BRIGHT_GREEN)

    if monitor_after:
        monitor.run(target_port)

if __name__ == "__main__":
    run()
