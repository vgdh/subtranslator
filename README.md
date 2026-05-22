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
- FFMPEG

## Installation
1. Clone this repository
2. Create python venv
```
python3 -m venv .venv
```
3. Install required packages:
```sh
pip install -r requirements.txt
```
4. Create a `.env` file with your configuration:
```
PROVIDER=gemini
API_KEY=your_gemini_api_key
LANGUAGE_OUT=target_language
MODEL=gemma-4-31b-it
```

If you want to use OpenRouter instead:
```
PROVIDER=openrouter
API_KEY=your_openrouter_api_key
LANGUAGE_OUT=target_language
MODEL=google/gemma-4-31b-it
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
- `PROVIDER`: Translation provider (`gemini` or `openrouter`)
- `API_KEY`: Your API key for Gemini or OpenRouter
- `LANGUAGE_OUT`: Target language for translation
- `MODEL`: Optional model override for OpenRouter (default: `gemma-4-31b-it`)

## Requirements
- ffmpeg-python
- python-dotenv  
- google-genai

## Ubuntu desktop link
1. Create file on desktop named `Run subtranslator.desktop` with the following:
```
[Desktop Entry]
Version=1.0
Type=Application
Terminal=true
Exec=/home/user/subtranslator/translate.sh
Name=Subtranslator Launcher
Comment=Run the Subtranslator script
Icon=utilities-terminal
Categories=Utility;
```

2. add execution flag to it
3. right clik -> allow to execute




## License
MIT License
