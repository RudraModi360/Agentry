import os, sys, numpy as np, torch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, '.')

from PIL import Image
from transformers import AutoModel, AutoTokenizer

print('Loading raw HF Jina CLIP v2...')
tokenizer = AutoTokenizer.from_pretrained('jinaai/jina-clip-v2', trust_remote_code=True)
hf_model = AutoModel.from_pretrained('jinaai/jina-clip-v2', trust_remote_code=True)
hf_model.eval()

# Check model config for image size
print(f'Model visual config img_size: {getattr(hf_model.vision_model, "img_size", "N/A")}')

# Get a test image
img_dir = 'rag_index/extracted_images'
imgs = sorted([f for f in os.listdir(img_dir) if f.endswith('.png')])
img_path = os.path.join(img_dir, imgs[0])
image = Image.open(img_path).convert('RGB')
print(f'Image size: {image.size}')

# Raw text encoding
text_input = tokenizer(['photosynthesis'], return_tensors='pt', padding=True, truncation=True)
with torch.no_grad():
    text_out = hf_model.get_text_features(**text_input)
    text_emb = text_out[0].numpy()
    text_emb = text_emb / np.linalg.norm(text_emb)

# Raw image encoding - use the model's own processor or resize manually to 512x512
# Try to get processor from the model's config
from torchvision import transforms
transform = transforms.Compose([
    transforms.Resize((512, 512), interpolation=transforms.InterpolationMode.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.48145466, 0.4578275, 0.40821073], std=[0.26862954, 0.26130258, 0.27577711]),
])
img_tensor = transform(image).unsqueeze(0)

with torch.no_grad():
    img_out = hf_model.get_image_features(pixel_values=img_tensor)
    img_emb = img_out[0].numpy()
    img_emb = img_emb / np.linalg.norm(img_emb)

sim = float(np.dot(text_emb, img_emb))
print(f'Raw HF model text-image sim: {sim:.4f}')
print(f'Text norm: {np.linalg.norm(text_emb):.4f}, Image norm: {np.linalg.norm(img_emb):.4f}')

# Also test multiple images
print()
print('=== RAW HF MODEL MULTI-IMAGE TEST ===')
embs = []
for i in range(3):
    path = os.path.join(img_dir, imgs[i])
    img = Image.open(path).convert('RGB')
    img_t = transform(img).unsqueeze(0)
    with torch.no_grad():
        out = hf_model.get_image_features(pixel_values=img_t)
        e = out[0].numpy()
        e = e / np.linalg.norm(e)
    embs.append(e)
    print(f'  {imgs[i]}: norm={np.linalg.norm(e):.4f}')

# Text-Image sims
queries = ['photosynthesis', 'heart', 'cell structure', 'chloroplast']
print()
print('=== RAW HF TEXT-IMAGE SIMS ===')
for q in queries:
    t_in = tokenizer([q], return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        t_out = hf_model.get_text_features(**t_in)
        t_emb = t_out[0].numpy()
        t_emb = t_emb / np.linalg.norm(t_emb)
    sims = [float(np.dot(t_emb, e)) for e in embs]
    print(f'  "{q}": {[f"{s:.4f}" for s in sims]}')
