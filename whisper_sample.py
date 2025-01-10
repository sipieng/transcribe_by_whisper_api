"""
音频转录工具

这个脚本用于将音频文件转录为字幕或文本文件。主要功能包括：
1. 支持多种音频格式（mp3, m4a, wav等）
2. 自动处理大于25MB的音频文件
   - 先尝试转换为低码率MP3
   - 如果仍然过大，则进行无损分割
3. 使用OpenAI的Whisper API进行转录
4. 自动处理时间戳（适用于字幕格式）
5. 自动清理临时文件
"""

from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量

from openai import OpenAI
from pydub import AudioSegment
import os
import re
from config import OPENAI_CONFIG, AUDIO_CONFIG, OUTPUT_CONFIG
from text_processor import process_text
import subprocess
import time

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

def get_audio_info(audio_file_path):
    """
    获取音频文件的时长和比特率
    
    Args:
        audio_file_path: 音频文件路径
    
    Returns:
        tuple: (duration, bitrate)，分别为时长（秒）和比特率（bps）
    """
    print("正在获取音频信息...")
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "format=duration,bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_file_path
    ]
    result = subprocess.check_output(probe_cmd).decode().strip().split('\n')
    duration = float(result[0])
    # 某些音频可能没有比特率信息，此时使用估算值
    try:
        bitrate = int(result[1])
    except (IndexError, ValueError):
        file_size = os.path.getsize(audio_file_path)
        bitrate = int((file_size * 8) / duration)  # 估算比特率
    
    print(f"音频总时长: {duration:.2f}秒")
    print(f"音频比特率: {bitrate/1000:.0f}kbps")
    return duration, bitrate

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
    os.makedirs(OUTPUT_CONFIG["audio_chunks_dir"], exist_ok=True)
    os.makedirs(OUTPUT_CONFIG["trans_chunks_dir"], exist_ok=True)
    
    # 获取音频时长
    duration, _ = get_audio_info(audio_file_path)
    
    # 计算需要分割的段数
    segment_duration = AUDIO_CONFIG["split_interval"] / 1000  # 转换为秒
    total_segments = (int(duration) + int(segment_duration) - 1) // int(segment_duration)
    segments = []
    
    print(f"音频总时长: {duration:.2f}秒")
    print(f"每段时长: {segment_duration}秒")
    print(f"预计分割为{total_segments}段")
    
    for i in range(0, int(duration), int(segment_duration)):
        segment_path = f"{OUTPUT_CONFIG['audio_chunks_dir']}/segment_{i//int(segment_duration)}.mp3"
        
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

def add_time(time_str, offset_ms):
    """
    为时间字符串添加偏移量
    
    Args:
        time_str: 时间字符串，格式为 "HH:MM:SS,mmm"
        offset_ms: 要添加的时间偏移量（毫秒）
    
    Returns:
        str: 调整后的时间字符串，格式与输入相同
    """
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

def adjust_timestamps(content, time_offset):
    """
    调整字幕文件的时间戳
    
    Args:
        content: 字幕文件内容
        time_offset: 时间偏移量（毫秒）
    
    Returns:
        str: 调整后的字幕内容
    
    Note:
        目前支持 SRT 和 VTT 格式的时间戳调整
    """
    if AUDIO_CONFIG["response_format"] not in ["srt", "vtt"]:
        return content
        
    # 使用正则表达式匹配时间戳行
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
    
    def replace_timestamps(match):
        start_time = match.group(1)
        end_time = match.group(2)
        new_start = add_time(start_time, time_offset)
        new_end = add_time(end_time, time_offset)
        return f"{new_start} --> {new_end}"

    return re.sub(pattern, replace_timestamps, content)

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

def clean_output():
    """清理所有输出文件和目录"""
    print("\n=== 清理输出文件 ===")
    
    # 清理目录中的文件
    for dir_path in [OUTPUT_CONFIG["audio_chunks_dir"], 
                    OUTPUT_CONFIG["trans_chunks_dir"]]:  # 使用新的目录名
        if os.path.exists(dir_path):
            # 删除目录中的文件
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                for _ in range(3):  # 最多尝试3次
                    try:
                        os.remove(file_path)
                        break
                    except PermissionError:
                        time.sleep(0.1)  # 等待100毫秒
                    except FileNotFoundError:
                        break  # 文件已经被删除，跳过
            
            # 删除空目录
            for _ in range(3):  # 最多尝试3次
                try:
                    os.rmdir(dir_path)
                    break
                except PermissionError:
                    time.sleep(0.1)  # 等待100毫秒
                except OSError as e:
                    if "目录不为空" in str(e):
                        print(f"删除目录失败（目录不为空）: {dir_path}")
                    break
                except FileNotFoundError:
                    break  # 目录已经被删除，跳过
    
    # 清理转换后的MP3文件
    if os.path.exists(OUTPUT_CONFIG["converted_audio"]):
        for _ in range(3):  # 最多尝试3次
            try:
                os.remove(OUTPUT_CONFIG["converted_audio"])
                break
            except PermissionError:
                time.sleep(0.1)  # 等待100毫秒
            except FileNotFoundError:
                break  # 文件已经被删除，跳过
    
    print("=== 清理完成 ===\n")

def get_supported_audio_files(path):
    """
    获取目录下所有支持的音频文件
    
    Args:
        path: 文件或目录路径
    
    Returns:
        list: 支持的音频文件路径列表
    """
    supported_formats = ['mp3', 'm4a', 'wav']
    
    if os.path.isfile(path):
        # 如果是文件，检查是否为支持的格式
        if get_audio_format(path) in supported_formats:
            return [path]
        return []
    
    # 如果是目录，收集所有支持的音频文件
    audio_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                audio_files.append(os.path.join(root, file))
    return sorted(audio_files)  # 排序确保处理顺序一致

def get_output_extension():
    """
    根据配置的响应格式返回对应的文件扩展名
    
    Returns:
        str: 文件扩展名（包含点号）
    """
    format_extensions = {
        "text": ".txt",
        "srt": ".srt",
        "json": ".json",
        "verbose_json": ".json",
        "vtt": ".vtt"
    }
    return format_extensions.get(AUDIO_CONFIG["response_format"], ".txt")  # 默认使用 .txt

def needs_timestamp_adjustment(response_format):
    """
    检查指定的响应格式是否需要时间戳调整
    
    Args:
        response_format: Whisper API的响应格式
    
    Returns:
        bool: 如果需要调整时间戳返回True，否则返回False
    """
    return response_format in ["srt", "vtt"]

def transcribe_audio(audio_path):
    """转录音频文件"""
    try:
        # 开始处理前清理所有临时文件
        clean_output()
        
        # 获取要处理的音频文件列表
        audio_files = get_supported_audio_files(audio_path)
        if not audio_files:
            print(f"未找到支持的音频文件: {audio_path}")
            return
        
        # 确保所有必要的目录都存在
        for dir_path in [OUTPUT_CONFIG["audio_chunks_dir"], 
                        OUTPUT_CONFIG["trans_chunks_dir"],
                        OUTPUT_CONFIG["transcripts_dir"]]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 处理每个音频文件
        total_files = len(audio_files)
        for index, audio_file in enumerate(audio_files, 1):
            print(f"\n=== 处理文件 {index}/{total_files}: {os.path.basename(audio_file)} ===")
            
            # 设置输出文件路径，使用动态扩展名
            output_filename = f"{os.path.splitext(os.path.basename(audio_file))[0]}{get_output_extension()}"
            output_path = os.path.join(OUTPUT_CONFIG["transcripts_dir"], output_filename)
            
            # 处理单个文件
            file_size = os.path.getsize(audio_file)
            print(f"文件大小: {file_size/1024/1024:.2f}MB")
            
            try:
                if file_size > AUDIO_CONFIG["max_file_size"]:
                    print(f"文件大小超过25MB，需要进行处理...")
                    converted_file = convert_to_mp3(audio_file)
                    converted_size = os.path.getsize(converted_file)
                    print(f"转换后文件大小: {converted_size/1024/1024:.2f}MB")
                    
                    # 如果转换后的文件仍然超过25MB，则进行分割
                    if converted_size > AUDIO_CONFIG["max_file_size"]:
                        print(f"转换后的文件仍超过25MB，需要进行分割...")
                        segments = split_audio(converted_file)
                        all_content = ""
                        
                        # 转录每个分段
                        for i, segment_path in enumerate(segments):
                            print(f"\n正在转录第{i+1}/{len(segments)}段...")
                            with open(segment_path, "rb") as audio_file_obj:
                                transcription = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file_obj,
                                    response_format=AUDIO_CONFIG["response_format"],
                                    language=AUDIO_CONFIG["language"]
                                )
                                
                                # 如果是文本格式，使用AI处理
                                if AUDIO_CONFIG["response_format"] == "text":
                                    transcription = process_text(transcription)
                                
                                # 只有在需要时才调整时间戳
                                if needs_timestamp_adjustment(AUDIO_CONFIG["response_format"]):
                                    transcription = adjust_timestamps(transcription, i * AUDIO_CONFIG["split_interval"])
                                
                                # 保存分段文件
                                segment_output_path = f"{OUTPUT_CONFIG['trans_chunks_dir']}/segment_{i}{get_output_extension()}"
                                with open(segment_output_path, "w", encoding="utf-8") as f:
                                    f.write(transcription)
                                print(f"第{i+1}段转录完成并保存")
                                
                                # 对于非字幕格式，添加分段标记
                                if not needs_timestamp_adjustment(AUDIO_CONFIG["response_format"]):
                                    all_content += f"\n=== 第{i+1}段 ===\n\n"
                                all_content += transcription + "\n"
                        
                        # 保存最终合并的文件
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(all_content)
                        print(f"\n所有分段已合并到: {output_path}")
                    else:
                        # 转换后的文件小于25MB，直接转录
                        print("转换后的文件小于25MB，直接进行转录...")
                        with open(converted_file, "rb") as audio_file_obj:
                            transcription = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file_obj,
                                response_format=AUDIO_CONFIG["response_format"],
                                language=AUDIO_CONFIG["language"]
                            )
                            
                            # 如果是文本格式，使用AI处理
                            if AUDIO_CONFIG["response_format"] == "text":
                                transcription = process_text(transcription)
                            
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.write(transcription)
                            print(f"转录完成，已保存到: {output_path}")
                else:
                    # 直接转录小文件
                    print("文件小于25MB，直接进行转录...")
                    with open(audio_file, "rb") as audio_file_obj:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file_obj,
                            response_format=AUDIO_CONFIG["response_format"],
                            language=AUDIO_CONFIG["language"]
                        )
                        
                        # 如果是文本格式，使用AI处理
                        if AUDIO_CONFIG["response_format"] == "text":
                            transcription = process_text(transcription)
                        
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(transcription)
                        print(f"转录完成，已保存到: {output_path}")
                
                print(f"=== 文件 {index}/{total_files} 处理完成 ===")
            except Exception as e:
                print(f"处理文件时出错: {str(e)}")
                continue
        
        print("\n=== 所有文件处理完成 ===")
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
    finally:
        # 确保在任何情况下都清理临时文件
        clean_output()


if __name__ == "__main__":

    # 示例用法
    input_path = r"C:\test.m4a"  # 可以是单个文件或目录
    transcribe_audio(input_path)
