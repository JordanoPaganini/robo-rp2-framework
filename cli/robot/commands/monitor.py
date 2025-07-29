import typer
import serial
import time
from typing_extensions import Annotated
import os

# # Importa as funções da pasta 'core'
from robot.core import utils

def _showInfo(target_port: str):
    typer.secho(f"Monitor serial - RP2040 ({target_port})...", fg=typer.colors.CYAN)
    typer.secho(f"Pressione Ctrl+C para sair.\n", fg=typer.colors.BRIGHT_BLUE)

def run(
    com_port: Annotated[str, typer.Option(
        "--com",
        help="Especifica a porta COM do RP2040 (ex: COM3 ou /dev/ttyACM0)."
    )] = None,
    baudrate: Annotated[int, typer.Option(
        "--baudrate",
        help="Taxa de transmissão serial (baudrate). Padrão: 115200."
    )] = 115200,
):
    """
    Abre o monitor serial do RP2040 para visualizar saídas em tempo real.
    """
    os.system('cls')

    # Detecta automaticamente a porta COM, se necessário
    target_port = com_port or utils.find_rp2040_port()
    if not target_port:
        typer.secho("ERRO: Nenhum dispositivo RP2040 encontrado.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    _showInfo(target_port)

    try:
        while True:
            try:
                with serial.Serial(target_port, baudrate=baudrate, timeout=1) as ser:
                    while True:
                        line = ser.readline()
                        if not line:
                            continue
                        decoded = line.decode(errors="ignore").strip()
                        
                        if decoded.startswith("#") and ":" in decoded:
                            _, code = decoded.split(":")
                            if code.strip() == "100":
                                # Dispositivo resetado pelo botão: reconecta silenciosamente
                                os.system('cls')
                                _showInfo(target_port)
                                break
                        else:
                            print(decoded)

            except serial.SerialException:
                # Aguarda o dispositivo reconectar (por exemplo, após reset)
                time.sleep(1)
                continue

    except KeyboardInterrupt:
        typer.secho("\nMonitor serial encerrado pelo usuário.", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    run()
