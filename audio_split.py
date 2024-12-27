from pydub import AudioSegment
import os

# 创建输出目录
output_dir = "segments"
os.makedirs(output_dir, exist_ok=True)

# 读取并分割音频
song = AudioSegment.from_mp3("t.mp3")
ten_seconds = 10 * 1000

for i in range(0, len(song), ten_seconds):
    segment = song[i:i+ten_seconds]
    output_file = os.path.join(output_dir, f"segment_{i//ten_seconds}.mp3")
    segment.export(output_file, format="mp3")
    print(f"已保存片段: {output_file}")