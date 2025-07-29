# cli/robot/core/utils.py
import serial.tools.list_ports
import subprocess
import typer

def find_rp2040_port() -> str | None:
    """
    Tenta encontrar a porta serial de um dispositivo RP2040 conectado.
    """
    ports = serial.tools.list_ports.comports()
    # Palavras-chave comuns em descrições de portas de RP2040
    rp2040_keywords = ["rp2040", "raspberry pi pico", "circuitpython", "micropython"]

    # Busca primária por palavras-chave específicas
    for port in ports:
        if port.description and any(keyword in port.description.lower() for keyword in rp2040_keywords):
            return port.device

    # Busca secundária por descrições genéricas de USB Serial
    generic_matches = [
        port.device
        for port in ports
        if port.description and "usb" in port.description.lower() and "serial" in port.description.lower()
    ]
    
    ports = serial.tools.list_ports.comports()
    rp2040_keywords = ["rp2040", "raspberry", "pico"]

    # Primeiro tenta achar por descrição conhecida
    for port in ports:
        if any(keyword in port.description.lower() for keyword in rp2040_keywords):
            return port.device

    # Depois tenta identificar por descrição genérica
    generic_matches = [
        port.device
        for port in ports
        if "serial" in port.description.lower() and "usb" in port.description.lower()
    ]

    if len(generic_matches) == 1:
        return generic_matches[0]
    elif len(generic_matches) > 1:
        print("⚠️ Múltiplos dispositivos genéricos encontrados. Especifique com --com.")
        return None
    else:
        return None
    
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

