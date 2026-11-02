from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent / "assets"
OUT.mkdir(exist_ok=True)
S = 512
im = Image.new("RGBA", (S, S), (5, 13, 29, 255))
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse((48, 48, 464, 464), fill=(0, 174, 255, 95))
glow = glow.filter(ImageFilter.GaussianBlur(35))
im = Image.alpha_composite(im, glow)
d = ImageDraw.Draw(im)
d.ellipse((42, 42, 470, 470), outline=(0, 190, 255, 255), width=13)
d.ellipse((64, 64, 448, 448), outline=(27, 91, 157, 255), width=5)
# Cabeça robótica estilizada
d.rounded_rectangle((132, 112, 380, 390), radius=88, fill=(173, 199, 220, 255), outline=(28, 220, 255, 255), width=12)
d.rounded_rectangle((158, 146, 354, 348), radius=66, fill=(5, 17, 35, 255), outline=(65, 112, 151, 255), width=7)
# Laterais / fones
d.rounded_rectangle((92, 198, 160, 315), radius=28, fill=(30, 92, 137, 255), outline=(0, 210, 255, 255), width=8)
d.rounded_rectangle((352, 198, 420, 315), radius=28, fill=(30, 92, 137, 255), outline=(0, 210, 255, 255), width=8)
# Olhos
d.rounded_rectangle((190, 222, 250, 253), radius=15, fill=(0, 222, 255, 255))
d.rounded_rectangle((264, 222, 324, 253), radius=15, fill=(0, 222, 255, 255))
d.arc((206, 275, 306, 333), 10, 170, fill=(0, 174, 255, 255), width=8)
# Núcleo
d.ellipse((224, 366, 288, 430), fill=(0, 30, 55, 255), outline=(0, 200, 255, 255), width=8)
d.ellipse((242, 384, 270, 412), fill=(0, 225, 255, 255))
# Brilho final
im = im.resize((256, 256), Image.Resampling.LANCZOS)
im.save(OUT / "jarvis.png")
im.save(OUT / "jarvis.ico", format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Ícones criados em", OUT)
