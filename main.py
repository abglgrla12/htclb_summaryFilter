import pandas as pd
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

import os
import uvicorn



app = FastAPI()

# Enable CORS for all origins (Adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/filter_totals")
async def filter_totals(file: UploadFile = File(...)):
    try:
        # Read the uploaded Excel file
        df = pd.read_excel(file.file, sheet_name=0, header=0)
        
        # Identify rows where the first column contains 'Total'
        first_col = df.columns[0]
        mask = df[first_col].astype(str).str.contains("Total", case=False, na=False)
        
        # Split into two DataFrames
        dt_summary = df[mask].reset_index(drop=True)   # Rows with 'Total'
        dt_filtered = df[~mask].reset_index(drop=True) # Rows without 'Total'
        
        # Convert DataFrames to JSON response
        return JSONResponse(content={
            "dt_summary": dt_summary.to_dict(orient="records"),
            "dt_filtered": dt_filtered.to_dict(orient="records")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Get PORT from Heroku, default to 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
