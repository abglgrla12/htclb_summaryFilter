import pandas as pd
import uvicorn
import time
import os
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware

# FastAPI app initialization
app = FastAPI()

# Enable CORS for external access (Make.com)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store processed Excel files
OUTPUT_DIR = "filtered_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_dataframe(df):
    """Ensure all missing values are converted to None for JSON serialization."""
    df = df.where(pd.notna(df), None)  # Convert NaN, NaT, and empty cells to None
    
    # Convert datetime columns to string to avoid NaT serialization issues
    for col in df.select_dtypes(include=["datetime"]).columns:
        df[col] = df[col].astype(str).replace("NaT", None)
    
    return df

@app.post("/filter_totals")
async def filter_totals(file: UploadFile = File(...)):
    try:
        start_time = time.time()

        # Read Excel file from "Report" sheet
        df = pd.read_excel(file.file, sheet_name="Report", header=0, dtype=str)

        # Convert empty values to None
        df = clean_dataframe(df)

        # Identify rows where the first column contains "Total"
        first_col = df.columns[0]
        mask = df[first_col].astype(str).str.contains("Total", case=False, na=False)

        # Separate summary and filtered data
        dt_summary = df[mask].reset_index(drop=True)
        dt_filtered = df[~mask].reset_index(drop=True)

        # Save filtered data to a new Excel file with "Report" sheet name
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dt_filtered.to_excel(writer, sheet_name='Report', index=False)
        output.seek(0)

        elapsed_time = time.time() - start_time  # Measure execution time

        return JSONResponse(content={
            "processing_time": f"{elapsed_time:.2f} seconds",
            "dt_summary": dt_summary.to_dict(orient="records"),
            "download_url": "/download/filtered_report.xlsx"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download the processed Excel file."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
