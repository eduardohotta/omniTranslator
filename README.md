# OmniTranslator v1.1.0 🎙️

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/eduardohotta/omniTranslator/releases)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Tradução de voz em tempo real com suporte a múltiplos idiomas**

OmniTranslator é uma aplicação desktop que captura áudio do microfone em tempo real, transcreve o texto usando reconhecimento de voz (online ou offline) e traduz automaticamente para o idioma desejado.

![OmniTranslator Screenshot](https://via.placeholder.com/800x400/2d2d2d/39FF14?text=OmniTranslator+Interface)

## ✨ Funcionalidades

- 🎯 **Reconhecimento de Voz em Tempo Real** - Captura e transcreve fala instantaneamente
- 🌐 **Tradução Automática** - Traduz para múltiplos idiomas simultaneamente
- 🎨 **Interface Overlay Customizável** - Janela flutuante com opacidade ajustável
- 🔄 **Múltiplos Engines**:
  - **Google Online** (recomendado) - Alta precisão, requer internet
  - **Vosk Offline** - Funciona sem internet (modelos small/big disponíveis)
  - **Whisper** - Modelo OpenAI para reconhecimento avançado
- ⌨️ **Atalhos de Teclado Globais** - Controle sem sair do aplicativo atual
- ⚙️ **Configurações Persistentes** - Salva preferências automaticamente
- 🔒 **Atualizações Seguras** - Verificação de checksum SHA256

## 🚀 Instalação

### Download Pre-compilado (Recomendado)

1. Acesse a [página de releases](https://github.com/eduardohotta/omniTranslator/releases)
2. Baixe `OmniTranslator.exe` da última versão
3. Execute como Administrador (recomendado para melhor compatibilidade com VAD)

### Instalação via Código Fonte

```bash
# Clone o repositório
git clone https://github.com/eduardohotta/omniTranslator.git
cd omniTranslator

# Instale as dependências
pip install -r requirements.txt

# Baixe os modelos (primeira execução)
python download_models.py

# Execute
python main.py
```

### Requisitos

- **Windows 10/11** (64-bit)
- **Python 3.10+** (se executar via código fonte)
- **Microfone** configurado e funcional
- **Conexão com Internet** (para tradução e engine Google)

## 📖 Como Usar

### Primeira Execução

1. Execute o `OmniTranslator.exe`
2. Na primeira vez, o programa pode solicitar download de modelos (se usar Vosk)
3. Configure seu microfone nas **Configurações** (ícone ⚙️)
4. Escolha o idioma de origem e destino
5. Clique em **"Iniciar Transcrição"**

### Interface

- **🟢 Círculo Verde**: O programa está ouvindo
- **🔴 Círculo Vermelho**: Fala detectada, processando...
- **Texto Branco**: Texto original transcrito
- **Texto Verde (#39FF14)**: Texto traduzido

### Atalhos de Teclado

| Atalho | Função |
|--------|--------|
| `Ctrl + Alt + S` | Pausar/Retomar escuta |
| `Ctrl + Alt + C` | Limpar texto na tela |

### Movimentação

- **Arraste a barra de título** para mover a janela
- **Redimensione** pelos cantos inferiores
- **Duplo-clique no círculo** para alternar "sempre no topo"

## ⚙️ Configuração

O arquivo `config.json` é criado automaticamente na primeira execução:

```json
{
  "source_lang": "pt",
  "target_lang": "en",
  "model_type": "google",
  "opacity": 0.69,
  "font_size": 14,
  "always_on_top": true,
  "win_width": 1000,
  "win_height": 240,
  "vad_threshold": 300
}
```

### Opções de Configuração

| Opção | Descrição | Valores |
|-------|-----------|---------|
| `source_lang` | Idioma de origem | `pt`, `en`, `es`, `fr`, etc. |
| `target_lang` | Idioma de destino | `en`, `es`, `fr`, `de`, `ja`, `zh-CN` |
| `model_type` | Engine de reconhecimento | `google`, `small`, `big`, `whisper` |
| `opacity` | Opacidade da janela | 0.0 a 1.0 |
| `font_size` | Tamanho da fonte | 8 a 72 |
| `always_on_top` | Sempre visível | `true`/`false` |
| `win_width` | Largura da janela | 400 a 1920 |
| `win_height` | Altura da janela | 100 a 600 |
| `vad_threshold` | Sensibilidade do VAD | 100 a 5000 |

## 🔧 Troubleshooting

### Segmentation Fault / Crash ao usar Google

**Solução**: Atualize para v1.1.0+ - O problema foi corrigido com processamento thread-safe.

### "Nenhum dispositivo de áudio encontrado"

1. Verifique se o microfone está conectado
2. Abra as Configurações e selecione manualmente o dispositivo
3. Certifique-se de que o microfone não está sendo usado por outro programa

### Tradução não funciona

- Verifique sua conexão com a internet
- O tradutor automático requer a biblioteca `deep-translator`
- Em caso de erro, o texto original será exibido

### Qualidade de reconhecimento baixa

1. **Use o engine Google** (requer internet) para melhor precisão
2. **Ajuste o VAD**: Aumente `vad_threshold` se estiver detectando ruído
3. **Fale mais próximo do microfone**
4. **Evite ambientes com muito ruído**

### Arquivos de modelo não encontrados

Execute o download manualmente:
```bash
python download_models.py --small  # Modelo pequeno (~40MB)
python download_models.py --big    # Modelo grande (~1GB)
```

## 🧪 Desenvolvimento

### Executar Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python -m pytest tests/test_config_schema.py -v
```

### Estrutura do Projeto

```
omniTranslator/
├── core/
│   ├── audio.py          # Captura de áudio
│   ├── transcriber.py    # Reconhecimento de voz
│   ├── translator.py     # Tradução
│   ├── pipeline.py       # Processamento
│   ├── config_schema.py  # Validação de config
│   ├── logging_config.py # Logging estruturado
│   ├── app_initializer.py # Inicialização
│   ├── base_engine.py    # Engine base
│   └── updater.py        # Atualizações
├── ui/
│   ├── overlay.py        # Interface principal
│   └── settings.py       # Configurações
├── tests/                # Testes unitários
├── main.py              # Entry point
├── download_models.py   # Download de modelos
└── requirements.txt     # Dependências
```

### Build do Executável

```bash
# Instale o PyInstaller
pip install pyinstaller

# Compile
pyinstaller OmniTranslator.spec --clean

# O executável estará em dist/OmniTranslator.exe
```

## 📦 Release Notes

### v1.1.0 (14/02/2026)

**Correções:**
- ✅ Fix: Segmentation fault ao usar engine Google Online
- ✅ Thread-safe processing para evitar crashes no Windows
- ✅ Verificações de segurança adicionadas

**Melhorias:**
- ✅ Schema de configuração com Pydantic
- ✅ Sistema de logging estruturado
- ✅ AppInitializer para inicialização em fases
- ✅ BaseAudioEngine para reduzir duplicação
- ✅ Validação de checksum SHA256 nas atualizações
- ✅ Suite completa de testes (30 testes)

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [Vosk](https://github.com/alphacep/vosk-api) - Reconhecimento offline
- [Whisper](https://github.com/openai/whisper) - Reconhecimento avançado
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Engine Google
- [PySide6](https://www.qt.io/qt-for-python) - Interface gráfica
- [deep-translator](https://github.com/nidhaloff/deep-translator) - Tradução

---

**Autor:** [eduardohotta](https://github.com/eduardohotta)

⭐ Se este projeto foi útil, considere dar uma estrela!
