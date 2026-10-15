"""vlm_probe.py CROP.png [model] : ask a small local VLM to describe differences between the left (Revit) and middle (ours) panels of a crop_pair image."""
import sys, time, torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText
mid = sys.argv[2] if len(sys.argv) > 2 else 'HuggingFaceTB/SmolVLM-256M-Instruct'
torch.set_num_threads(4)
proc = AutoProcessor.from_pretrained(mid); model = AutoModelForImageTextToText.from_pretrained(mid, torch_dtype=torch.float32).eval()
im = Image.open(sys.argv[1]).convert('RGB'); w, h = im.size; a, b = im.crop((0, 0, w//3, h)), im.crop((w//3, 0, 2*w//3, h))
msgs = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'image'}, {'type': 'text', 'text': 'Image 1 is an architectural drawing by Revit. Image 2 should show the same drawing. List text labels or symbols that appear in image 1 but are missing in image 2.'}]}]
prompt = proc.apply_chat_template(msgs, add_generation_prompt=True)
inp = proc(text=prompt, images=[a, b], return_tensors='pt')
t = time.time()
with torch.no_grad(): out = model.generate(**inp, max_new_tokens=80, do_sample=False)
print(round(time.time() - t, 1), 's:', proc.batch_decode(out[:, inp['input_ids'].shape[1]:], skip_special_tokens=True)[0])
