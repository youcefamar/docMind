import os
import urllib.request

# Default download target: Llama-3.1-8B-Instruct (Q4_K_M quantized GGUF)
MODEL_URL = "https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
OUTPUT_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "llama-3.1-8b-instruct.Q4_K_M.gguf")

def download_gguf():
    if os.path.exists(OUTPUT_PATH):
        print(f"Model already exists at: {OUTPUT_PATH}")
        return

    print(f"Downloading GGUF model from HuggingFace to {OUTPUT_PATH}...")
    print("This may take a few minutes depending on your internet connection (~4.9 GB)...")

    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        print(f"\rDownloading: {percent}% [{count * block_size / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB]", end="")

    try:
        urllib.request.urlretrieve(MODEL_URL, OUTPUT_PATH, reporthook=progress_hook)
        print("\nDownload complete! Local GGUF model is ready.")
    except Exception as e:
        print(f"\nError downloading GGUF model: {e}")
        print("You can manually place any .gguf model file into backend/models/ and set GGUF_MODEL_PATH in your .env file.")

if __name__ == "__main__":
    download_gguf()
