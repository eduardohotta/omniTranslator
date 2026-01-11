# Instruções de Uso - Tradutor Offline

Aqui está o passo a passo para configurar e rodar o seu programa de tradução:

## 1. Instalar Dependências
Abra o terminal na pasta do projeto e execute:
```powershell
pip install -r requirements.txt
```
*(Se houver erro com o `webrtcvad`, não se preocupe, o programa vai funcionar mesmo sem ele)*

## 2. Baixar os Modelos (Primeira vez apenas)
Execute este script para baixar os modelos de inteligência artificial (Vosk e Argos):
```powershell
python download_models.py
```
Isso pode demorar um pouco dependendo da sua internet (aprox. 150MB).

## 3. Iniciar o Programa
Para abrir o overlay, execute:
```powershell
python main.py
```

## 4. Como Usar
- **Fale no microfone**: O texto deve aparecer automaticamente na tela.
- **Ctrl + Alt + S**: Pausar / Retomar a escuta.
- **Ctrl + Alt + C**: Limpar o texto da tela.
- **Mover**: Clique e arraste o texto para mover a janela.
- **Sair**: Feche a janela ou pare o terminal.

## Configurações
Você pode alterar o tamanho da fonte, cor e opacidade no arquivo `config.json`.
