import requests
from bs4 import BeautifulSoup
import shutil
import time
import os
import psutil
from tqdm import tqdm
import platform

def find_and_select_rp2040_drive():
    """
    Verifica as unidades de armazenamento conectadas e permite ao usuário
    selecionar a que corresponde ao RP2040 em modo BOOTSEL.
    Retorna o caminho de montagem da unidade selecionada ou None.
    """
    possible_drives = []
    
    # psutil.disk_partitions() lista todas as partições montadas.
    partitions = psutil.disk_partitions()
    for p in partitions:
        # Tenta identificar unidades removíveis de forma genérica.
        # A unidade RPI-RP2 geralmente é FAT/VFAT e pequena.
        is_removable = 'removable' in p.opts or (platform.system() == 'Windows' and 'fixed' not in p.opts)
        is_fat = 'fat' in p.fstype.lower()

        if is_removable and is_fat:
             try:
                 usage = psutil.disk_usage(p.mountpoint)
                 # A unidade do RP2040 tem cerca de 128MB. Filtramos por um tamanho
                 # um pouco maior para garantir a detecção.
                 if usage.total < 256 * 1024 * 1024:
                    possible_drives.append(p)
             except (PermissionError, FileNotFoundError):
                 # Algumas unidades podem gerar erro ao acessar, então as ignoramos.
                 continue

    if not possible_drives:
        return None

    # Se apenas uma unidade candidata for encontrada, pede confirmação.
    if len(possible_drives) == 1:
        drive = possible_drives[0]
        usage = psutil.disk_usage(drive.mountpoint)
        size_mb = usage.total / (1024 * 1024)
        print(f"\nDispositivo encontrado: {drive.mountpoint} ({size_mb:.0f}MB)")
        try:
            confirm = input("-> Este é o seu RP2040 (RPI-RP2)? (s/n): ").lower().strip()
            if confirm == 's':
                return drive.mountpoint
        except KeyboardInterrupt:
            print("\nOperação cancelada.")
            return "exit"
        return None

    # Se múltiplas unidades forem encontradas, pede para o usuário escolher.
    print("\n[AVISO] Múltiplos dispositivos encontrados. Por favor, selecione o seu RP2040:")
    for i, p in enumerate(possible_drives):
        usage = psutil.disk_usage(p.mountpoint)
        size_mb = usage.total / (1024 * 1024)
        print(f"  [{i+1}] {p.mountpoint} ({p.device}) - Tamanho: {size_mb:.0f} MB")

    while True:
        try:
            choice_str = input(f"-> Digite o número (1-{len(possible_drives)}) ou 'c' para cancelar: ").strip().lower()
            if choice_str == 'c':
                 return "exit"
            choice = int(choice_str)
            if 1 <= choice <= len(possible_drives):
                return possible_drives[choice - 1].mountpoint
            else:
                print("   Seleção inválida. Tente novamente.")
        except ValueError:
            print("   Entrada inválida. Por favor, digite um número.")
        except KeyboardInterrupt:
            print("\nOperação cancelada.")
            return "exit"


def download_file_with_progress(url, filename):
    """
    Faz o download de um arquivo a partir de uma URL, exibindo uma barra de progresso.
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 KB

        with tqdm(total=total_size, unit='iB', unit_scale=True, desc=f"Baixando {os.path.basename(filename)}") as progress_bar:
            with open(filename, 'wb') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)

        if total_size != 0 and progress_bar.n != total_size:
            print("\n[ERRO] O download pode ter sido interrompido.")
            return False
        
        print("Download concluído com sucesso.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n[ERRO] Falha no download: {e}")
        return False
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro ao salvar o arquivo: {e}")
        return False

def run():
    """
    Executa o processo completo de instalação do MicroPython no RP2040.
    """
    BASE_URL = "https://micropython.org"
    DOWNLOAD_PAGE_URL = f"{BASE_URL}/download/RPI_PICO/"
    firmware_url = None
    firmware_filename = None
    link_tag = None

    # 1. Encontrar a URL do firmware mais recente
    try:
        print("🔎 Procurando a última versão estável do MicroPython...")
        page = requests.get(DOWNLOAD_PAGE_URL, timeout=10)
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")

        # --- LÓGICA DE BUSCA ATUALIZADA ---
        # A nova página usa uma tag <span> com classes específicas para marcar a versão estável.
        stable_tag = soup.find('span', class_='is-success', string='stable')

        if stable_tag:
            # Navega da tag 'stable' até o link de download correspondente.
            firmware_div = stable_tag.find_parent('div', class_='firmware')
            if firmware_div:
                link_tag = firmware_div.find('a', href=lambda href: href and href.endswith('.uf2'))
        
        if not link_tag:
            # Fallback: se a lógica acima falhar, tenta pegar o primeiro link que não seja "preview".
            all_links = soup.find_all('a', href=lambda href: href and href.endswith('.uf2'))
            for link in all_links:
                if 'preview' not in link['href'].lower():
                    link_tag = link
                    break # Pega o primeiro que encontrar
        
        if not link_tag:
            print("[ERRO] Não foi possível encontrar o link de download do firmware na página.")
            return

        firmware_url = BASE_URL + link_tag['href']
        firmware_filename = os.path.basename(link_tag['href'])
        print(f"✔️ Versão encontrada: {firmware_filename}")

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao acessar a página de downloads: {e}")
        return
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao analisar a página: {e}")
        return

    # 2. Baixar o arquivo de firmware
    if not download_file_with_progress(firmware_url, firmware_filename):
        if os.path.exists(firmware_filename):
            os.remove(firmware_filename) # Limpa arquivo incompleto
        return

    # 3. Instruir o usuário e aguardar o dispositivo
    print("\n--- 🚨 AÇÃO NECESSÁRIA 🚨 ---")
    print("1. Desconecte seu RP2040 do computador.")
    print("2. Pressione e SEGURE o botão 'BOOTSEL'.")
    print("3. Com o botão pressionado, conecte o RP2040 ao computador.")
    print("4. Solte o botão 'BOOTSEL' assim que a conexão for feita.")
    print("O dispositivo deve aparecer como um pen drive chamado 'RPI-RP2'.")
    print("\n⏳ Aguardando o dispositivo em modo BOOTSEL...")

    target_path = None
    while not target_path:
        target_path = find_and_select_rp2040_drive()
        if target_path == "exit":
            if os.path.exists(firmware_filename):
                os.remove(firmware_filename)
            return
        if not target_path:
            time.sleep(1)
            print(".", end="", flush=True)

    print(f"\n✔️ Dispositivo selecionado: {target_path}")

    # 4. Copiar o firmware para o dispositivo
    try:
        print(f"⚙️ Copiando '{firmware_filename}' para o dispositivo...")
        destination_file = os.path.join(target_path, firmware_filename)
        shutil.copy(firmware_filename, destination_file)
        print("✨ Firmware copiado com sucesso!")
        print("Aguardando o dispositivo reiniciar...")
        
        # A cópia faz o dispositivo ejetar e reiniciar automaticamente.
        # Esperamos a unidade desaparecer para confirmar.
        time.sleep(2) # Dá um tempo para o processo de ejeção iniciar
        while os.path.exists(target_path):
            time.sleep(0.5)

    except Exception as e:
        print(f"\n[ERRO] Falha ao copiar o arquivo para o dispositivo: {e}")
        print("Por favor, verifique se o dispositivo está conectado corretamente e tente novamente.")
    finally:
        # 5. Limpar o arquivo baixado
        if os.path.exists(firmware_filename):
            os.remove(firmware_filename)
    
    print("\n🎉 Instalação concluída! Seu RP2040 está pronto com o MicroPython.")


if __name__ == '__main__':
    # Exemplo de como chamar a função.
    # Para usar na sua CLI, basta chamar run() a partir do comando do Typer.
    run()
