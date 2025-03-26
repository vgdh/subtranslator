import os
import sys
import ffmpeg
import subprocess

def extract_subtitle(mkv_file, stream_index):
    try:

        output_file = f"temp_subtitle.srt"
        if os.path.exists(output_file):
            os.remove(output_file) 

        subprocess.run([
            'ffmpeg', '-i', mkv_file,
            '-map', f'0:{stream_index}',
            output_file
        ], check=True, capture_output=True)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            subtitle_text = f.read()
        return subtitle_text
    except Exception as e:
        print(f"Error extracting subtitle: {str(e)}")
        sys.exit(1)

def list_subtitles(mkv_file):
    try:
        # Get media information using ffprobe
        probe = ffmpeg.probe(mkv_file)
        
        # Find all subtitle streams
        subtitle_streams = [stream for stream in probe['streams'] 
                          if stream['codec_type'] == 'subtitle']
        
        if not subtitle_streams:
            print("No subtitle tracks found")
            return None
        
        print(f"\nSubtitle tracks in {mkv_file}:")
        print("-" * 50)
        
        for idx, stream in enumerate(subtitle_streams, 1):
            language = stream.get('tags', {}).get('language', 'unknown')
            codec = stream.get('codec_name', 'unknown')
            title = stream.get('tags', {}).get('title', 'No title')
            print(f"{idx}. Language: {language}, Codec: {codec}, Title: {title}")
        
        # Ask user to select a subtitle
        while True:
            try:
                choice = int(input("\nSelect subtitle number: "))
                if 1 <= choice <= len(subtitle_streams):
                    selected_stream = subtitle_streams[choice - 1]
                    return selected_stream['index']
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    except Exception:
        print("Error: An error occurred while listing subtitle tracks")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <mkv_file>")
        sys.exit(1)
    
    mkv_file = sys.argv[1]
    if not mkv_file.lower().endswith('.mkv'):
        print("Error: Please provide a .mkv file")
        sys.exit(1)
    
    stream_index = list_subtitles(mkv_file)
    if stream_index is not None:
        subtitle_text = extract_subtitle(mkv_file, stream_index)
        print("\nSubtitle content loaded successfully!")
        print(subtitle_text)
        # Now subtitle_text contains the selected subtitle content
        # You can use it for further processing

if __name__ == "__main__":
    main()