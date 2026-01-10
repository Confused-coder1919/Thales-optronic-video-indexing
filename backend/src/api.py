import os
import shutil
import yaml
import traceback # NEW: To grab the exact error message
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime, timezone

import backend.src.core.transcribe as transcribe
import backend.src.core.analyze_outputs as analyze_outputs
from backend.src.utils.extract_audio import extract_audio_from_video

app = FastAPI(title="Thales STT Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = "backend/config/settings.yaml"

def load_config():
    # Fix for path issues: always look relative to project root
    base_path = os.getcwd()
    full_path = os.path.join(base_path, CONFIG_PATH)
    if os.path.exists(full_path):
        with open(full_path, "r") as f:
            return yaml.safe_load(f)
    # Fallback if config is missing
    return {"paths": {"output_dir": "backend/data/output"}}

# --- ROBUST BACKGROUND TASK ---
def process_audio_task(file_path: str, job_dir: str, config: dict):
    print(f"--- STARTING JOB: {job_dir} ---")
    
    try:
        # CHECK: Is this a video?
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"]:
            print(f"Detected video file ({file_ext}). Extracting audio...")
            # Extract audio to a new file
            audio_path = os.path.join(job_dir, "extracted_audio.m4a")
            final_audio_path = extract_audio_from_video(file_path, audio_path)
            print(f"✅ Audio extracted: {final_audio_path}")
        else:
            # It's already audio
            final_audio_path = file_path
            print(f"Using audio file directly: {final_audio_path}")


        # Transcribe using the correct audio path (not the original video!)
        print(f"Transcribing: {final_audio_path}...")
        lang, segments, words = transcribe.transcribe_audio(final_audio_path, config)
        
        # Save CSV
        transcribe.save_to_csv(segments, os.path.join(job_dir, "segments.csv"), 
                              ["segment_id", "start", "end", "text", "avg_logprob"])
        
        # Analyze
        print("Analyzing...")
        df = analyze_outputs.load_data(job_dir)
        report = analyze_outputs.generate_intel_report(df, config)
        
        # Save Success Report
        with open(os.path.join(job_dir, "sitrep.json"), "w") as f:
            import json
            json.dump(report, f, indent=2)
            
        print(f"--- JOB SUCCESS: {job_dir} ---")

    except Exception as e:
        # CRITICAL: Catch the crash and save it to a file
        error_msg = str(e)
        trace = traceback.format_exc()
        print(f"!!! JOB FAILED !!!\n{trace}")
        
        error_data = {
            "status": "failed",
            "error": error_msg,
            "details": trace
        }
        
        with open(os.path.join(job_dir, "error.json"), "w") as f:
            import json
            json.dump(error_data, f, indent=2)

@app.post("/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    config = load_config()
    
    # Create Job ID
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename_clean = os.path.splitext(file.filename)[0].replace(" ", "_")
    job_id = f"{filename_clean}_{timestamp}"
    
    # Ensure absolute path for output
    base_out = config.get('paths', {}).get('output_dir', "backend/data/output")
    job_dir = os.path.join(os.getcwd(), base_out, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save uploaded file
    input_path = os.path.join(job_dir, "source_audio" + os.path.splitext(file.filename)[1])
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_audio_task, input_path, job_dir, config)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    config = load_config()
    base_out = config.get('paths', {}).get('output_dir', "backend/data/output")
    job_dir = os.path.join(os.getcwd(), base_out, job_id)
    
    sitrep_path = os.path.join(job_dir, "sitrep.json")
    error_path = os.path.join(job_dir, "error.json")
    
    if os.path.exists(error_path):
        # Report the crash to frontend
        with open(error_path, "r") as f:
            import json
            return json.load(f)
            
    if os.path.exists(sitrep_path):
        with open(sitrep_path, "r") as f:
            import json
            data = json.load(f)
        
        # Load transcript if available
        transcript = []
        seg_path = os.path.join(job_dir, "segments.csv")
        if os.path.exists(seg_path):
            import pandas as pd
            try:
                seg_df = pd.read_csv(seg_path)
                transcript = seg_df.to_dict(orient="records")
            except:
                pass
        
        return {"status": "completed", "report": data, "transcript": transcript}
    
    return {"status": "processing"}

@app.get("/download/{job_id}/{file_type}")
def download_file(job_id: str, file_type: str):
    config = load_config()
    base_out = config.get('paths', {}).get('output_dir', "backend/data/output")
    job_dir = os.path.join(os.getcwd(), base_out, job_id)
    
    filename = "sitrep.json" if file_type == "json" else "segments.csv"
    path = os.path.join(job_dir, filename)
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(path, filename=f"{job_id}.{file_type}")