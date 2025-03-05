import pandas as pd
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/filter_totals")
async def filter_totals(file: UploadFile = File(...)):
    try:
        # Read the uploaded Excel file, specifically the "Report" sheet
        df = pd.read_excel(file.file, sheet_name="Report", header=0, dtype=str)
        
        # Replace all empty strings and NaN values with None (JSON friendly)
        df = df.replace(["", "NaN", "nan", "None"], None)

        # Identify rows where the first column contains 'Total'
        first_col = df.columns[0]
        mask = df[first_col].astype(str).str.contains("Total", case=False, na=False)
        
        # Split into two DataFrames
        dt_summary = df[mask].reset_index(drop=True)
        dt_filtered = df[~mask].reset_index(drop=True)

        # Convert DataFrames to dictionaries for JSON response
        return JSONResponse(content={
            "dt_summary": dt_summary.to_dict(orient="records"),
            "dt_filtered": dt_filtered.to_dict(orient="records")
        })
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Sheet 'Report' not found: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
