import pandas as pd
import uvicorn
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

        # Read Excel file, using the "Report" sheet
        df = pd.read_excel(file.file, sheet_name="Report", header=0, dtype=str)
        
        # Convert all empty values to None
        df = clean_dataframe(df)

        # Identify rows where the first column contains "Total"
        first_col = df.columns[0]
        mask = df[first_col].astype(str).str.contains("Total", case=False, na=False)

        # Separate summary and filtered data
        dt_summary = df[mask].reset_index(drop=True)
        dt_filtered = df[~mask].reset_index(drop=True)

        elapsed_time = time.time() - start_time  # Measure execution time
        
        return JSONResponse(content={
            "processing_time": f"{elapsed_time:.2f} seconds",
            "dt_summary": dt_summary.to_dict(orient="records"),
            "dt_filtered": dt_filtered.to_dict(orient="records"),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
