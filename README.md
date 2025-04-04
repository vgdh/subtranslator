# Subtranslator (Subtitle translator)

A Python tool that extracts and translates subtitles from MKV files using AI.

## Features
- Extracts subtitle tracks from MKV files using ffmpeg
- Translates subtitles using AI model (only Google's Gemini currently implemented. You need to create a free key https://aistudio.google.com/apikey)
- Supports batch processing to handle rate limits
- Shows estimated completion time during translation
- Saves translated subtitles as SRT files

## Prerequisites
- Python 3.x

## Installation
1. Clone this repository
2. Install required packages:
```sh
pip install -r requirements.txt
```
3. Create a `.env` file with your configuration:
```
PROVIDER=gemini
API_KEY=your_gemini_api_key
LANGUAGE=target_language
```

## Usage
Run the script with an MKV file as argument:

```sh
python subtranslator.py video.mkv
```

The script will:
1. List all available subtitle tracks in the MKV file
2. Let you select which subtitle track to translate
3. Extract and translate the subtitles
4. Save the translated subtitles as `video_language.srt`

## Configuration
Configure the translator by editing the `.env` file:
- `PROVIDER`: Translation provider (currently only supports `gemini`)
- `API_KEY`: Your Gemini API key
- `LANGUAGE`: Target language for translation

## Requirements
- ffmpeg-python
- python-dotenv  
- google-genai

## License
MIT License
