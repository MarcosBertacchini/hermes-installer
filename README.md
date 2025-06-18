# Hermes Installer

[![Versão](https://img.shields.io/badge/versão-1.0.4-blue.svg)](https://github.com/MarcosBertacchini/hermes-installer)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Licença](https://img.shields.io/badge/licença-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/MarcosBertacchini/hermes-installer)

## 📋 Descrição

O Hermes Installer é uma ferramenta robusta para gerenciamento de dependências Python. Ele automatiza o processo de instalação de pacotes, criando um ambiente virtual isolado e garantindo que todas as dependências sejam instaladas corretamente.

## ✨ Novidades na versão 1.0.4

- Novo menu interativo para escolha do tipo de instalação:
  - Instalar pacotes do projeto (`requirements.txt`)
  - Instalar pacotes do ambiente de desenvolvimento (tudo que está instalado no seu ambiente Python)
  - Instalar todos os pacotes do sistema
- Detecção automática da pasta `requirements/`:
  - Se existir, permite instalar, atualizar, baixar novos pacotes ou limpar a pasta
  - Se não existir, cria automaticamente
- Resumo da operação ao final de cada ação (instalação, download, atualização)
- Informações claras de como ativar/desativar o ambiente virtual
- Filtro automático para não baixar/instalar pacotes padrão do Python
- Melhor tratamento de erros e logs
- Removida a limitação de só instalar do `requirements.txt` (agora pode instalar do ambiente ou do sistema)

## 🚀 Requisitos

- Python 3.8 ou superior
- Conexão com a internet (para download inicial dos pacotes)
- Permissões de administrador (para criar ambiente virtual)

## 📁 Estrutura do Projeto

```
hermes-installer/
├── hermes_installer.py    # Script principal
├── requirements.txt       # Lista de dependências
├── README.md             # Este arquivo
├── LICENSE               # Licença MIT
├── logs/                 # Diretório de logs
├── requirements/         # Pacotes Python baixados
└── venv/                # Ambiente virtual Python
```

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/MarcosBertacchini/hermes-installer.git
cd hermes-installer
```

2. Execute o instalador:
```bash
python hermes_installer.py
```

## 💻 Uso

1. Coloque seu arquivo `requirements.txt` no mesmo diretório do script (opcional, se quiser instalar do projeto)
2. Execute o script:
```bash
python hermes_installer.py
```
3. Siga as instruções na tela e escolha o tipo de instalação desejado

### Opções do menu interativo
- Instalar pacotes do projeto (`requirements.txt`)
- Instalar pacotes do ambiente de desenvolvimento
- Instalar todos os pacotes do sistema
- Sair

Se a pasta `requirements/` já existir, você pode:
- Instalar pacotes existentes
- Atualizar pacotes existentes
- Baixar novos pacotes do `requirements.txt`
- Limpar a pasta e baixar tudo novamente

## 📝 Logs

Os logs são armazenados no diretório `logs/` com o formato:
```
hermes_installer_YYYYMMDD_HHMMSS.log
```

## 🔧 Configuração

O script utiliza as seguintes configurações padrão:
- Diretório de logs: `./logs/`
- Diretório de pacotes: `./requirements/`
- Ambiente virtual: `./venv/`

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**Marcos Bertacchini**
- Email: marcos.bertacchini@live.com
- GitHub: [@MarcosBertacchini](https://github.com/MarcosBertacchini)

## 🙏 Agradecimentos

- [Python](https://www.python.org/)
- [pip](https://pip.pypa.io/)
- [colorama](https://pypi.org/project/colorama/)
- [tqdm](https://pypi.org/project/tqdm/)
- [requests](https://pypi.org/project/requests/) 