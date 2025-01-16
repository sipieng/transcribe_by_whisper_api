from openai import OpenAI
from pydub import AudioSegment
import os
import re
from config import OPENAI_CONFIG, AUDIO_CONFIG, OUTPUT_CONFIG
from text_processor import process_text
import subprocess
import time

# Initialize OpenAI client
client = OpenAI(
    base_url=OPENAI_CONFIG["base_url"],
    api_key=OPENAI_CONFIG["api_key"]
)

def get_audio_format(file_path):
    """Get the audio format from file extension"""
    return os.path.splitext(file_path)[1][1:].lower()

def get_output_extension():
    """
    Get the output file extension based on response format
    
    Returns:
        str: File extension (including dot)
    """
    format_extensions = {
        "text": ".txt",
        "srt": ".srt",
        "json": ".json",
        "verbose_json": ".json",
        "vtt": ".vtt"
    }
    return format_extensions.get(AUDIO_CONFIG["response_format"], ".txt")

def needs_timestamp_adjustment(response_format):
    """
    Check if the response format needs timestamp adjustment
    
    Args:
        response_format: Whisper API response format
    
    Returns:
        bool: True if timestamp adjustment is needed
    """
    return response_format in ["srt", "vtt"]

def add_time(time_str, offset_ms):
    """
    Add time offset to timestamp
    
    Args:
        time_str: Timestamp string in format "HH:MM:SS,mmm"
        offset_ms: Time offset in milliseconds
    
    Returns:
        str: Adjusted timestamp string
    """
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    total_ms += offset_ms
    h = total_ms // 3600000
    m = (total_ms % 3600000) // 60000
    s = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def adjust_timestamps(content, time_offset):
    """
    Adjust subtitle timestamps
    
    Args:
        content: Subtitle content
        time_offset: Time offset in milliseconds
    
    Returns:
        str: Content with adjusted timestamps
    
    Note:
        Currently supports SRT and VTT formats
    """
    if AUDIO_CONFIG["response_format"] not in ["srt", "vtt"]:
        return content
        
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
    
    def replace_timestamps(match):
        start_time = match.group(1)
        end_time = match.group(2)
        new_start = add_time(start_time, time_offset)
        new_end = add_time(end_time, time_offset)
        return f"{new_start} --> {new_end}"

    return re.sub(pattern, replace_timestamps, content)

def convert_to_mp3(input_file):
    """Convert audio to MP3 format with specified bitrate"""
    output_path = OUTPUT_CONFIG["converted_audio"]
    
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-y",  # Overwrite output file if exists
        output_path
    ]
    
    print(f"Converting audio to {AUDIO_CONFIG['mp3_bitrate']} bitrate MP3...")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

def split_audio(audio_file_path):
    """Split audio file using ffmpeg"""
    print("\n=== Starting Audio Split ===")
    # Ensure output directories exist
    os.makedirs(OUTPUT_CONFIG["audio_chunks_dir"], exist_ok=True)
    os.makedirs(OUTPUT_CONFIG["trans_chunks_dir"], exist_ok=True)
    
    # Get audio duration
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    duration = float(result.stdout)
    
    # Calculate number of segments
    segment_duration = AUDIO_CONFIG["split_interval"] / 1000  # Convert to seconds
    segments = []
    
    for i in range(0, int(duration * 1000), int(AUDIO_CONFIG["split_interval"])):
        segment_path = f"{OUTPUT_CONFIG['audio_chunks_dir']}/segment_{i//int(segment_duration)}.mp3"
        segments.append(segment_path)
        
        # ffmpeg command for splitting
        cmd = [
            "ffmpeg",
            "-i", audio_file_path,
            "-ss", str(i/1000),
            "-t", str(segment_duration),
            "-c", "copy",
            "-y",
            segment_path
        ]
        
        print(f"Splitting segment {i//int(segment_duration)+1}...")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return segments

def clean_output():
    """Clean all output files and directories"""
    print("\n=== Cleaning Output Files ===")
    
    # Clean directories
    for dir_path in [OUTPUT_CONFIG["audio_chunks_dir"], 
                    OUTPUT_CONFIG["trans_chunks_dir"]]:
        if os.path.exists(dir_path):
            # Delete files in directory
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                for _ in range(3):  # Try up to 3 times
                    try:
                        os.remove(file_path)
                        break
                    except PermissionError:
                        time.sleep(0.1)  # Wait 100ms
                    except FileNotFoundError:
                        break  # File already deleted
            
            # Delete empty directory
            for _ in range(3):  # Try up to 3 times
                try:
                    os.rmdir(dir_path)
                    break
                except PermissionError:
                    time.sleep(0.1)  # Wait 100ms
                except OSError as e:
                    if "directory not empty" in str(e).lower():
                        print(f"Failed to delete directory (not empty): {dir_path}")
                    break
                except FileNotFoundError:
                    break  # Directory already deleted
    
    # Clean converted MP3 file
    if os.path.exists(OUTPUT_CONFIG["converted_audio"]):
        for _ in range(3):  # Try up to 3 times
            try:
                os.remove(OUTPUT_CONFIG["converted_audio"])
                break
            except PermissionError:
                time.sleep(0.1)  # Wait 100ms
            except FileNotFoundError:
                break  # File already deleted
    
    print("=== Cleanup Complete ===\n")

def get_supported_audio_files(path):
    """
    Get all supported audio files from path
    
    Args:
        path: File or directory path
    
    Returns:
        list: List of supported audio file paths
    """
    supported_formats = ['mp3', 'm4a', 'wav']
    
    if os.path.isfile(path):
        if get_audio_format(path) in supported_formats:
            return [path]
        return []
    
    audio_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                audio_files.append(os.path.join(root, file))
    return sorted(audio_files)

def transcribe_audio(audio_path):
    """Transcribe audio file"""
    try:
        # Clean temporary files before starting
        clean_output()
        
        # Get list of audio files to process
        audio_files = get_supported_audio_files(audio_path)
        if not audio_files:
            print(f"No supported audio files found: {audio_path}")
            return
        
        # Ensure all necessary directories exist
        for dir_path in [OUTPUT_CONFIG["audio_chunks_dir"], 
                        OUTPUT_CONFIG["trans_chunks_dir"],
                        OUTPUT_CONFIG["transcripts_dir"]]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Process each audio file
        total_files = len(audio_files)
        for index, audio_file in enumerate(audio_files, 1):
            print(f"\n=== Processing File {index}/{total_files}: {os.path.basename(audio_file)} ===")
            
            # Set output file path
            output_filename = f"{os.path.splitext(os.path.basename(audio_file))[0]}{get_output_extension()}"
            output_path = os.path.join(OUTPUT_CONFIG["transcripts_dir"], output_filename)
            
            # Process single file
            file_size = os.path.getsize(audio_file)
            print(f"File size: {file_size/1024/1024:.2f}MB")
            
            try:
                if file_size > AUDIO_CONFIG["max_file_size"]:
                    print(f"File size exceeds 25MB, processing required...")
                    converted_file = convert_to_mp3(audio_file)
                    converted_size = os.path.getsize(converted_file)
                    print(f"Converted file size: {converted_size/1024/1024:.2f}MB")
                    
                    # If converted file still exceeds limit, split it
                    if converted_size > AUDIO_CONFIG["max_file_size"]:
                        print(f"Converted file still exceeds 25MB, splitting required...")
                        segments = split_audio(converted_file)
                        all_content = ""
                        
                        # Transcribe each segment
                        for i, segment_path in enumerate(segments):
                            print(f"\nTranscribing segment {i+1}/{len(segments)}...")
                            with open(segment_path, "rb") as audio_file_obj:
                                transcription = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file_obj,
                                    response_format=AUDIO_CONFIG["response_format"],
                                    language=AUDIO_CONFIG["language"]
                                )
                                
                                # Process text if needed
                                if AUDIO_CONFIG["response_format"] == "text":
                                    transcription = process_text(transcription)
                                # Adjust timestamps if needed
                                elif needs_timestamp_adjustment(AUDIO_CONFIG["response_format"]):
                                    transcription = adjust_timestamps(transcription, i * AUDIO_CONFIG["split_interval"])
                                
                                # Save segment
                                segment_output_path = f"{OUTPUT_CONFIG['trans_chunks_dir']}/segment_{i}{get_output_extension()}"
                                with open(segment_output_path, "w", encoding="utf-8") as f:
                                    f.write(transcription)
                                print(f"Segment {i+1} transcribed and saved")
                                
                                # Add segment markers for non-subtitle formats
                                if not needs_timestamp_adjustment(AUDIO_CONFIG["response_format"]):
                                    all_content += f"\n=== Segment {i+1} ===\n\n"
                                all_content += transcription + "\n"
                        
                        # Save merged file
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(all_content)
                        print(f"\nAll segments merged to: {output_path}")
                    else:
                        # Transcribe converted file directly
                        print("Converted file is under 25MB, transcribing directly...")
                        with open(converted_file, "rb") as audio_file_obj:
                            transcription = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file_obj,
                                response_format=AUDIO_CONFIG["response_format"],
                                language=AUDIO_CONFIG["language"]
                            )
                            
                            # Process text if needed
                            if AUDIO_CONFIG["response_format"] == "text":
                                transcription = process_text(transcription)
                                
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.write(transcription)
                            print(f"Transcription complete, saved to: {output_path}")
                else:
                    # Transcribe small file directly
                    print("File is under 25MB, transcribing directly...")
                    with open(audio_file, "rb") as audio_file_obj:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file_obj,
                            response_format=AUDIO_CONFIG["response_format"],
                            language=AUDIO_CONFIG["language"]
                        )
                        
                        # Process text if needed
                        if AUDIO_CONFIG["response_format"] == "text":
                            transcription = process_text(transcription)
                            
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(transcription)
                        print(f"Transcription complete, saved to: {output_path}")
                
                print(f"=== File {index}/{total_files} Processing Complete ===")
            except Exception as e:
                print(f"Error processing file: {str(e)}")
                continue
        
        print("\n=== All Files Processing Complete ===")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
    finally:
        # Clean temporary files in any case
        clean_output()

if __name__ == "__main__":
    input_path = r"path/to/your/audio"  # Can be a single file or directory
    transcribe_audio(input_path) 