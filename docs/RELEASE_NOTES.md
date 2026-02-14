## OmniTranslator v1.1.0

### 🐛 Correção de Bug Crítico
- **Fix: Segmentation fault ao usar engine Google Online**
  - O crash ocorria porque sinais Qt eram emitidos de thread não-Qt
  - Implementada fila thread-safe para comunicação entre threads
  - Adicionadas verificações de segurança em múltiplos pontos

### ✨ Melhorias de Arquitetura
- **Schema de Configuração com Pydantic** - Validação automática de todas as configurações
- **Sistema de Logging Estruturado** - Logs com níveis apropriados e cores no terminal  
- **AppInitializer** - Separação da lógica de inicialização em fases bem definidas
- **BaseAudioEngine** - Classe base abstrata para reduzir duplicação de código
- **Segurança nas Atualizações** - Validação de checksum SHA256 para downloads

### 🧪 Qualidade
- **Suite Completa de Testes** - 30 testes unitários implementados
  - Testes de configuração (validação Pydantic)
  - Testes de logging
  - Testes de segurança (checksum SHA256)
  - Testes de engine base

### 📦 Arquivos Incluídos
- OmniTranslator.exe - Executável principal (271 MB)
- OmniTranslator.exe.sha256 - Checksum de verificação

### ⚠️ Notas Importantes
- Execute o programa como Administrador para melhor compatibilidade com VAD
- O primeiro uso pode demorar para baixar modelos (se usar Vosk)
- Requer conexão com internet para tradução e engine Google

### 🔒 Checksum SHA256
```
423779c5bcc05fa8562b747b54e83f5711f13f9149db818424b28ce9772cbc4a  OmniTranslator.exe
```
