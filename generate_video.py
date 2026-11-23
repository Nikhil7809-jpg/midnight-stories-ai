import os
import json
import subprocess
from pathlib import Path
from google import genai
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

Path("output").mkdir(exist_ok=True)

prompt = """
Write an original, suspenseful horror story for a YouTube Short.
Length: 130-160 words.
Use a powerful opening hook and a surprising ending.
Return only the story, no explanations.
"""

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt
)

story = response.text.strip()

with open("output/story.txt", "w", encoding="utf-8") as f:
    f.write(story)

title = "THE LAST KNOCK"
audio_path = "output/narration.mp3"
video_path = "output/midnight_story.mp4"

gTTS(text=story, lang="en", slow=False).save(audio_path)

# Create a vertical cinematic background
img = Image.new("RGB", (1080, 1920), (12, 8, 24))
draw = ImageDraw.Draw(img)

for y in range(1920):
    shade = int(12 + 20 * y / 1920)
    draw.line((0, y, 1080, y), fill=(shade, 5, shade + 12))

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(font_path, 76)

draw.text((90, 700), title, font=font, fill=(255, 220, 220))
draw.text((90, 830), "A MIDNIGHT STORY", font=font, fill=(180, 160, 200))

background = "output/background.png"
img.save(background)

# Generate captions as timed subtitle segments
words = story.split()
segments = []
chunk_size = 7

for i in range(0, len(words), chunk_size):
    segment = " ".join(words[i:i + chunk_size])
    start = i / 2.4
    end = (i + chunk_size) / 2.4
    segments.append((start, end, segment))

def timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}".replace(".", ",")

with open("output/captions.srt", "w", encoding="utf-8") as f:
    for number, (start, end, text) in enumerate(segments, 1):
        f.write(
            f"{number}\n"
            f"{timestamp(start)} --> {timestamp(end)}\n"
            f"{text}\n\n"
        )

subprocess.run([
    "ffmpeg", "-y",
    "-loop", "1", "-i", background,
    "-i", audio_path,
    "-vf",
    "scale=1080:1920,subtitles=output/captions.srt:"
    "force_style='FontSize=18,PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00000000,BorderStyle=1,Outline=2,"
    "Alignment=2,MarginV=180'",
    "-c:v", "libx264",
    "-tune", "stillimage",
    "-c:a", "aac",
    "-b:a", "128k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    "-movflags", "+faststart",
    video_path
], check=True)

print("Video created:", video_path)
