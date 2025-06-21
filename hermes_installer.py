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
import pkg_resources

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

def instalar_pacotes_pasta_existente(pip_path: str, pasta_requirements: Path):
    """Instala os pacotes que já existem na pasta requirements."""
    pacotes_disponiveis = listar_pacotes_pasta(pasta_requirements)
    
    if not pacotes_disponiveis:
        print_warning("Nenhum pacote encontrado na pasta requirements!")
        return False
    
    print_highlight(f"\nInstalando {len(pacotes_disponiveis)} pacotes da pasta requirements...")
    
    for pacote in pacotes_disponiveis:
        nome_pacote, versao = extrair_nome_versao(pacote)
        if not versao:
            continue
            
        print_info(f"Instalando {nome_pacote}...")
        try:
            subprocess.run([pip_path, "install", "--no-index", "--find-links", str(pasta_requirements.absolute()), pacote], check=True)
            print_success(f"✓ {nome_pacote} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print_error(f"✗ Erro ao instalar {nome_pacote}: {e}")
            return False
    
    print_success("Todos os pacotes da pasta requirements foram instalados com sucesso!")
    return True

def instalar_pacotes_ambiente_desenvolvimento(pip_path: str, pasta_requirements: Path):
    """Instala todos os pacotes do ambiente de desenvolvimento atual."""
    pacotes_ambiente = obter_pacotes_ambiente_desenvolvimento()
    
    if not pacotes_ambiente:
        print_warning("Nenhum pacote encontrado no ambiente de desenvolvimento!")
        return False
    
    print_highlight(f"\nInstalando {len(pacotes_ambiente)} pacotes do ambiente de desenvolvimento...")
    
    # Primeiro baixa todos os pacotes
    print_info("Baixando pacotes do ambiente de desenvolvimento...")
    for pacote in pacotes_ambiente:
        if not baixar_pacote(pacote, pasta_requirements):
            print_warning(f"Falha ao baixar {pacote}, continuando...")
    
    # Depois instala todos
    print_info("Instalando pacotes...")
    for pacote in pacotes_ambiente:
        nome_pacote, versao = extrair_nome_versao(pacote)
        if not versao:
            continue
            
        print_info(f"Instalando {nome_pacote}...")
        try:
            subprocess.run([pip_path, "install", "--no-index", "--find-links", str(pasta_requirements.absolute()), pacote], check=True)
            print_success(f"✓ {nome_pacote} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print_error(f"✗ Erro ao instalar {nome_pacote}: {e}")
            return False
    
    print_success("Todos os pacotes do ambiente de desenvolvimento foram instalados com sucesso!")
    return True

def atualizar_pacotes_existentes(pasta_requirements: Path):
    """Atualiza os pacotes existentes na pasta requirements."""
    pacotes_existentes = listar_pacotes_pasta(pasta_requirements)
    
    if not pacotes_existentes:
        print_warning("Nenhum pacote encontrado na pasta requirements para atualizar!")
        return False
    
    print_highlight(f"\nAtualizando {len(pacotes_existentes)} pacotes existentes...")
    
    # Remove todos os arquivos existentes
    for arquivo in pasta_requirements.iterdir():
        if arquivo.is_file() and (arquivo.suffix == '.whl' or arquivo.suffixes == ['.tar', '.gz']):
            arquivo.unlink()
            print_info(f"Removido: {arquivo.name}")
    
    # Baixa as versões mais recentes
    for pacote in pacotes_existentes:
        if not baixar_pacote(pacote, pasta_requirements):
            print_warning(f"Falha ao atualizar {pacote}")
    
    print_success("Pacotes atualizados com sucesso!")
    return True

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

def obter_pacotes_ambiente_desenvolvimento() -> List[str]:
    """Obtém todos os pacotes instalados no ambiente de desenvolvimento atual."""
    try:
        pacotes = []
        for dist in pkg_resources.working_set:
            nome = dist.project_name
            versao = dist.version
            pacotes.append(f"{nome}=={versao}")
        return sorted(pacotes)
    except Exception as e:
        logger.error(f"Erro ao obter pacotes do ambiente de desenvolvimento: {e}")
        return []

def contar_pacotes_pasta(pasta_requirements: Path) -> int:
    """Conta quantos pacotes existem na pasta requirements."""
    if not pasta_requirements.exists():
        return 0
    
    # Conta arquivos .whl e .tar.gz
    whl_files = list(pasta_requirements.glob("*.whl"))
    tar_files = list(pasta_requirements.glob("*.tar.gz"))
    return len(whl_files) + len(tar_files)

def listar_pacotes_pasta(pasta_requirements: Path) -> List[str]:
    """Lista os pacotes disponíveis na pasta requirements."""
    if not pasta_requirements.exists():
        return []
    
    pacotes = []
    for arquivo in pasta_requirements.iterdir():
        if arquivo.is_file() and (arquivo.suffix == '.whl' or arquivo.suffixes == ['.tar', '.gz']):
            # Extrai nome e versão do nome do arquivo
            nome_arquivo = arquivo.stem
            if arquivo.suffixes == ['.tar', '.gz']:
                nome_arquivo = arquivo.stem.replace('.tar', '')
            
            # Remove extensões e números de build
            partes = nome_arquivo.split('-')
            if len(partes) >= 2:
                nome = partes[0]
                versao = partes[1]
                pacotes.append(f"{nome}=={versao}")
    
    return sorted(pacotes)

def exibir_menu_opcoes(pasta_requirements: Path, pacotes_requirements: List[str], pacotes_ambiente: List[str]):
    """Exibe menu de opções para o usuário."""
    print(f"\n{Fore.CYAN}╔═══════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║                    OPÇÕES DISPONÍVEIS                 ║")
    print(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════╝")
    
    # Verifica se a pasta requirements existe
    if pasta_requirements.exists():
        num_pacotes = contar_pacotes_pasta(pasta_requirements)
        print(f"\n{Fore.GREEN}✓ Pasta 'requirements' encontrada com {num_pacotes} pacotes")
        
        if num_pacotes > 0:
            print(f"{Fore.YELLOW}1. Instalar pacotes existentes na pasta requirements")
            print(f"{Fore.YELLOW}2. Atualizar pacotes existentes (baixar versões mais recentes)")
        print(f"{Fore.YELLOW}3. Baixar pacotes do requirements.txt (substituir existentes)")
    else:
        print(f"\n{Fore.RED}✗ Pasta 'requirements' não encontrada")
        print(f"{Fore.YELLOW}1. Criar pasta requirements e baixar pacotes do requirements.txt")
    print(f"{Fore.YELLOW}4. Baixar pacotes do ambiente de desenvolvimento (apenas baixar)")
    print(f"{Fore.YELLOW}5. Instalar todos os pacotes do ambiente de desenvolvimento atual")
    print(f"{Fore.YELLOW}6. Sair")
    return pasta_requirements.exists()

def obter_escolha_usuario() -> int:
    """Obtém a escolha do usuário."""
    while True:
        try:
            escolha = input(f"\n{Fore.CYAN}Escolha uma opção (1-6): ").strip()
            escolha_int = int(escolha)
            if 1 <= escolha_int <= 6:
                return escolha_int
            else:
                print_error("Opção inválida. Digite um número entre 1 e 6.")
        except ValueError:
            print_error("Entrada inválida. Digite um número.")

def confirmar_acao(acao: str) -> bool:
    """Confirma se o usuário deseja executar uma ação."""
    print(f"\n{Fore.YELLOW}Deseja {acao}? (S/N)")
    resposta = input().strip().upper()
    return resposta == 'S'

def main():
    try:
        # Exibe o logo
        exibir_logo()
        print_highlight("\n=== Hermes Installer ===")
        logger.debug("Iniciando Hermes Installer")
        
        # Verifica a estrutura básica de pastas
        script_dir = get_script_dir()
        logs_dir = script_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Obtém informações sobre o ambiente
        pasta_requirements = script_dir / "requirements"
        pacotes_requirements = []
        pacotes_ambiente = obter_pacotes_ambiente_desenvolvimento()
        
        # Verifica se existe requirements.txt
        requirements_file = script_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                pacotes_requirements = ler_requirements()
                logger.debug(f"Pacotes lidos do requirements.txt: {len(pacotes_requirements)}")
            except Exception as e:
                log_exception(e, "Erro ao ler requirements.txt")
                pacotes_requirements = []
        else:
            print_warning("Arquivo requirements.txt não encontrado!")
            logger.warning("Arquivo requirements.txt não encontrado")
        
        # Exibe informações do ambiente
        print_info(f"\nAmbiente de desenvolvimento: {len(pacotes_ambiente)} pacotes detectados")
        if pacotes_requirements:
            print_info(f"Requirements.txt: {len(pacotes_requirements)} pacotes listados")
        
        # Exibe menu de opções
        pasta_existe = exibir_menu_opcoes(pasta_requirements, pacotes_requirements, pacotes_ambiente)
        
        # Obtém a escolha do usuário
        escolha = obter_escolha_usuario()
        
        # Processa a escolha
        if escolha == 6:
            print_info("Saindo do Hermes Installer.")
            sys.exit(0)
        
        # Cria o ambiente virtual se necessário
        if not criar_ambiente_virtual():
            print_error("Falha ao criar ambiente virtual. Verifique o log para mais detalhes.")
            sys.exit(1)
        
        # Ativa o ambiente virtual
        try:
            python_path, pip_path = ativar_ambiente_virtual()
            logger.debug(f"Ambiente virtual ativado. Python: {python_path}, Pip: {pip_path}")
        except Exception as e:
            log_exception(e, "Erro ao ativar ambiente virtual")
            sys.exit(1)
        
        # Atualiza o pip
        print_info("Atualizando pip...")
        try:
            subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
            logger.debug("Pip atualizado com sucesso")
        except Exception as e:
            log_exception(e, "Erro ao atualizar pip pela internet")
            # Tentar instalar pip localmente
            print_warning("Não foi possível atualizar o pip pela internet. Tentando instalar versão local do pip...")
            pip_local = None
            for arquivo in pasta_requirements.iterdir():
                if arquivo.is_file() and arquivo.name.startswith("pip-") and (arquivo.suffix == ".whl" or arquivo.suffixes == [".tar", ".gz"]):
                    pip_local = str(arquivo)
                    break
            if pip_local:
                try:
                    subprocess.run([pip_path, "install", "--upgrade", pip_local], check=True)
                    print_success("Pip instalado/atualizado localmente com sucesso!")
                    logger.debug("Pip instalado/atualizado localmente com sucesso")
                except Exception as e2:
                    log_exception(e2, "Falha ao instalar pip localmente")
                    print_error("Falha ao instalar o pip localmente. Verifique sua conexão ou o arquivo local.")
                    sys.exit(1)
            else:
                print_error("Arquivo do pip não encontrado na pasta requirements. Não foi possível atualizar o pip.")
                sys.exit(1)
        
        # Executa a ação escolhida
        sucesso = None
        
        if escolha == 1:
            if pasta_existe and contar_pacotes_pasta(pasta_requirements) > 0:
                # Instalar pacotes existentes
                if confirmar_acao("instalar os pacotes existentes na pasta requirements"):
                    sucesso = instalar_pacotes_pasta_existente(pip_path, pasta_requirements)
            else:
                # Criar pasta e baixar do requirements.txt
                if not pacotes_requirements:
                    print_error("Nenhum pacote encontrado no requirements.txt!")
                    sys.exit(1)
                
                if confirmar_acao("criar pasta requirements e baixar pacotes do requirements.txt"):
                    pasta_requirements.mkdir(exist_ok=True)
                    print_info("Baixando pacotes do requirements.txt...")
                    for pacote in pacotes_requirements:
                        baixar_pacote(pacote, pasta_requirements)
                    
                    if confirmar_acao("instalar os pacotes baixados"):
                        sucesso = instalar_pacotes(pip_path, pasta_requirements)
        
        elif escolha == 2:
            # Atualizar pacotes existentes
            if confirmar_acao("atualizar os pacotes existentes"):
                sucesso = atualizar_pacotes_existentes(pasta_requirements)
                if sucesso and confirmar_acao("instalar os pacotes atualizados"):
                    sucesso = instalar_pacotes_pasta_existente(pip_path, pasta_requirements)
        
        elif escolha == 3:
            # Baixar do requirements.txt (substituir existentes)
            if not pacotes_requirements:
                print_error("Nenhum pacote encontrado no requirements.txt!")
                sys.exit(1)
            
            if confirmar_acao("baixar pacotes do requirements.txt (substituindo existentes)"):
                pasta_requirements.mkdir(exist_ok=True)
                # Remove arquivos existentes
                for arquivo in pasta_requirements.iterdir():
                    if arquivo.is_file() and (arquivo.suffix == '.whl' or arquivo.suffixes == ['.tar', '.gz']):
                        arquivo.unlink()
                
                print_info("Baixando pacotes do requirements.txt...")
                for pacote in pacotes_requirements:
                    baixar_pacote(pacote, pasta_requirements)
                
                if confirmar_acao("instalar os pacotes baixados"):
                    sucesso = instalar_pacotes(pip_path, pasta_requirements)
        
        elif escolha == 4:
            # Baixar pacotes do ambiente de desenvolvimento (apenas baixar)
            if not pacotes_ambiente:
                print_error("Nenhum pacote encontrado no ambiente de desenvolvimento!")
                sys.exit(1)
            if confirmar_acao("baixar todos os pacotes do ambiente de desenvolvimento (apenas baixar)"):
                pasta_requirements.mkdir(exist_ok=True)
                print_info("Baixando pacotes do ambiente de desenvolvimento...")
                for pacote in pacotes_ambiente:
                    baixar_pacote(pacote, pasta_requirements)
                print_success("Todos os pacotes do ambiente de desenvolvimento foram baixados!")
                sucesso = True
        
        elif escolha == 5:
            # Instalar pacotes do ambiente de desenvolvimento
            if not pacotes_ambiente:
                print_error("Nenhum pacote encontrado no ambiente de desenvolvimento!")
                sys.exit(1)
            if confirmar_acao("instalar todos os pacotes do ambiente de desenvolvimento"):
                pasta_requirements.mkdir(exist_ok=True)
                sucesso = instalar_pacotes_ambiente_desenvolvimento(pip_path, pasta_requirements)
        
        # Resultado final
        if sucesso:
            print_success("\n✓ Download concluída com sucesso!")
            logger.debug("Download concluída com sucesso")
            print_highlight("\nPara ativar o ambiente virtual:")
            if sys.platform == "win32":
                print(f"{Fore.CYAN}venv\\Scripts\\activate")
            else:
                print(f"{Fore.CYAN}source venv/bin/activate")
        elif sucesso is False:
            print_error("\n✗ Instalação falhou. Verifique o log para mais detalhes.")
            logger.error("Instalação falhou")
            sys.exit(1)
        else:
            print_info("\nAção cancelada pelo usuário.")
            logger.info("Ação cancelada pelo usuário")
            
    except subprocess.CalledProcessError as e:
        log_exception(e, "Erro durante a instalação")
        sys.exit(1)
    except Exception as e:
        log_exception(e, "Erro inesperado")
        sys.exit(1)
    finally:
        logger.debug("Finalizando Hermes Installer")

if __name__ == "__main__":
    main()
