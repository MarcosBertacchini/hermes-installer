# Hermes Installer

[![Versão](https://img.shields.io/badge/versão-1.0.30035-blue.svg)](https://github.com/MarcosBertacchini/hermes-installer)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Licença](https://img.shields.io/badge/licença-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/MarcosBertacchini/hermes-installer)

## 📋 Descrição

O Hermes Installer é uma ferramenta robusta para gerenciamento de dependências Python. Ele automatiza o processo de instalação de pacotes, criando um ambiente virtual isolado e garantindo que todas as dependências sejam instaladas corretamente.

## ✨ Funcionalidades

- ✅ Criação automática de ambiente virtual
- 📦 Download e instalação de pacotes Python
- 🔄 Verificação de dependências
- 📝 Sistema de logs detalhado
- 🎨 Interface colorida no terminal
- 🔍 Verificação de integridade dos pacotes
- 🔄 Atualização automática do pip

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

1. Coloque seu arquivo `requirements.txt` no mesmo diretório do script
2. Execute o script:
```bash
python hermes_installer.py
```
3. Siga as instruções na tela

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