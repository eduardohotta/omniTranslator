#!/bin/bash

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "ERRO: Versao nao especificada!"
    echo "Uso: ./build_and_release.sh <versao>"
    echo "Exemplo: ./build_and_release.sh 1.2.0"
    exit 1
fi

echo "========================================"
echo "   Build + Release v$VERSION"
echo "========================================"

# 0. Atualizar RELEASE_NOTES.md
echo "[0/6] Atualizando RELEASE_NOTES.md..."
cat > RELEASE_NOTES.md << EOF
## OmniTranslator v$VERSION

### Correcoes
- Correcao de segmentation fault no engine Google
- Thread-safe processing

### Melhorias
- Schema de configuracao com Pydantic
- Sistema de logging estruturado
- Suite completa de testes

### Checksum SHA256

Execute para verificar:
~~~
certutil -hashfile OmniTranslator.exe SHA256
~~~
EOF

# 1. Limpar build anterior
echo "[1/6] Limpando build anterior..."
rm -rf dist build

# 2. Build
echo "[2/6] Compilando exe..."
python -m PyInstaller OmniTranslator.spec --clean
if [ $? -ne 0 ]; then
    echo "ERRO no build!"
    exit 1
fi

# 3. Gerar SHA256
echo "[3/6] Gerando SHA256..."
sha256sum "dist/OmniTranslator.exe" > "dist/OmniTranslator.exe.sha256"

# 4. Criar tag
echo "[4/6] Criando tag v$VERSION..."
git tag -d v$VERSION 2>/dev/null
git tag v$VERSION

# 5. Commit
echo "[5/6] Fazendo commit..."
git add -A
git commit -m "Release v$VERSION" || echo "Nada para commit"

# 6. Push + Release
echo "[6/6] Enviando para GitHub..."
git push origin main --tags
gh release create v$VERSION \
  --title "OmniTranslator v$VERSION" \
  --notes-file RELEASE_NOTES.md \
  "dist/OmniTranslator.exe" \
  "dist/OmniTranslator.exe.sha256"

echo ""
echo "========================================"
echo "   SUCESSO!"
echo "========================================"
echo "Versao:  v$VERSION"
echo "Release: https://github.com/eduardohotta/omniTranslator/releases/tag/v$VERSION"
