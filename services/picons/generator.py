
from PIL import Image, ImageDraw, ImageFont

def generate_picon(text, color, out):
    img = Image.new("RGB", (1024,1024), color)
    d = ImageDraw.Draw(img)
    d.text((512,512), text, fill="white", anchor="mm")
    img.save(out)
