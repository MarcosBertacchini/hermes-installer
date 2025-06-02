# Hermes Installer

## Versão 1.0.30035

### Descrição
O Hermes Installer é uma ferramenta para gerenciamento de dependências Python. Ele automatiza o processo de instalação de pacotes Python, criando um ambiente virtual isolado e gerenciando as dependências de forma eficiente.

### Funcionalidades
- Criação automática de ambiente virtual Python
- Download e armazenamento local de pacotes
- Verificação de pacotes faltantes e desatualizados
- Instalação de dependências em ambiente isolado
- Sistema de logs para rastreamento de operações
- Interface colorida para melhor visualização

### Requisitos
- Python 3.6 ou superior
- Conexão com a internet para download inicial de pacotes
- Permissões de escrita no diretório de instalação

### Estrutura de Pastas
```
hermes_installer/
├── hermes_installer.exe
├── requirements.txt
├── logs/
├── requirements/
└── venv/
```

### Como Usar
1. Execute o arquivo `hermes_installer.exe`
2. Confirme o início da instalação
3. Aguarde o processo de verificação e download dos pacotes
4. Confirme a instalação dos pacotes
5. Após a conclusão, ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

### Logs
Os logs de execução são armazenados na pasta `logs/` com o formato:
- Nome: `hermes_installer_YYYYMMDD_HHMMSS.log`
- Contém informações detalhadas sobre o processo de instalação
- Útil para diagnóstico de problemas

### Notas
- O instalador cria um ambiente virtual isolado para evitar conflitos com outras instalações Python
- Os pacotes são baixados e armazenados localmente para instalações futuras
- Em caso de erro, consulte o arquivo de log para mais detalhes

### Suporte
Para reportar problemas ou sugerir melhorias, por favor abra uma issue no repositório do projeto. 