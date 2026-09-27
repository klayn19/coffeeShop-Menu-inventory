import os
import shutil
from PIL import Image, ImageDraw

project_dir = r"C:\Users\klayn\Desktop\COFFEE MENU"
images_dir = os.path.join(project_dir, "images")
os.makedirs(images_dir, exist_ok=True)

# Copy the 6 generated images
generated = [
    (r"C:\Users\klayn\.gemini\antigravity\brain\8b00d273-bd48-4324-a78e-3d64c16b55db\hot_coffee_1775427977479.png", "C001.png"),
    (r"C:\Users\klayn\.gemini\antigravity\brain\8b00d273-bd48-4324-a78e-3d64c16b55db\espresso_1775427995910.png", "C002.png"),
    (r"C:\Users\klayn\.gemini\antigravity\brain\8b00d273-bd48-4324-a78e-3d64c16b55db\cappuccino_1775428045588.png", "C003.png"),
    (r"C:\Users\klayn\.gemini\antigravity\brain\8b00d273-bd48-4324-a78e-3d64c16b55db\caramel_latte_1775428056982.png", "C004.png"),
    (r"C:\Users\klayn\.gemini\antigravity\brain\8b00d273-bd48-4324-a78e-3d64c16b55db\macchiato_1775428087399.png", "C005.png"),
    (r"C:\Users\klayn\.gemini\antigravity\brain\8b00d273-bd48-4324-a78e-3d64c16b55db\caramel_macchiato_1775428100932.png", "C006.png"),
]

for src, dst_name in generated:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(images_dir, dst_name))
        
# For the remaining 2, generate simple placeholders
def create_placeholder(text, filename):
    img = Image.new('RGB', (250, 250), color = (111, 78, 55))
    d = ImageDraw.Draw(img)
    d.text((10,100), text, fill=(245,230,211))
    img.save(os.path.join(images_dir, filename))

create_placeholder('Iced Capp Placeholder', 'C007.png')
create_placeholder('Iced Coffee Placeholder', 'C008.png')

print("Images copied and placeholders generated.")
