import os
import sys
import ffmpeg
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from google import genai #google-genai
import json

def gemini_request(api_key: str, model: str, content: str) -> str:
    """Send a request to the Gemini API"""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=content)
    return response.text

def llm_request(config, content: str) -> str:
    if config['provider'] == 'gemini':
        return gemini_request(config['api_key'], "gemini-2.5-pro-exp-03-25", content)
    else:
        raise ValueError(f"Unsupported model: {config['provider']}")


def create_default_config():
    """Create default .env file if it doesn't exist"""
    env_path = Path('.env')
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write("PROVIDER=gemini\nAPI_KEY=enterkey\nLANGUAGE=russian")

def load_config():
    """Load configuration from .env file"""
    create_default_config()
    load_dotenv()
    
    config = {
        'provider': os.getenv('PROVIDER', 'gemini'),
        'api_key': os.getenv('API_KEY', 'enterkey'),
        'language': os.getenv('LANGUAGE', 'russian')

    }
    
    if config['api_key'] == 'enterkey':
        print("Warning: Please set your API key in the .env file")
    
    return config

class SubtitleEntry:
    def __init__(self, number: str, timeline: str, text: str):
        self.number = number
        self.timeline = timeline
        self.text = text

def parse_subtitles(subtitle_text: str) -> list[SubtitleEntry]:
    entries = []
    current_entry = {'number': '', 'timeline': '', 'text': []}
    
    for line in subtitle_text.split('\n'):
        line = line.strip()
        if not line:
            if current_entry['number']:  # Complete entry found
                entries.append(SubtitleEntry(
                    current_entry['number'],
                    current_entry['timeline'],
                    '\n'.join(current_entry['text'])
                ))
                current_entry = {'number': '', 'timeline': '', 'text': []}
        elif '-->' in line:
            current_entry['timeline'] = line
        elif line.isdigit():
            current_entry['number'] = line
        else:
            current_entry['text'].append(line)
    
    # Add the last entry if exists
    if current_entry['number']:
        entries.append(SubtitleEntry(
            current_entry['number'],
            current_entry['timeline'],
            '\n'.join(current_entry['text'])
        ))
    
    return entries

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

def batch_subtitles(subtitle_entries: list[SubtitleEntry], batch_size: int = 10) -> list[list[str]]:
    """
    Split subtitle entries into batches and extract their text content
    
    Args:
        subtitle_entries: List of SubtitleEntry objects
        batch_size: Number of subtitle texts per batch
        
    Returns:
        List of batches, where each batch is a list of subtitle texts
    """
    batches = []
    current_batch = []
    
    for entry in subtitle_entries:
        current_batch.append(entry.text)
        
        if len(current_batch) >= batch_size:
            batches.append(current_batch)
            current_batch = []
    
    # Add the remaining entries if any
    if current_batch:
        batches.append(current_batch)
    
    return batches

def process_batch(batch: list[str], config: dict) -> list[str]:
    """
    Process a batch of subtitle texts using the LLM API
    
    Args:
        batch: List of subtitle texts to process
        config: Configuration dictionary with API settings
        
    Returns:
        List of processed/translated texts
    """
    # Create JSON array of texts
    content = json.dumps(batch)
    
    print(str(content))
    # Make the API request

    request =  request_builder(content, config)

    response = llm_request(config, )
    
    # Parse the response and return processed texts
    # Implementation depends on your API response format
    return [] 

def request_builder(content, config):
    req = f"""Translate this json to {config['language']}:
{str(content)}
you MUST respond as JSON, and the response must be a JSON array of the same length as the input JSON array.
"""
    return req

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <mkv_file>")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    mkv_file = sys.argv[1]
    if not mkv_file.lower().endswith('.mkv'):
        print("Error: Please provide a .mkv file")
        sys.exit(1)
    
    stream_index = list_subtitles(mkv_file)
    if stream_index is not None:
        subtitle_text = extract_subtitle(mkv_file, stream_index)
        subtitle_entries = parse_subtitles(subtitle_text)
        print("\nSubtitle content loaded successfully!")
        
        # Create batches of subtitle texts
        batches = batch_subtitles(subtitle_entries)
        print(f"Created {len(batches)} batches of subtitles")
        
        for batch in batches:
            process_batch(batch, config)  # Future function to implement

        
        
if __name__ == "__main__":
    main()