import os
import shutil

def fix_model_structure(model_path="model"):
    print(f"Checking model structure in {model_path}...")
    
    # Check for am/final.mdl (common in FalaBrasil models)
    am_final = os.path.join(model_path, "am", "final.mdl")
    root_final = os.path.join(model_path, "final.mdl")
    
    if os.path.exists(am_final) and not os.path.exists(root_final):
        print("Found final.mdl in 'am' subdirectory. Moving to root...")
        try:
            shutil.move(am_final, root_final)
            print("Moved final.mdl successfully.")
        except Exception as e:
            print(f"Error moving file: {e}")
            
    # Check for conf/mfcc.conf
    conf_mfcc = os.path.join(model_path, "conf", "mfcc.conf")
    if not os.path.exists(conf_mfcc):
        print("Warning: conf/mfcc.conf not found. This might be an issue.")
    
    # Check for conf/model.conf
    conf_model = os.path.join(model_path, "conf", "model.conf")
    if not os.path.exists(conf_model):
        print("Warning: conf/model.conf not found. This might be an issue.")
        
    # Check if graph exists
    graph_dir = os.path.join(model_path, "graph")
    if os.path.exists(graph_dir):
        # Vosk sometimes needs HCLG.fst
        # But usually just having final.mdl and confs is enough for basic load
        pass
        
    print("Structure check complete.")
    if os.path.exists(root_final):
        print("Model appears to be ready for Vosk.")
    else:
        print("CRITICAL: final.mdl still not found in root. Model will fail to load.")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "model"
    fix_model_structure(target)

