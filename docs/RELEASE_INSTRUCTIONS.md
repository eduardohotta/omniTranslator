# Instruções para Criar Release v1.1.0

## Opção 1: Usar o Script Automático (Recomendado)

1. Execute o arquivo `create_release.bat`
2. Se for a primeira vez, o script pedirá para fazer login no GitHub
3. Siga as instruções:
   - Escolha: **GitHub.com**
   - Escolha: **HTTPS**
   - Escolha: **Login with a web browser** (mais fácil)
4. O script criará a release automaticamente

## Opção 2: Criar pelo Site do GitHub (Manual)

Se preferir criar pelo site:

1. Acesse: https://github.com/eduardohotta/omniTranslator/releases
2. Clique em **"Draft a new release"**
3. Em "Choose a tag", selecione **v1.1.0**
4. Título: **OmniTranslator v1.1.0**
5. Cole o conteúdo de `RELEASE_NOTES.md` na descrição
6. Arraste os arquivos para a área de upload:
   - `dist/OmniTranslator.exe` (271 MB)
   - `dist/OmniTranslator.exe.sha256`
7. Clique em **"Publish release"**

## Opção 3: Usar Token de Acesso (Para Automação)

1. Crie um token em: https://github.com/settings/tokens
   - Escopo necessário: `repo` (full control)
2. Execute:
   ```cmd
   set GH_TOKEN=seu_token_aqui
   create_release.bat
   ```

## Arquivos da Release

- **OmniTranslator.exe** (271 MB) - Executável principal
- **OmniTranslator.exe.sha256** - Checksum para verificação de integridade

## Verificação

Após criar, acesse:
https://github.com/eduardohotta/omniTranslator/releases/tag/v1.1.0
