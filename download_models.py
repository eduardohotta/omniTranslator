import shutil
import sys
import os
import urllib.request
import zipfile
import logging
from logging.handlers import RotatingFileHandler

# Configuração de Log com rotação automática
# Limita o log a 1MB e mantém apenas 2 backups (total ~3MB máximo)
log_handler = RotatingFileHandler(
    'download.log',
    maxBytes=1024 * 1024,  # 1MB
    backupCount=2,  # Mantém apenas 2 backups
    encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("Downloader")
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

MODEL_METADATA = {
    "small": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip",
        "zip": "vosk-model-small.zip",
        "folder": "vosk-model-small-pt-0.3"
    },
    "big": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-pt-fb-v0.1.1-20220516_2113.zip",
        "zip": "vosk-model-pt-big.zip",
        "folder": "vosk-model-pt-fb-v0.1.1-20220516_2113"
    }
}
def is_model_installed(model_type):
    if model_type == "google":
        return "google"
    if model_type not in MODEL_METADATA:
        if model_type == "whisper": return "whisper"
        return False
        
    # Check all potential folder locations
    folders_to_check = [f"model_{model_type}"]
    if model_type in MODEL_METADATA:
        folders_to_check.append(MODEL_METADATA[model_type]["folder"])

    for d in folders_to_check:
        if not os.path.exists(d): 
            continue
        
        # Check root of this folder
        f_mdl = os.path.join(d, "final.mdl")
        if os.path.exists(f_mdl):
            size_mb = os.path.getsize(f_mdl) / (1024 * 1024)
            if model_type == "big" and size_mb < 50:
                continue # Skip invalid ones
            return d
            
        # Check one level deep (subfolders)
        try:
            for item in os.listdir(d):
                sub = os.path.join(d, item)
                if os.path.isdir(sub):
                    f_mdl = os.path.join(sub, "final.mdl")
                    if os.path.exists(f_mdl):
                        size_mb = os.path.getsize(f_mdl) / (1024 * 1024)
                        if model_type == "big" and size_mb < 50:
                            continue
                        return d # Return the container dir
        except:
            pass

    return False

def download_file(url, filename, progress_callback=None):
    logger.info(f"Iniciando download: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.getheader('Content-Length', 0))
            download_size = 0
            logger.info(f"Tamanho total detectado: {total_size} bytes")
            
            with open(filename, 'wb') as out_file:
                chunk_size = 1024 * 1024 # 1MB chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    download_size += len(chunk)
                    if progress_callback and total_size > 0:
                        percent = int((download_size / total_size) * 100)
                        progress_callback(percent)
                        
        logger.info(f"Download concluído com sucesso: {filename}")
    except Exception as e:
        logger.error(f"Erro no download de {url}: {str(e)}")
        raise

def unzip_file(zip_path, extract_to, progress_callback=None):
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            total_files = len(files)
            for i, file in enumerate(files):
                zip_ref.extract(file, extract_to)
                if progress_callback and i % 10 == 0:
                    # Map extraction to 100-200% or just keep at 100 with text
                    percent = int((i / total_files) * 100)
                    # We send a special value or just handle it in the callback
                    # For now, let's just finish the download at 100 and extraction is silent or logged
                    pass
    except Exception as e:
        print(f"Extraction error: {e}")
        raise
    print("Extraction complete.")

def setup_vosk(model_type="small", progress_callback=None):
    if model_type not in MODEL_METADATA:
        print(f"Unknown model type: {model_type}")
        return None
        
    meta = MODEL_METADATA[model_type]
    target_dir = f"model_{model_type}"
    
    if is_model_installed(model_type):
        return f"model_{model_type}", "OK"
    
    # Limpa tentativas anteriores corrompidas (0 bytes)
    if os.path.exists(meta["zip"]):
        if os.path.getsize(meta["zip"]) < 100:
            logger.info(f"Removendo zip corrompido ou vazio: {meta['zip']}")
            os.remove(meta["zip"])
    
    target_dir = f"model_{model_type}"
    if os.path.exists(target_dir):
        # If it reached here but is_model_installed returned False, it's invalid
        print(f"Model at {target_dir} is invalid or incomplete. Removing...")
        shutil.rmtree(target_dir)


    print(f"Setting up Vosk model type: {model_type}...")
    
    logger.info(f"Configurando modelo Vosk: {model_type}")
    
    try:
        download_file(meta["url"], meta["zip"], progress_callback)
        
        # Cria a pasta final imediatamente para extrair nela
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # Extração direta na pasta alvo para economizar espaço
        logger.info(f"Extraindo diretamente em {target_dir}...")
        unzip_file(meta["zip"], target_dir, progress_callback)
        
        # Deleta o zip o mais rápido possível para liberar espaço
        if os.path.exists(meta["zip"]):
            logger.info("Removendo arquivo ZIP para liberar espaço.")
            os.remove(meta["zip"])

        # Se houver uma pasta interna (comum em zips do Vosk), movemos os arquivos para cima
        # model_big/vosk-model-pt-.../files -> model_big/files
        inner_folder = os.path.join(target_dir, meta["folder"])
        if os.path.exists(inner_folder):
            logger.info(f"Normalizando estrutura: movendo arquivos de {inner_folder} para {target_dir}")
            
            # Movimentação Estrutural interna (FalaBrasil/am)
            am_path = os.path.join(inner_folder, "am")
            if os.path.exists(am_path):
                for item in os.listdir(am_path):
                    shutil.move(os.path.join(am_path, item), os.path.join(inner_folder, item))

            # Sobe tudo da inner_folder para target_dir
            for item in os.listdir(inner_folder):
                s = os.path.join(inner_folder, item)
                d = os.path.join(target_dir, item)
                if os.path.exists(d):
                    if os.path.isdir(d): shutil.rmtree(d)
                    else: os.remove(d)
                shutil.move(s, d)
            
            # Remove a pasta agora vazia
            try: shutil.rmtree(inner_folder)
            except: pass

        logger.info(f"Setup concluído com sucesso em {target_dir}")
        return target_dir, "OK"
            
    except Exception as e:
        err_msg = str(e)
        if "Errno 28" in err_msg:
            err_msg = "Espaço insuficiente em disco (HD Cheio)."
        
        logger.error(f"Erro fatal no setup_vosk: {err_msg}")
        
        # Cleanup general on failure
        if os.path.exists(meta["zip"]):
            try: os.remove(meta["zip"])
            except: pass
            
        return None, err_msg

def setup_argos():
    print("WARNING: Offline translation (Argos) is disabled.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--small", action="store_true")
    parser.add_argument("--big", action="store_true")
    args = parser.parse_args()

    if not args.small and not args.big:
         setup_vosk("small")
         setup_vosk("big")
    else:
        if args.small: setup_vosk("small")
        if args.big: setup_vosk("big")
    setup_argos()
