# Correção de Segmentation Fault - OmniTranslator

## Problema
O programa estava fechando inesperadamente com `Segmentation fault` durante o reconhecimento de fala usando o engine Google Online.

## Causa Raiz
O problema ocorria porque **sinais Qt estavam sendo emitidos de uma thread do `ThreadPoolExecutor`**, o que não é thread-safe no Windows e causa segmentation faults.

O fluxo problemático era:
1. Áudio detectado → `_async_pipeline` executado na thread do executor
2. Dentro dessa thread, sinais Qt eram emitidos diretamente (`update_thinking_signal.emit`, `update_text_signal.emit`)
3. Isso causava acesso não-sincronizado à memória → **Segmentation fault**

## Solução Implementada

### 1. Fila Thread-Safe para Resultados
Criamos uma fila (`queue.Queue`) para passar resultados da thread do executor de volta para a thread do QThread principal:

```python
# No __init__
self._result_queue = queue.Queue()

# Na thread do executor (seguro)
self._result_queue.put({'type': 'text', 'text': texto, 'translation': traducao})

# Na thread do QThread (processamento dos resultados)
while not self._result_queue.empty():
    result = self._result_queue.get_nowait()
    self.update_text_signal.emit(result['text'], result['translation'])
```

### 2. Verificações de Segurança Adicionadas
Adicionamos verificações em múltiplos pontos para evitar acesso a objetos nulos:

- Verificação de `transcriber` e `engine` antes de usar
- Verificação de `sample_rate` válido
- Verificação de dados de áudio não vazios
- Verificação de `recognizer` inicializado

### 3. Tratamento de Erros Aprimorado
- Adicionado `traceback.print_exc()` para melhor debugging
- Try-except em mais pontos do código
- Mensagens de log mais descritivas

### 4. Encerramento Seguro da Thread
Melhoramos o método `stop()` para:
- Processar resultados pendentes antes de fechar
- Desligar o `ThreadPoolExecutor` corretamente
- Aguardar com timeout e forçar terminação se necessário

## Arquivos Modificados

### core/pipeline.py
- Adicionada `_result_queue` para comunicação thread-safe
- Modificado `run()` para processar resultados da fila
- Modificado `_async_pipeline()` para usar a fila em vez de emitir sinais diretamente
- Adicionadas verificações de segurança
- Melhorado método `stop()`

### core/transcriber.py
- Adicionadas verificações no `GoogleEngine.recognize()`:
  - Verificação de dados de áudio não vazios
  - Verificação de `sample_rate` válido
  - Verificação de array numpy não vazio
  - Verificação de `recognizer` inicializado
- Adicionado traceback para debugging

## Testes
Execute os testes para verificar que tudo funciona:

```bash
python -m pytest tests/ -v
```

## Monitoramento
Se o problema persistir, verifique os logs do console. Agora temos:
- Mensagens de warning quando objetos não estão disponíveis
- Tracebacks completos em caso de erro
- Logs de início/fim de processamento

## Próximos Passos (Opcional)
Se desejar mais estabilidade, considere:
1. Usar `QThread` ao invés de `ThreadPoolExecutor` para processamento assíncrono
2. Implementar timeout no reconhecimento do Google
3. Adicionar mecanismo de retry para falhas de reconhecimento
4. Criar logs em arquivo para análise posterior
