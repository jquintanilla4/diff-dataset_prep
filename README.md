# Dataset Preparation Tools

Utilities and scripts to build high‑quality image–caption datasets. This repo covers:
- Image caption generation with multiple models/APIs
- Caption cleanup and normalization
- Helper tools for resizing, renaming, find/replace, trigger-word removal, and organizing unpaired files

---

## Quick Start

- Python 3.9+ recommended (used 3.11)
- Create a virtual environment and install deps

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Extras used by various scripts:
pip install google-generativeai openai python-dotenv tqdm torch qwen-vl-utils ollama lmstudio
```

Notes:
- Install PyTorch for your platform per the official instructions if the base `pip install torch` fails.
- First runs of HF models will download weights (can be large); ensure sufficient disk/VRAM.

### Environment variables
Create a `.env` file in the repo root with your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
```

Scripts that call Gemini use either:
- `google.generativeai` directly, or
- `openai` client with `base_url=https://generativelanguage.googleapis.com/v1beta/openai/`

---

## Conventions and Outputs

- Image captions are saved alongside images as `{basename}.txt`.
- Gemini 1-shot single-image generation writes `p_{basename}.txt`.
- Cleanup scripts write to a `cleaned/` subfolder with `*_c.txt` filenames.
- Batch Gemini (legacy) drops `batch_*.txt` and `raw_response_batch_*.json`, then moves them to `results/`.
- Splitter (legacy) writes `descriptions/` and `prompts/` subfolders and logs to `zero_processed_files.txt`.
- `tools/find_solo.py` can move unpaired files to `unpaired/`.

---

## Typical Workflow

1) Generate captions (choose one model):
- `image_captions_gemini_1shotSingle.py` (Gemini API)
- `image_captions_florence.py` (HF: Florence-2-Flux-Large)
- `image_captions_moondream.py` (HF: moondream2)
- `image_captions_qwen25vl_cuda.py` (HF: Qwen2-VL; CUDA)
- `image_captions_qwen25vl_lmstudio.py` (LM Studio; Qwen2.5-VL 7B instruct)

2) Clean captions:
- `caption_cleanup_gemini.py` (general cleanup)
- `caption_cleanup_gemini_pass2.py` (optional second pass; removes depth/palette/atmosphere sentences)

3) Use tools as needed:
- Resize, rename, find/replace, trigger-word removal, organize unpaired files

---

## Scripts

### Caption Cleanup

- `caption_cleanup_gemini.py`
  - Reads `*.txt` in a folder, cleans with Gemini via OpenAI-compatible client.
  - Writes to `cleaned/{name}_c.txt`. Skips non-empty existing outputs.
  - Prompts for folder path and optional prepend token (e.g., "arcane oil").

- `caption_cleanup_gemini_pass2.py`
  - Second pass. Removes sentences about depth, color palette (as a palette), and atmosphere.
  - Same I/O behavior as above; writes to `cleaned/{name}_c.txt`.

Usage (both):
```bash
python caption_cleanup_gemini.py
python caption_cleanup_gemini_pass2.py
```

### Caption Generation

- `image_captions_gemini_1shotSingle.py`
  - Uses the Gemini API (with an internal one‑shot image example) to analyze each image and write `p_{basename}.txt`.
  - Prompts for folder path and max images (cap 3000). Retries with exponential backoff.
  - Note: The script references a local sample image path for the one‑shot example. Update it to a valid path on your machine.

- `image_captions_florence.py`
  - HF transformers model: `gokaygokay/Florence-2-Flux-Large`. Device auto-detect (CUDA/MPS/CPU).
  - Saves `{basename}.txt`. Removes common starters using `tools.caption_starters.clean_caption()`.

- `image_captions_moondream.py`
  - HF transformers model: `vikhyatk/moondream2` (revision `2024-08-26`). Device auto-detect.
  - Saves `{basename}.txt`. Removes common starters.

- `image_captions_qwen25vl_cuda.py`
  - HF `Qwen/Qwen2-VL-7B-Instruct` with `qwen_vl_utils`. CUDA required.
  - Saves `{basename}.txt`. Cleans common starters.

- `image_captions_qwen25vl_lmstudio.py`
  - Uses `lmstudio` Python package with model `mlx-community/qwen2.5-vl-7b-instruct`.
  - Saves `{basename}.txt`. Cleans common starters.

Legacy (Ollama-based):
- `legacy/image_captions_llamavision.py` (model `llama3.2-vision:11b-instruct-q8_0`)
- `legacy/image_captions_llava.py` (model `llava:34b`)
- `legacy/caption_cleanup_llama3-8B.py` (cleanup using `llama3.1:8b-instruct-fp16`)

Usage (generation):
```bash
python image_captions_gemini_1shotSingle.py
python image_captions_florence.py
python image_captions_moondream.py
python image_captions_qwen25vl_cuda.py
python image_captions_qwen25vl_lmstudio.py
```

### Tools

- `tools/image_resize.py`
  - Interactive image resizing. Choose one: resize largest dimension, exact height, or exact width; then enter target pixels.
  - Skips images that already satisfy the chosen constraint.

- `tools/rename_files.py`
  - Renames files in a folder to `image_0001.ext`, `image_0002.ext`, … (skips already‑matching files). Picks the next available index.

- `tools/findreplace_word.py`
  - Find and replace a word across all `*.txt` in a folder.

- `tools/triggerword_removal.py`
  - Removes the first occurrence of trigger words `"BBCDFL, "` and `"WSBBC, "` across all `*.txt`.

- `tools/find_solo.py`
  - Reports .png files without matching .txt (and vice versa). Optionally moves unpaired files to an `unpaired/` subfolder.

- `tools/gemini_ratelimit_test.py`
  - Quick sanity check for Gemini API key/rate limits.

Usage (tools):
```bash
python tools/image_resize.py
python tools/rename_files.py
python tools/findreplace_word.py
python tools/triggerword_removal.py
python tools/find_solo.py
python tools/gemini_ratelimit_test.py
```

---

## Example Pipeline

```bash
# 1) Generate captions
python image_captions_florence.py

# 2) Clean captions (first pass)
python caption_cleanup_gemini.py

# 3) Optional: refine captions (second pass)
python caption_cleanup_gemini_pass2.py

---

## Troubleshooting & Notes

- Hugging Face models may require significant VRAM; reduce image size or switch models if OOM.
- Qwen2‑VL CUDA path requires a working CUDA setup and `qwen-vl-utils`.
- Gemini scripts use exponential backoff to mitigate rate limits.
- If `image_captions_gemini_1shotSingle.py` fails early, ensure the one‑shot sample image path points to a valid local image.
- On macOS with Apple Silicon, Florence/Moondream can run with MPS; first load may be slower due to compilation.

---

## License
Internal tooling for dataset preparation.