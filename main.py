from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
import edge_tts
from io import BytesIO
import os
import tempfile

app = FastAPI()

async def tts_to_bytes(text: str, voice: str, rate: str, volume: str, pitch: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
        tmp_path = tmp_file.name
    try:
        await communicate.save(tmp_path)
        with open(tmp_path, 'rb') as f:
            audio_data = f.read()
        return audio_data
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "API running... use /convert.",
            "developer": "Blind tech visionary"
        }
    )

@app.get("/convert")
async def convert(
    text: str = None,
    voice: str = "en-US-GuyNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    file_name: str = "generated_mp3.mp3"
):
    if not text or text.strip() == "":
        return JSONResponse(
            content={
                "status_code": 400,
                "message": "Text is required"
            },
            status_code=400
        )
    
    try:
        rate = rate if rate else "+0%"
        volume = volume if volume else "+0%"
        pitch = pitch if pitch else "+0Hz"
        voice = voice if voice else "en-US-GuyNeural"
        file_name = file_name if file_name and file_name.strip() else "generated_mp3.mp3"
        
        if not file_name.lower().endswith(".mp3"):
            file_name += ".mp3"
        
        audio_data = await tts_to_bytes(text, voice, rate, volume, pitch)
        audio_buffer = BytesIO(audio_data)
        
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename={file_name}"
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status_code": 500,
                "message": str(e)
            },
            status_code=500
        )

@app.get("/voices")
async def list_voices():
    try:
        voices = await edge_tts.list_voices()
        sorted_voices = sorted(voices, key=lambda x: (x.get("Locale", ""), x.get("ShortName", "")))
        formatted_voices = []
        for v in sorted_voices:
            formatted_voices.append({
                "ShortName": v.get("ShortName", "N/A"),
                "FriendlyName": v.get("FriendlyName", v.get("ShortName", "N/A")),
                "Gender": v.get("Gender", "Unknown"),
                "Locale": v.get("Locale", "N/A")
            })
        
        return JSONResponse(
            content={
                "status_code": 200,
                "voices": formatted_voices
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status_code": 500,
                "message": str(e)
            },
            status_code=500
        )