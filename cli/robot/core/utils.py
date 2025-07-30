# cli/robot/core/utils.py
import serial.tools.list_ports
import subprocess
import typer

RP2040_VID = 0x2E8A
RP2040_PID = 0x0005

def find_rp2040_port():
    """
    Varre as portas seriais disponíveis e retorna a porta correspondente a um RP2040.
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == RP2040_VID and port.pid == RP2040_PID:
            return port.device
    return None

def run_shell_command(command: list[str], description: str):
    """
    Executa um comando no shell, mostrando uma descrição e tratando erros.
    """
    typer.echo(f"-> {description}...")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        typer.secho("   OK!", fg=typer.colors.GREEN)
        return result.stdout
    except subprocess.CalledProcessError as e:
        typer.secho(f"ERRO ao executar '{' '.join(command)}':", fg=typer.colors.RED)
        typer.secho(e.stderr, fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

