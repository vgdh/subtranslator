import os
import sys
import ffmpeg
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from google import genai #google-genai
import json
import time

_TMP_FILE = "temp_subtitle.srt"
_last_request_time = 0
_GEMINI_MIN_REQUEST_INTERVAL = 60/15  # requests per minute)

def gemini_request(api_key: str, model: str, content: str) -> str:
    """Send a request to the Gemini API with rate limiting
    """
    global _last_request_time
    
    # Calculate time to wait
    now = time.time()
    time_since_last = now - _last_request_time
    if time_since_last < _GEMINI_MIN_REQUEST_INTERVAL:
        wait_time = _GEMINI_MIN_REQUEST_INTERVAL - time_since_last
        time.sleep(wait_time)
    
    # Make the request
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=content)
    
    # Update last request time
    _last_request_time = time.time()
    
    return response.text

def llm_request(config, content: str) -> str:
    if config['provider'] == 'gemini':
        return gemini_request(config['api_key'], "gemini-2.0-flash", content)
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

        output_file = _TMP_FILE
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
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        # Create JSON array of texts
        content = json.dumps(batch)
        
        # Make the API request
        request = request_builder(content, config)
        response = llm_request(config, request)
        
        if response:
            cleaned_response = response[response.find('['):response.rfind(']') + 1]
            # Parse the JSON response
            try:
                translated_texts = json.loads(cleaned_response)
                
                # Check if lengths match
                if len(translated_texts) == len(batch):
                    return translated_texts
                else:
                    print(f"Warning: Response length mismatch (got {len(translated_texts)}, expected {len(batch)}). Retrying...")
                    retry_count += 1
                    
            except json.JSONDecodeError:
                print("Error: Failed to decode JSON response. Retrying...")
                retry_count += 1
        else:
            raise ValueError("Error: No response from LLM API")
    
    raise Exception(f"Failed to get correct translation after {max_retries} attempts")

def request_builder(content, config):
    req = f"""Task: 
Translate provided JSON to {config['language']}
============================================================
Context:
{str(content)}
============================================================
You MUST respond JSON only, and the response must be a JSON array of the same length as the input JSON array."""
    return req

def format_subtitle_entry(entry: SubtitleEntry) -> str:
    """Convert a SubtitleEntry to SRT format string"""
    return f"{entry.number}\n{entry.timeline}\n{entry.text}\n"

def save_subtitles(config, entries: list[SubtitleEntry], mkv_file: str):
    """Save subtitle entries to a file in SRT format"""
    # Create output filename by replacing .mkv extension with .srt
    output_file = Path(mkv_file).with_stem(f"{Path(mkv_file).stem}_{config['language']}").with_suffix('.srt')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(format_subtitle_entry(entry))
                f.write('\n')  # Extra newline between entries
        print(f"Translated subtitles saved to: {output_file}")
    except Exception as e:
        print(f"Error saving subtitles: {str(e)}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <mkv_file>")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    # Pretty print configuration
    print("\nCurrent configuration:")
    print("-" * 50)
    for key, value in config.items():
        if key == 'api_key':
            # Mask API key for security
            masked_key = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
            print(f"{key:10}: {masked_key}")
        else:
            print(f"{key:10}: {value}")
    print("-" * 50 + "\n")

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
        batches = batch_subtitles(subtitle_entries, batch_size=50)
        print(f"Created {len(batches)} batches of subtitles")
        
        translated_entries = []
   
        batch_execute_times_sec = []
        for batch in batches:
            if len(batch_execute_times_sec)==0:
                print(f"Processing batch {batches.index(batch)+1} of {len(batches)}")
            else:
                extimated_time_for_one_batch = sum(batch_execute_times_sec)/len(batch_execute_times_sec)
                estimated_time = extimated_time_for_one_batch * (len(batches) - len(batch_execute_times_sec))
                est_minutes = int(estimated_time // 60)
                est_seconds = int(estimated_time % 60)
                print(f"Processing batch {batches.index(batch)+1} of {len(batches)} Estimated time for remaining batches: {est_minutes} minutes {est_seconds} seconds")
            
            start_time = time.time()
            translated_texts = process_batch(batch, config)
            end_time = time.time()
            batch_execute_times_sec.append(end_time - start_time)

            for id in range(len(batch)):
                # Add the translated text to the corresponding entry
                subtitle_entries[id].text = translated_texts[id]
                translated_entries.append(subtitle_entries[id])
            
            # Remove the processed batch from the original list
            subtitle_entries = subtitle_entries[len(batch):]
        
        # Save the translated subtitles
        save_subtitles(config, translated_entries, mkv_file)


    if os.path.exists(_TMP_FILE):
        try:
            os.remove(_TMP_FILE)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {_TMP_FILE}: {str(e)}")
            
if __name__ == "__main__":
    main()