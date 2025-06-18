import subprocess
import sys
import os
from pathlib import Path
import requests
from tqdm import tqdm
import re
import hashlib
import json
from typing import Set, List, Dict, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from colorama import init, Fore, Back, Style
import logging
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError

# Inicializa o colorama
init(autoreset=True)

def get_script_dir():
    """Obtém o diretório do script, funcionando tanto para .py quanto para .exe"""
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    else:
        return Path(os.path.dirname(os.path.abspath(__file__)))

def get_version(package_name: str) -> str:
    """Obtém a versão de um pacote usando importlib.metadata."""
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None

# Configuração do sistema de log
def setup_logger():
    """Configura o sistema de log."""
    script_dir = get_script_dir()
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo de log com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"hermes_installer_{timestamp}.log"
    
    # Configuração do logger
    logger = logging.getLogger("HermesInstaller")
    logger.setLevel(logging.DEBUG)
    
    # Handler para arquivo (nível DEBUG - todos os logs)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para console (apenas erros críticos)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    
    # Formato do log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adiciona os handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Inicializa o logger
logger = setup_logger()

def print_success(text: str):
    """Imprime texto em verde e registra no log."""
    print(f"{Fore.GREEN}{text}")
    logger.debug(text)  # Mudado para debug

def print_error(text: str):
    """Imprime texto em vermelho e registra no log."""
    print(f"{Fore.RED}{text}")
    logger.error(text)

def print_warning(text: str):
    """Imprime texto em amarelo e registra no log."""
    print(f"{Fore.YELLOW}{text}")
    logger.debug(text)  # Mudado para debug

def print_info(text: str):
    """Imprime texto em azul e registra no log."""
    print(f"{Fore.BLUE}{text}")
    logger.debug(text)  # Mudado para debug

def print_highlight(text: str):
    """Imprime texto em magenta e registra no log."""
    print(f"{Fore.MAGENTA}{text}")
    logger.debug(text)  # Mudado para debug

def log_exception(e: Exception, context: str = ""):
    """Registra uma exceção no log com contexto."""
    error_msg = f"{context}: {str(e)}" if context else str(e)
    logger.exception(error_msg)
    print_error(error_msg)

def exibir_logo():
    """Exibe o logo do Hermes Installer."""
    logo = f"""
{Fore.CYAN}
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║  {Fore.YELLOW}██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗{Fore.CYAN}  ║
║  {Fore.YELLOW}██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝{Fore.CYAN}  ║
║  {Fore.YELLOW}███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗{Fore.CYAN}  ║
║  {Fore.YELLOW}██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║{Fore.CYAN}  ║
║  {Fore.YELLOW}██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║{Fore.CYAN}  ║
║  {Fore.YELLOW}╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝{Fore.CYAN}  ║
║                                                       ║
║  {Fore.GREEN}Instalador de Dependências Python{Fore.CYAN}                    ║
║  {Fore.GREEN}Versão 1.0.30035{Fore.CYAN}                                     ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""
    print(logo)

def escolher_tipo_instalacao():
    """Permite ao usuário escolher o tipo de instalação."""
    print(f"\n{Fore.CYAN}=== Escolha o tipo de instalação ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. {Fore.WHITE}Instalar pacotes do projeto (requirements.txt)")
    print(f"{Fore.YELLOW}2. {Fore.WHITE}Instalar pacotes do ambiente de desenvolvimento")
    print(f"{Fore.YELLOW}3. {Fore.WHITE}Instalar todos os pacotes do sistema")
    print(f"{Fore.YELLOW}4. {Fore.WHITE}Sair")
    
    while True:
        try:
            escolha = input(f"\n{Fore.CYAN}Escolha uma opção (1-4): {Style.RESET_ALL}").strip()
            if escolha in ['1', '2', '3', '4']:
                return escolha
            else:
                print_error("Opção inválida! Escolha 1, 2, 3 ou 4.")
        except KeyboardInterrupt:
            print_info("\nOperação cancelada pelo usuário.")
            sys.exit(0)

def verificar_pasta_requirements():
    """Verifica se a pasta requirements existe e retorna informações sobre ela."""
    script_dir = get_script_dir()
    pasta_requirements = script_dir / "requirements"
    
    if not pasta_requirements.exists():
        return False, None, []
    
    # Conta os arquivos na pasta
    arquivos = list(pasta_requirements.glob("*.whl")) + list(pasta_requirements.glob("*.tar.gz"))
    return True, pasta_requirements, arquivos

def escolher_acao_pasta_existente(pasta_requirements: Path, arquivos: List[Path]):
    """Permite ao usuário escolher o que fazer com a pasta requirements existente."""
    print(f"\n{Fore.CYAN}=== Pasta requirements encontrada ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}Pasta: {pasta_requirements}")
    print(f"{Fore.GREEN}Arquivos encontrados: {len(arquivos)}")
    
    if arquivos:
        print(f"\n{Fore.YELLOW}Arquivos na pasta:")
        for i, arquivo in enumerate(arquivos[:10], 1):  # Mostra apenas os primeiros 10
            print(f"  {i}. {arquivo.name}")
        if len(arquivos) > 10:
            print(f"  ... e mais {len(arquivos) - 10} arquivos")
    
    print(f"\n{Fore.CYAN}Escolha uma opção:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. {Fore.WHITE}Instalar pacotes existentes na pasta")
    print(f"{Fore.YELLOW}2. {Fore.WHITE}Atualizar pacotes existentes")
    print(f"{Fore.YELLOW}3. {Fore.WHITE}Baixar novos pacotes do requirements.txt")
    print(f"{Fore.YELLOW}4. {Fore.WHITE}Limpar pasta e baixar tudo novamente")
    print(f"{Fore.YELLOW}5. {Fore.WHITE}Voltar ao menu principal")
    
    while True:
        try:
            escolha = input(f"\n{Fore.CYAN}Escolha uma opção (1-5): {Style.RESET_ALL}").strip()
            if escolha in ['1', '2', '3', '4', '5']:
                return escolha
            else:
                print_error("Opção inválida! Escolha 1, 2, 3, 4 ou 5.")
        except KeyboardInterrupt:
            print_info("\nOperação cancelada pelo usuário.")
            sys.exit(0)

def obter_pacotes_ambiente_desenvolvimento():
    """Obtém os pacotes instalados no ambiente de desenvolvimento."""
    try:
        # Lista todos os pacotes instalados
        result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"], 
                              capture_output=True, text=True, check=True)
        
        pacotes = []
        for linha in result.stdout.strip().split('\n'):
            if linha and '==' in linha:
                # Remove caracteres especiais e normaliza
                linha = linha.strip()
                if not linha.startswith('#') and '==' in linha:
                    pacotes.append(linha)
        
        return pacotes
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao obter pacotes do ambiente: {e}")
        return []

def obter_pacotes_sistema():
    """Obtém todos os pacotes Python instalados no sistema."""
    try:
        # Lista todos os pacotes instalados globalmente
        result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"], 
                              capture_output=True, text=True, check=True)
        
        pacotes = []
        for linha in result.stdout.strip().split('\n'):
            if linha and '==' in linha:
                # Remove caracteres especiais e normaliza
                linha = linha.strip()
                if not linha.startswith('#') and '==' in linha:
                    pacotes.append(linha)
        
        return pacotes
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao obter pacotes do sistema: {e}")
        return []

def processar_pacotes_para_download(pacotes: List[str]) -> List[str]:
    """Processa e filtra pacotes para download, removendo pacotes padrão do Python."""
    pacotes_padrao = {
        'pip', 'setuptools', 'wheel', 'distlib', 'filelock', 'platformdirs',
        'packaging', 'pyparsing', 'six', 'markupsafe', 'jinja2', 'click',
        'colorama', 'urllib3', 'certifi', 'charset-normalizer', 'idna',
        'requests', 'tqdm'
    }
    
    pacotes_filtrados = []
    for pacote in pacotes:
        nome_pacote = pacote.split('==')[0].lower()
        if nome_pacote not in pacotes_padrao:
            pacotes_filtrados.append(pacote)
    
    return pacotes_filtrados

def instalar_pacotes_existentes(pasta_requirements: Path, pip_path: str):
    """Instala os pacotes que já estão na pasta requirements."""
    arquivos = list(pasta_requirements.glob("*.whl")) + list(pasta_requirements.glob("*.tar.gz"))
    
    if not arquivos:
        print_warning("Nenhum pacote encontrado na pasta requirements!")
        return False
    
    print_highlight(f"\nInstalando {len(arquivos)} pacotes existentes...")
    
    for arquivo in arquivos:
        try:
            nome_arquivo = arquivo.name
            print_info(f"Instalando {nome_arquivo}...")
            
            # Instala o arquivo diretamente
            subprocess.run([pip_path, "install", str(arquivo)], check=True)
            print_success(f"Pacote {nome_arquivo} instalado com sucesso!")
            
        except subprocess.CalledProcessError as e:
            print_error(f"Erro ao instalar {arquivo.name}: {e}")
            return False
    
    print_success("Todos os pacotes existentes foram instalados com sucesso!")
    return True

def atualizar_pacotes_existentes(pasta_requirements: Path):
    """Atualiza os pacotes existentes na pasta requirements."""
    arquivos = list(pasta_requirements.glob("*.whl")) + list(pasta_requirements.glob("*.tar.gz"))
    
    if not arquivos:
        print_warning("Nenhum pacote encontrado na pasta requirements!")
        return False
    
    print_highlight(f"\nAtualizando {len(arquivos)} pacotes existentes...")
    
    for arquivo in arquivos:
        try:
            # Extrai nome e versão do arquivo
            nome_arquivo = arquivo.stem
            if '-' in nome_arquivo:
                nome_pacote = nome_arquivo.rsplit('-', 1)[0]
                versao_atual = nome_arquivo.rsplit('-', 1)[1]
                
                print_info(f"Verificando atualizações para {nome_pacote}...")
                
                # Tenta baixar a versão mais recente
                if baixar_pacote(f"{nome_pacote}>=0", pasta_requirements):
                    # Remove o arquivo antigo
                    arquivo.unlink()
                    print_success(f"Pacote {nome_pacote} atualizado!")
                else:
                    print_warning(f"Não foi possível atualizar {nome_pacote}")
                    
        except Exception as e:
            print_error(f"Erro ao atualizar {arquivo.name}: {e}")
    
    print_success("Atualização de pacotes concluída!")
    return True

def limpar_pasta_requirements(pasta_requirements: Path):
    """Remove todos os arquivos da pasta requirements."""
    arquivos = list(pasta_requirements.glob("*.whl")) + list(pasta_requirements.glob("*.tar.gz"))
    
    if not arquivos:
        print_info("Pasta requirements já está vazia.")
        return True
    
    print_warning(f"Removendo {len(arquivos)} arquivos da pasta requirements...")
    
    for arquivo in arquivos:
        try:
            arquivo.unlink()
            print_info(f"Removido: {arquivo.name}")
        except Exception as e:
            print_error(f"Erro ao remover {arquivo.name}: {e}")
    
    print_success("Pasta requirements limpa com sucesso!")
    return True

def confirmar_inicio():
    """Pergunta ao usuário se deseja continuar com a instalação."""
    print(f"\n{Fore.YELLOW}Deseja iniciar o processo de instalação? (S/N)")
    resposta = input().strip().upper()
    return resposta == 'S'

def criar_sessao_requests():
    """Cria uma sessão do requests com retry automático."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def extrair_nome_versao(requisito: str) -> Tuple[str, str]:
    """Extrai nome e versão de um requisito."""
    # Remove extras e marcadores de ambiente
    requisito = requisito.split(';')[0].split('[')[0].strip()
    
    # Remove espaços extras e parênteses
    requisito = re.sub(r'\s+', ' ', requisito).strip()
    requisito = requisito.replace('(', '').replace(')', '')
    
    # Padrões comuns de versão
    padroes = [
        r'^([^=<>~!]+)==([^=<>~!]+)$',  # ==
        r'^([^=<>~!]+)>=([^=<>~!]+)$',  # >=
        r'^([^=<>~!]+)<=([^=<>~!]+)$',  # <=
        r'^([^=<>~!]+)>([^=<>~!]+)$',   # >
        r'^([^=<>~!]+)<([^=<>~!]+)$',   # <
        r'^([^=<>~!]+)~=([^=<>~!]+)$',  # ~=
        r'^([^=<>~!]+)!=([^=<>~!]+)$',  # !=
        r'^([^=<>~!]+)\s+([^=<>~!]+)$', # espaço
    ]
    
    for padrao in padroes:
        match = re.match(padrao, requisito)
        if match:
            nome = match.group(1).strip()
            versao = match.group(2).strip()
            
            # Remove caracteres inválidos da versão
            versao = re.sub(r'[^\d\.]', '', versao)
            
            # Se a versão estiver vazia após a limpeza, retorna None
            if not versao:
                return nome, None
                
            return nome, versao
    
    # Se não encontrar padrão de versão, retorna o nome e None
    return requisito.strip(), None

def obter_dependencias_pypi(nome_pacote: str, versao: str) -> List[str]:
    """Obtém as dependências de um pacote do PyPI."""
    try:
        # Limpa o nome do pacote e versão
        nome_pacote = nome_pacote.strip().lower()
        versao = versao.strip()
        
        # Se a versão for inválida, retorna lista vazia
        if not versao or not re.match(r'^\d+(\.\d+)*$', versao):
            print_warning(f"Versão inválida para {nome_pacote}: {versao}")
            return []
            
        session = criar_sessao_requests()
        url = f"https://pypi.org/pypi/{nome_pacote}/{versao}/json"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        dependencias = []
        if 'info' in data and 'requires_dist' in data['info'] and data['info']['requires_dist']:
            for req in data['info']['requires_dist']:
                # Remove especificações de versão extras e marcadores de ambiente
                req = req.split(';')[0].split('[')[0].strip()
                if req and not req.startswith('python'):
                    dependencias.append(req)
        
        return dependencias
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao obter dependências de {nome_pacote}: {e}")
        return []
    except Exception as e:
        print_error(f"Erro inesperado ao obter dependências de {nome_pacote}: {e}")
        return []

def processar_dependencias_recursivamente(pacotes_iniciais: List[str]) -> Set[str]:
    """Processa dependências recursivamente."""
    pacotes_processados = set()
    pacotes_para_processar = pacotes_iniciais.copy()
    
    while pacotes_para_processar:
        pacote = pacotes_para_processar.pop(0)
        if pacote in pacotes_processados:
            continue
        
        pacotes_processados.add(pacote)
        nome_pacote, versao = extrair_nome_versao(pacote)
        
        if versao:
            try:
                dependencias = obter_dependencias_pypi(nome_pacote, versao)
                for dep in dependencias:
                    if dep not in pacotes_processados:
                        pacotes_para_processar.append(dep)
            except Exception as e:
                print_error(f"Erro ao processar dependências de {pacote}: {e}")
                continue
    
    return pacotes_processados

def ler_requirements():
    """Lê os pacotes do arquivo requirements.txt"""
    script_dir = get_script_dir()
    requirements_file = script_dir / "requirements.txt"
    
    if not requirements_file.exists():
        raise FileNotFoundError("Arquivo requirements.txt não encontrado!")
    
    with open(requirements_file, 'r') as f:
        # Remove linhas vazias e comentários
        pacotes = [linha.strip() for linha in f.readlines() 
                  if linha.strip() and not linha.strip().startswith('#')]
    
    return pacotes

def verificar_pacotes_requirements(pasta_requirements, pacotes):
    """Verifica se todos os pacotes do requirements.txt estão presentes e atualizados na pasta requirements"""
    pacotes_faltantes = []
    pacotes_desatualizados = []
    
    for pacote in pacotes:
        nome_pacote = pacote.split("==")[0] if "==" in pacote else pacote.split(">=")[0]
        versao = pacote.split("==")[1] if "==" in pacote else pacote.split(">=")[1]
        
        # Procura por arquivos que correspondam ao padrão do pacote
        arquivos_encontrados = list(pasta_requirements.glob(f"{nome_pacote}-{versao}*"))
        
        if not arquivos_encontrados:
            pacotes_faltantes.append(pacote)
            continue
            
        # Verifica se o arquivo está corrompido ou incompleto
        arquivo = arquivos_encontrados[0]
        try:
            # Tenta obter o hash do arquivo no PyPI
            url, _ = obter_url_pacote(nome_pacote, versao)
            response = requests.head(url)
            tamanho_esperado = int(response.headers.get('content-length', 0))
            
            # Verifica o tamanho do arquivo local
            tamanho_local = arquivo.stat().st_size
            
            if tamanho_local != tamanho_esperado:
                pacotes_desatualizados.append(pacote)
                arquivo.unlink()  # Remove o arquivo corrompido
        except Exception:
            pacotes_desatualizados.append(pacote)
            if arquivo.exists():
                arquivo.unlink()  # Remove o arquivo em caso de erro
    
    return pacotes_faltantes, pacotes_desatualizados

def criar_pasta_requirements() -> Path:
    """Cria a pasta requirements se não existir."""
    script_dir = get_script_dir()
    requirements_path = script_dir / "requirements"
    if not requirements_path.exists():
        print_info("Criando pasta requirements...")
        requirements_path.mkdir()
        print_success("Pasta requirements criada com sucesso!")
    return requirements_path

def obter_url_pacote(nome_pacote, versao):
    """Obtém a URL correta do pacote no PyPI."""
    # Primeiro tenta obter a URL do wheel
    url_wheel = f"https://files.pythonhosted.org/packages/py3/{nome_pacote[0]}/{nome_pacote}/{nome_pacote}-{versao}-py3-none-any.whl"
    
    # Se não encontrar o wheel, tenta o tar.gz
    url_tar = f"https://files.pythonhosted.org/packages/source/{nome_pacote[0]}/{nome_pacote}/{nome_pacote}-{versao}.tar.gz"
    
    # Tenta primeiro o wheel
    response = requests.head(url_wheel)
    if response.status_code == 200:
        return url_wheel, ".whl"
    
    # Se não encontrar o wheel, tenta o tar.gz
    response = requests.head(url_tar)
    if response.status_code == 200:
        return url_tar, ".tar.gz"
    
    # Se não encontrar nenhum dos dois, tenta buscar na página do pacote
    url_pypi = f"https://pypi.org/pypi/{nome_pacote}/{versao}/json"
    response = requests.get(url_pypi)
    if response.status_code == 200:
        data = response.json()
        if 'urls' in data:
            for url_info in data['urls']:
                if url_info['packagetype'] in ['wheel', 'sdist']:
                    return url_info['url'], os.path.splitext(url_info['filename'])[1]
    
    raise Exception(f"Não foi possível encontrar o pacote {nome_pacote} versão {versao}")

def baixar_pacote(pacote: str, pasta_destino: Path) -> bool:
    """Baixa um pacote do PyPI para a pasta requirements."""
    nome_pacote, versao = extrair_nome_versao(pacote)
    if not versao:
        print_warning(f"Pacote {pacote} não tem versão especificada, pulando...")
        return False
    
    try:
        # Obtém a URL correta do pacote
        url, extensao = obter_url_pacote(nome_pacote, versao)
        
        # Nome do arquivo de destino
        arquivo_destino = pasta_destino / f"{nome_pacote}-{versao}{extensao}"
        
        if arquivo_destino.exists():
            print_info(f"Pacote {nome_pacote} já existe em requirements/")
            return True
        
        print_info(f"Baixando {nome_pacote}...")
        session = criar_sessao_requests()
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Obtém o tamanho total do arquivo
        total_size = int(response.headers.get('content-length', 0))
        
        # Baixa o arquivo com barra de progresso
        with open(arquivo_destino, 'wb') as f, tqdm(
            desc=nome_pacote,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as barra:
            for data in response.iter_content(chunk_size=1024):
                tamanho = f.write(data)
                barra.update(tamanho)
        
        print_success(f"Pacote {nome_pacote} baixado com sucesso!")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao baixar {nome_pacote}: {e}")
        if arquivo_destino.exists():
            arquivo_destino.unlink()
        return False
    except Exception as e:
        print_error(f"Erro inesperado ao baixar {nome_pacote}: {e}")
        if arquivo_destino.exists():
            arquivo_destino.unlink()
        return False

def criar_ambiente_virtual():
    """Cria um ambiente virtual Python se não existir."""
    script_dir = get_script_dir()
    venv_path = script_dir / "venv"
    
    try:
        if not venv_path.exists():
            print_info("Criando ambiente virtual...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            
            # Aguarda um momento para garantir que os arquivos sejam criados
            time.sleep(2)
            
            # Verifica se os arquivos necessários foram criados
            if sys.platform == "win32":
                python_path = venv_path / "Scripts/python.exe"
                pip_path = venv_path / "Scripts/pip.exe"
            else:
                python_path = venv_path / "bin/python"
                pip_path = venv_path / "bin/pip"
            
            if not python_path.exists() or not pip_path.exists():
                raise FileNotFoundError("Arquivos do ambiente virtual não foram criados corretamente")
            
            print_success("Ambiente virtual criado com sucesso!")
            logger.debug("Ambiente virtual criado com sucesso")
            return True
        else:
            logger.debug("Ambiente virtual já existe")
            return True
            
    except subprocess.CalledProcessError as e:
        log_exception(e, "Erro ao criar ambiente virtual")
        return False
    except Exception as e:
        log_exception(e, "Erro inesperado ao criar ambiente virtual")
        return False

def ativar_ambiente_virtual():
    """Ativa o ambiente virtual."""
    script_dir = get_script_dir()
    venv_path = script_dir / "venv"
    
    if not venv_path.exists():
        raise FileNotFoundError("Ambiente virtual não encontrado!")
    
    if sys.platform == "win32":
        python_path = venv_path / "Scripts/python.exe"
        pip_path = venv_path / "Scripts/pip.exe"
    else:
        python_path = venv_path / "bin/python"
        pip_path = venv_path / "bin/pip"

    if not python_path.exists():
        raise FileNotFoundError(f"Python do ambiente virtual não encontrado em: {python_path}")
    if not pip_path.exists():
        raise FileNotFoundError(f"Pip do ambiente virtual não encontrado em: {pip_path}")

    logger.debug(f"Ambiente virtual encontrado em: {venv_path}")
    logger.debug(f"Python: {python_path}")
    logger.debug(f"Pip: {pip_path}")

    return str(python_path), str(pip_path)

def instalar_pacotes(pip_path: str, pasta_requirements: Path):
    """Instala os pacotes da pasta requirements."""
    pacotes = ler_requirements()
    print_highlight("\nInstalando pacotes...")
    
    for pacote in pacotes:
        nome_pacote, versao = extrair_nome_versao(pacote)
        if not versao:
            continue
            
        # Procura por arquivos que correspondam ao padrão do pacote
        arquivos_encontrados = list(pasta_requirements.glob(f"{nome_pacote}-{versao}*"))
        
        if arquivos_encontrados:
            arquivo = arquivos_encontrados[0]
            print_info(f"Instalando {nome_pacote}...")
            # Usa o caminho absoluto do arquivo
            caminho_arquivo = str(arquivo.absolute())
            subprocess.run([pip_path, "install", "--no-index", "--find-links", str(pasta_requirements.absolute()), pacote], check=True)
        else:
            print_warning(f"Arquivo não encontrado para {nome_pacote}, instalando da internet...")
            subprocess.run([pip_path, "install", pacote], check=True)
    
    print_success("Todos os pacotes foram instalados com sucesso!")

def verificar_estrutura_pastas():
    """Verifica e cria todas as pastas necessárias para o funcionamento do Hermes."""
    script_dir = get_script_dir()
    pastas_necessarias = {
        "logs": "Armazenamento de logs de execução",
        "requirements": "Armazenamento de pacotes Python",
        "venv": "Ambiente virtual Python"
    }
    
    print_info("\nVerificando estrutura de pastas...")
    logger.debug("Iniciando verificação de estrutura de pastas")
    
    for pasta, descricao in pastas_necessarias.items():
        pasta_path = script_dir / pasta
        try:
            if not pasta_path.exists():
                print_info(f"Criando pasta {pasta} ({descricao})...")
                pasta_path.mkdir(exist_ok=True)
                logger.debug(f"Pasta {pasta} criada em: {pasta_path}")
            else:
                logger.debug(f"Pasta {pasta} já existe em: {pasta_path}")
        except Exception as e:
            log_exception(e, f"Erro ao criar pasta {pasta}")
            return False
    
    # Verifica se o requirements.txt existe
    requirements_file = script_dir / "requirements.txt"
    if not requirements_file.exists():
        print_error("Arquivo requirements.txt não encontrado!")
        logger.error(f"Arquivo requirements.txt não encontrado em: {requirements_file}")
        return False
    
    logger.debug("Verificação de estrutura de pastas concluída com sucesso")
    return True

def mostrar_info_ambiente_virtual():
    """Mostra informações sobre como ativar o ambiente virtual."""
    print_highlight("\n=== Informações do Ambiente Virtual ===")
    print_info("Para ativar o ambiente virtual:")
    
    if sys.platform == "win32":
        print(f"{Fore.CYAN}venv\\Scripts\\activate")
        print(f"{Fore.CYAN}ou")
        print(f"{Fore.CYAN}venv\\Scripts\\activate.bat")
    else:
        print(f"{Fore.CYAN}source venv/bin/activate")
    
    print_info("\nPara desativar o ambiente virtual:")
    print(f"{Fore.CYAN}deactivate")
    
    print_info("\nPara verificar se está ativo:")
    print(f"{Fore.CYAN}python -c \"import sys; print(sys.prefix)\"")

def mostrar_resumo_operacao(tipo_operacao: str, pacotes_processados: int, sucesso: bool):
    """Mostra um resumo da operação realizada."""
    print_highlight(f"\n=== Resumo da Operação ===")
    print_info(f"Tipo de operação: {tipo_operacao}")
    print_info(f"Pacotes processados: {pacotes_processados}")
    
    if sucesso:
        print_success("Status: Concluído com sucesso!")
    else:
        print_error("Status: Concluído com erros!")
    
    if sucesso and tipo_operacao in ["Instalação", "Download e Instalação"]:
        mostrar_info_ambiente_virtual()

def main():
    try:
        # Exibe o logo
        exibir_logo()
        
        # Verifica a estrutura básica de pastas
        if not verificar_estrutura_pastas():
            print_error("Erro na verificação da estrutura de pastas. Verifique o log para mais detalhes.")
            sys.exit(1)
        
        # Loop principal do menu
        while True:
            # Escolha do tipo de instalação
            tipo_instalacao = escolher_tipo_instalacao()
            
            if tipo_instalacao == '4':  # Sair
                print_info("Saindo do Hermes Installer...")
                sys.exit(0)
            
            # Verifica se a pasta requirements existe
            pasta_existe, pasta_requirements, arquivos = verificar_pasta_requirements()
            
            if pasta_existe and arquivos:
                # Pasta existe e tem arquivos - oferece opções
                acao = escolher_acao_pasta_existente(pasta_requirements, arquivos)
                
                if acao == '1':  # Instalar pacotes existentes
                    if not criar_ambiente_virtual():
                        print_error("Falha ao criar ambiente virtual.")
                        continue
                    
                    try:
                        python_path, pip_path = ativar_ambiente_virtual()
                        if instalar_pacotes_existentes(pasta_requirements, pip_path):
                            mostrar_resumo_operacao("Instalação", len(arquivos), True)
                        else:
                            mostrar_resumo_operacao("Instalação", len(arquivos), False)
                    except Exception as e:
                        log_exception(e, "Erro ao instalar pacotes existentes")
                        mostrar_resumo_operacao("Instalação", 0, False)
                    continue
                
                elif acao == '2':  # Atualizar pacotes existentes
                    arquivos = list(pasta_requirements.glob("*.whl")) + list(pasta_requirements.glob("*.tar.gz"))
                    if atualizar_pacotes_existentes(pasta_requirements):
                        mostrar_resumo_operacao("Atualização", len(arquivos), True)
                    else:
                        mostrar_resumo_operacao("Atualização", len(arquivos), False)
                    continue
                
                elif acao == '3':  # Baixar novos pacotes do requirements.txt
                    try:
                        pacotes = ler_requirements()
                        print_info(f"Baixando {len(pacotes)} pacotes do requirements.txt...")
                        
                        sucessos = 0
                        for pacote in pacotes:
                            if baixar_pacote(pacote, pasta_requirements):
                                sucessos += 1
                            else:
                                print_warning(f"Falha ao baixar {pacote}")
                        
                        print_success("Download concluído!")
                        mostrar_resumo_operacao("Download", len(pacotes), sucessos == len(pacotes))
                    except Exception as e:
                        log_exception(e, "Erro ao baixar pacotes do requirements.txt")
                        mostrar_resumo_operacao("Download", 0, False)
                    continue
                
                elif acao == '4':  # Limpar pasta e baixar tudo novamente
                    if limpar_pasta_requirements(pasta_requirements):
                        try:
                            pacotes = ler_requirements()
                            print_info(f"Baixando {len(pacotes)} pacotes do requirements.txt...")
                            
                            sucessos = 0
                            for pacote in pacotes:
                                if baixar_pacote(pacote, pasta_requirements):
                                    sucessos += 1
                                else:
                                    print_warning(f"Falha ao baixar {pacote}")
                            
                            print_success("Download concluído!")
                            mostrar_resumo_operacao("Download", len(pacotes), sucessos == len(pacotes))
                        except Exception as e:
                            log_exception(e, "Erro ao baixar pacotes do requirements.txt")
                            mostrar_resumo_operacao("Download", 0, False)
                    continue
                
                elif acao == '5':  # Voltar ao menu principal
                    continue
            
            else:
                # Pasta não existe ou está vazia - cria e baixa pacotes
                if not pasta_existe:
                    pasta_requirements = criar_pasta_requirements()
                
                if tipo_instalacao == '1':  # Pacotes do projeto
                    try:
                        pacotes = ler_requirements()
                        print_info(f"Baixando {len(pacotes)} pacotes do requirements.txt...")
                        
                        sucessos = 0
                        for pacote in pacotes:
                            if baixar_pacote(pacote, pasta_requirements):
                                sucessos += 1
                            else:
                                print_warning(f"Falha ao baixar {pacote}")
                        
                        print_success("Download concluído!")
                        mostrar_resumo_operacao("Download", len(pacotes), sucessos == len(pacotes))
                        
                        # Pergunta se deseja instalar
                        print_info("\nDeseja instalar os pacotes agora? (s/n)")
                        if input().lower() == 's':
                            if not criar_ambiente_virtual():
                                print_error("Falha ao criar ambiente virtual.")
                                continue
                            
                            try:
                                python_path, pip_path = ativar_ambiente_virtual()
                                instalar_pacotes(pip_path, pasta_requirements)
                                mostrar_resumo_operacao("Download e Instalação", len(pacotes), True)
                            except Exception as e:
                                log_exception(e, "Erro ao instalar pacotes")
                                mostrar_resumo_operacao("Download e Instalação", len(pacotes), False)
                        
                    except Exception as e:
                        log_exception(e, "Erro ao processar pacotes do projeto")
                        mostrar_resumo_operacao("Download", 0, False)
                
                elif tipo_instalacao == '2':  # Pacotes do ambiente de desenvolvimento
                    try:
                        pacotes = obter_pacotes_ambiente_desenvolvimento()
                        if not pacotes:
                            print_warning("Nenhum pacote encontrado no ambiente de desenvolvimento.")
                            continue
                        
                        # Filtra pacotes padrão
                        pacotes_filtrados = processar_pacotes_para_download(pacotes)
                        print_info(f"Encontrados {len(pacotes)} pacotes no ambiente de desenvolvimento.")
                        print_info(f"Após filtro: {len(pacotes_filtrados)} pacotes para download.")
                        
                        if not pacotes_filtrados:
                            print_warning("Nenhum pacote relevante encontrado após filtro.")
                            continue
                        
                        print_info(f"Baixando {len(pacotes_filtrados)} pacotes do ambiente de desenvolvimento...")
                        
                        sucessos = 0
                        for pacote in pacotes_filtrados:
                            if baixar_pacote(pacote, pasta_requirements):
                                sucessos += 1
                            else:
                                print_warning(f"Falha ao baixar {pacote}")
                        
                        print_success("Download concluído!")
                        mostrar_resumo_operacao("Download", len(pacotes_filtrados), sucessos == len(pacotes_filtrados))
                        
                        # Pergunta se deseja instalar
                        print_info("\nDeseja instalar os pacotes agora? (s/n)")
                        if input().lower() == 's':
                            if not criar_ambiente_virtual():
                                print_error("Falha ao criar ambiente virtual.")
                                continue
                            
                            try:
                                python_path, pip_path = ativar_ambiente_virtual()
                                instalar_pacotes(pip_path, pasta_requirements)
                                mostrar_resumo_operacao("Download e Instalação", len(pacotes_filtrados), True)
                            except Exception as e:
                                log_exception(e, "Erro ao instalar pacotes")
                                mostrar_resumo_operacao("Download e Instalação", len(pacotes_filtrados), False)
                        
                    except Exception as e:
                        log_exception(e, "Erro ao processar pacotes do ambiente de desenvolvimento")
                        mostrar_resumo_operacao("Download", 0, False)
                
                elif tipo_instalacao == '3':  # Pacotes do sistema
                    try:
                        pacotes = obter_pacotes_sistema()
                        if not pacotes:
                            print_warning("Nenhum pacote encontrado no sistema.")
                            continue
                        
                        # Filtra pacotes padrão
                        pacotes_filtrados = processar_pacotes_para_download(pacotes)
                        print_info(f"Encontrados {len(pacotes)} pacotes no sistema.")
                        print_info(f"Após filtro: {len(pacotes_filtrados)} pacotes para download.")
                        
                        if not pacotes_filtrados:
                            print_warning("Nenhum pacote relevante encontrado após filtro.")
                            continue
                        
                        print_info(f"Baixando {len(pacotes_filtrados)} pacotes do sistema...")
                        
                        sucessos = 0
                        for pacote in pacotes_filtrados:
                            if baixar_pacote(pacote, pasta_requirements):
                                sucessos += 1
                            else:
                                print_warning(f"Falha ao baixar {pacote}")
                        
                        print_success("Download concluído!")
                        mostrar_resumo_operacao("Download", len(pacotes_filtrados), sucessos == len(pacotes_filtrados))
                        
                        # Pergunta se deseja instalar
                        print_info("\nDeseja instalar os pacotes agora? (s/n)")
                        if input().lower() == 's':
                            if not criar_ambiente_virtual():
                                print_error("Falha ao criar ambiente virtual.")
                                continue
                            
                            try:
                                python_path, pip_path = ativar_ambiente_virtual()
                                instalar_pacotes(pip_path, pasta_requirements)
                                mostrar_resumo_operacao("Download e Instalação", len(pacotes_filtrados), True)
                            except Exception as e:
                                log_exception(e, "Erro ao instalar pacotes")
                                mostrar_resumo_operacao("Download e Instalação", len(pacotes_filtrados), False)
                        
                    except Exception as e:
                        log_exception(e, "Erro ao processar pacotes do sistema")
                        mostrar_resumo_operacao("Download", 0, False)
            
            # Pergunta se deseja continuar
            print_info("\nDeseja realizar outra operação? (s/n)")
            if input().lower() != 's':
                print_info("Saindo do Hermes Installer...")
                break
            
    except KeyboardInterrupt:
        print_info("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        log_exception(e, "Erro inesperado no programa principal")
        sys.exit(1)
    finally:
        logger.debug("Finalizando Hermes Installer")

if __name__ == "__main__":
    main()
