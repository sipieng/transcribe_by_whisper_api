"""
音频转录工具

这个脚本用于将音频文件转录为SRT字幕文件。主要功能包括：
1. 支持多种音频格式（mp3, m4a, wav等）
2. 自动处理大于25MB的音频文件
   - 先尝试转换为低码率MP3
   - 如果仍然过大，则进行无损分割
3. 使用OpenAI的Whisper API进行转录
4. 自动处理时间戳，确保分段转录后的字幕时间正确
"""

from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量

from openai import OpenAI
from pydub import AudioSegment
import os
import re
from config import OPENAI_CONFIG, AUDIO_CONFIG, OUTPUT_CONFIG
import subprocess

# 初始化OpenAI客户端
client = OpenAI(
    base_url=OPENAI_CONFIG["base_url"],
    api_key=OPENAI_CONFIG["api_key"]
)

def get_audio_format(file_path):
    """
    检测音频文件格式
    
    Args:
        file_path: 音频文件路径
    
    Returns:
        str: 音频文件格式（不含点号），如 'mp3', 'm4a'
    """
    extension = os.path.splitext(file_path)[1].lower()
    return extension[1:]  # 移除点号

def load_audio(file_path):
    """
    根据文件格式加载音频
    
    Args:
        file_path: 音频文件路径
    
    Returns:
        AudioSegment: pydub的音频对象
    
    Raises:
        ValueError: 当音频格式不支持或缺少解码器时抛出
    """
    audio_format = get_audio_format(file_path)
    print(f"正在加载{audio_format}格式的音频文件...")
    
    if audio_format == "mp3":
        return AudioSegment.from_mp3(file_path)
    elif audio_format == "m4a":
        return AudioSegment.from_file(file_path, format="m4a")
    elif audio_format == "wav":
        return AudioSegment.from_wav(file_path)
    else:
        # 对于其他格式，尝试使用通用加载方法
        try:
            return AudioSegment.from_file(file_path, format=audio_format)
        except:
            raise ValueError(f"不支持的音频格式或缺少解码器: {audio_format}")

def split_audio(audio_file_path):
    """
    使用ffmpeg无损分割音频文件
    
    Args:
        audio_file_path: 音频文件路径
    
    Returns:
        list: 分割后的音频文件路径列表
    """
    print("\n=== 开始音频分割 ===")
    # 确保输出目录存在
    os.makedirs(OUTPUT_CONFIG["segments_dir"], exist_ok=True)
    os.makedirs(OUTPUT_CONFIG["srt_dir"], exist_ok=True)
    
    # 获取音频总时长（秒）
    print("正在获取音频时长...")
    probe_cmd = [
        "ffprobe",  # 使用ffprobe工具
        "-v", "error",
        "-show_entries", "format=duration",  # 获取音频时长
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_file_path
    ]
    duration = float(subprocess.check_output(probe_cmd).decode().strip())
    
    # 计算需要分割的段数
    segment_duration = AUDIO_CONFIG["split_interval"] / 1000  # 转换为秒
    total_segments = (int(duration) + int(segment_duration) - 1) // int(segment_duration)
    segments = []
    
    print(f"音频总时长: {duration:.2f}秒")
    print(f"每段时长: {segment_duration}秒")
    print(f"预计分割为{total_segments}段")
    
    for i in range(0, int(duration), int(segment_duration)):
        segment_path = f"{OUTPUT_CONFIG['segments_dir']}/segment_{i//int(segment_duration)}.mp3"
        
        # 构建ffmpeg命令
        cmd = [
            "ffmpeg",
            "-i", audio_file_path,  # 输入文件
            "-ss", str(i),          # 开始时间点
            "-t", str(segment_duration),  # 持续时间
            "-c", "copy",           # 关键：使用copy模式，实现无损分割
            "-y",                   # 自动覆盖已存在文件
            segment_path            # 输出文件路径
        ]
        
        print(f"\n正在分割第{i//int(segment_duration)+1}/{total_segments}段...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"第{i//int(segment_duration)+1}段分割完成")
            segments.append(segment_path)
        else:
            print(f"警告：第{i//int(segment_duration)+1}段分割可能存在问题")
    
    print("=== 音频分割完成 ===\n")
    return segments


def adjust_srt_timestamps(srt_content, time_offset):
    """
    调整SRT文件的时间戳
    
    Args:
        srt_content: SRT文件内容
        time_offset: 时间偏移量（毫秒）
    
    Returns:
        str: 调整后的SRT内容
    """
    def add_time(time_str, offset_ms):
        # 将时间字符串转换为毫秒
        h, m, s = time_str.split(':')
        s, ms = s.split(',')
        total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        # 添加偏移
        total_ms += offset_ms
        # 转换回时间格式
        h = total_ms // 3600000
        m = (total_ms % 3600000) // 60000
        s = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    # 使用正则表达式匹配时间戳行
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
    
    def replace_timestamps(match):
        start_time = match.group(1)
        end_time = match.group(2)
        new_start = add_time(start_time, time_offset)
        new_end = add_time(end_time, time_offset)
        return f"{new_start} --> {new_end}"

    return re.sub(pattern, replace_timestamps, srt_content)


def convert_to_mp3(input_file):
    """
    使用ffmpeg将音频转换为指定码率的MP3格式
    
    Args:
        input_file: 输入音频文件路径
    
    Returns:
        str: 转换后的MP3文件路径
    """
    print("\n=== 开始音频转换 ===")
    output_path = OUTPUT_CONFIG["converted_audio"]
    
    cmd = [
        "ffmpeg",          # 调用ffmpeg命令
        "-i", input_file,  # 输入文件
        "-b:a", AUDIO_CONFIG["mp3_bitrate"],  # 设置音频比特率
        "-ac", "1",        # 转换为单声道
        "-y",              # 自动覆盖已存在的文件
        output_path        # 输出文件路径
    ]
    
    print(f"正在将音频转换为{AUDIO_CONFIG['mp3_bitrate']}比特率的单声道MP3...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode == 0:
        print("音频转换完成")
    else:
        print("警告：音频转换可能存在问题")
    
    print("=== 音频转换完成 ===\n")
    return output_path

def transcribe_audio(audio_file_path):
    """
    转录音频文件为SRT字幕
    
    Args:
        audio_file_path: 音频文件路径
    """
    # 首先清理之前的输出文件
    clean_output()
    
    print("\n=== 开始音频转录 ===")
    print(f"处理文件: {os.path.basename(audio_file_path)}")
    
    file_size = os.path.getsize(audio_file_path)
    print(f"文件大小: {file_size/1024/1024:.2f}MB")
    
    # 如果文件大于25MB，先尝试转换为低码率MP3
    if file_size > AUDIO_CONFIG["max_file_size"]:
        print(f"文件大小超过25MB，需要进行处理...")
        converted_file = convert_to_mp3(audio_file_path)
        converted_size = os.path.getsize(converted_file)
        print(f"转换后文件大小: {converted_size/1024/1024:.2f}MB")
        
        # 如果转换后的文件仍然超过25MB，则进行分割
        if converted_size > AUDIO_CONFIG["max_file_size"]:
            print(f"转换后的文件仍超过25MB，需要进行分割...")
            segments = split_audio(converted_file)
            all_srt_content = ""
            
            # 转录每个分段
            for i, segment_path in enumerate(segments):
                print(f"\n正在转录第{i+1}/{len(segments)}段...")
                with open(segment_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="srt",
                        language=AUDIO_CONFIG["language"]
                    )
                    
                    # 调整时间戳
                    time_offset = i * AUDIO_CONFIG["split_interval"]
                    adjusted_srt = adjust_srt_timestamps(transcription, time_offset)
                    
                    # 保存分段SRT
                    segment_srt_path = f"{OUTPUT_CONFIG['srt_dir']}/segment_{i}.srt"
                    with open(segment_srt_path, "w", encoding="utf-8") as f:
                        f.write(adjusted_srt)
                    print(f"第{i+1}段转录完成并保存")
                    
                    all_srt_content += adjusted_srt + "\n"
            
            # 保存最终合并的SRT文件
            with open(OUTPUT_CONFIG["final_output"], "w", encoding="utf-8") as f:
                f.write(all_srt_content)
            print(f"\n所有分段已合并到: {OUTPUT_CONFIG['final_output']}")
        else:
            # 转换后的文件小于25MB，直接转录
            print("转换后的文件小于25MB，直接进行转录...")
            with open(converted_file, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="srt",
                    language=AUDIO_CONFIG["language"]
                )
                with open(OUTPUT_CONFIG["final_output"], "w", encoding="utf-8") as f:
                    f.write(transcription)
                print(f"转录完成，已保存到: {OUTPUT_CONFIG['final_output']}")
    else:
        # 原文件小于25MB，直接转录
        print("文件小于25MB，直接进行转录...")
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="srt",
                language=AUDIO_CONFIG["language"]
            )
            with open(OUTPUT_CONFIG["final_output"], "w", encoding="utf-8") as f:
                f.write(transcription)
            print(f"转录完成，已保存到: {OUTPUT_CONFIG['final_output']}")
    
    print("=== 音频转录完成 ===\n")

def clean_output():
    """
    清理所有输出文件和目录
    包括：
    1. segments 目录下的所有音频文件
    2. srt_segments 目录下的所有SRT文件
    3. 转换后的MP3文件
    4. 最终的SRT文件
    """
    print("\n=== 清理输出文件 ===")
    
    # 清理目录中的文件
    for dir_path in [OUTPUT_CONFIG["segments_dir"], OUTPUT_CONFIG["srt_dir"]]:
        if os.path.exists(dir_path):
            # 删除目录中的文件
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                try:
                    os.remove(file_path)
                except PermissionError as e:
                    print(f"删除文件失败（文件可能被占用）: {file_path}")
            
            # 删除空目录
            try:
                os.rmdir(dir_path)
            except PermissionError:
                print(f"删除目录失败（目录可能被占用）: {dir_path}")
            except OSError:
                # 目录不为空，但这种情况应该很少发生
                print(f"删除目录失败（目录不为空）: {dir_path}")
    
    # 清理单个文件
    for file_path in [OUTPUT_CONFIG["converted_audio"], OUTPUT_CONFIG["final_output"]]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except PermissionError:
                print(f"删除文件失败（文件可能被占用）: {file_path}")
    
    print("=== 清理完成 ===\n")


if __name__ == "__main__":

    audio_file_path = r"C:\Users\mike.shen\Desktop\The_Medici_1.m4a"
    transcribe_audio(audio_file_path)
