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

def main():
    try:
        # Exibe o logo e pergunta se deseja continuar
        exibir_logo()
        if not confirmar_inicio():
            print_info("Instalação cancelada pelo usuário.")
            logger.debug("Instalação cancelada pelo usuário na confirmação inicial")
            sys.exit(0)

        print_highlight("\n=== Hermes Installer ===")
        logger.debug("Iniciando Hermes Installer")
        
        # Verifica a estrutura de pastas
        if not verificar_estrutura_pastas():
            print_error("Erro na verificação da estrutura de pastas. Verifique o log para mais detalhes.")
            sys.exit(1)
        
        # Lê os pacotes do requirements.txt
        try:
            pacotes = ler_requirements()
            logger.debug(f"Pacotes lidos do requirements.txt: {len(pacotes)}")
        except Exception as e:
            log_exception(e, "Erro ao ler requirements.txt")
            sys.exit(1)
        
        # Cria a pasta requirements
        try:
            pasta_requirements = criar_pasta_requirements()
            logger.debug(f"Pasta requirements criada/verificada: {pasta_requirements}")
        except Exception as e:
            log_exception(e, "Erro ao criar pasta requirements")
            sys.exit(1)
        
        # Verifica os pacotes existentes
        print_info("\nVerificando pacotes na pasta requirements...")
        try:
            pacotes_faltantes, pacotes_desatualizados = verificar_pacotes_requirements(pasta_requirements, pacotes)
            logger.debug(f"Pacotes faltantes: {len(pacotes_faltantes)}")
            logger.debug(f"Pacotes desatualizados: {len(pacotes_desatualizados)}")
        except Exception as e:
            log_exception(e, "Erro ao verificar pacotes")
            sys.exit(1)
        
        if pacotes_faltantes:
            print_warning("\nPacotes faltantes:")
            for pacote in pacotes_faltantes:
                print(f"- {pacote}")
                logger.debug(f"Pacote faltante: {pacote}")
        
        if pacotes_desatualizados:
            print_warning("\nPacotes desatualizados ou corrompidos:")
            for pacote in pacotes_desatualizados:
                print(f"- {pacote}")
                logger.debug(f"Pacote desatualizado: {pacote}")
        
        if pacotes_faltantes or pacotes_desatualizados:
            print_info("\nBaixando pacotes faltantes e atualizando pacotes desatualizados...")
            downloads_sucesso = True
            for pacote in pacotes_faltantes + pacotes_desatualizados:
                try:
                    if not baixar_pacote(pacote, pasta_requirements):
                        downloads_sucesso = False
                        logger.error(f"Falha ao baixar pacote: {pacote}")
                        break
                except Exception as e:
                    log_exception(e, f"Erro ao baixar pacote {pacote}")
                    downloads_sucesso = False
                    break
            
            if not downloads_sucesso:
                print_warning("Erro ao baixar alguns pacotes. Deseja continuar com a instalação? (s/n)")
                logger.debug("Usuário será questionado sobre continuar após falha nos downloads")
                if input().lower() != 's':
                    print_error("Instalação cancelada pelo usuário.")
                    logger.debug("Instalação cancelada pelo usuário após falha nos downloads")
                    sys.exit(0)
        else:
            print_success("Todos os pacotes estão atualizados!")
            logger.debug("Todos os pacotes estão atualizados")
        
        # Pergunta se deseja instalar
        print_info("\nDeseja instalar os pacotes agora? (s/n)")
        if input().lower() != 's':
            print_error("Instalação cancelada pelo usuário.")
            logger.debug("Instalação cancelada pelo usuário")
            sys.exit(0)
        
        # Cria o ambiente virtual
        if not criar_ambiente_virtual():
            print_error("Falha ao criar ambiente virtual. Verifique o log para mais detalhes.")
            sys.exit(1)
        
        # Ativa o ambiente virtual e obtém os caminhos do Python e pip
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
            log_exception(e, "Erro ao atualizar pip")
            sys.exit(1)
        
        # Instala os pacotes
        try:
            instalar_pacotes(pip_path, pasta_requirements)
            logger.debug("Pacotes instalados com sucesso")
        except Exception as e:
            log_exception(e, "Erro ao instalar pacotes")
            sys.exit(1)
        
        print_success("\nInstalação concluída com sucesso!")
        logger.debug("Instalação concluída com sucesso")
        print_highlight("\nPara ativar o ambiente virtual:")
        if sys.platform == "win32":
            print(f"{Fore.CYAN}venv\\Scripts\\activate")
        else:
            print(f"{Fore.CYAN}source venv/bin/activate")
            
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
