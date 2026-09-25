# Google Colab Face Recognition API

To offload the heavy `face_recognition` and `dlib` processing from your Render backend, run this script in a Google Colab notebook. It spins up a FastAPI server and exposes it publicly using `pyngrok`.

## Instructions
1. Open [Google Colab](https://colab.research.google.com/).
2. Create a new Notebook.
3. Paste the following code block into a cell and run it.
4. Copy the `NgrokTunnel` URL printed at the bottom of the cell output.
5. In your Django backend `.env` (or Render Environment Variables), set:
   `FACE_ENGINE_URL=<the_ngrok_url>`

```python
# Cell 1: Install dependencies
!npm install -g localtunnel
!pip install fastapi uvicorn python-multipart face_recognition
```

```python
# Cell 2: Write the FastAPI app to a file
%%writefile app.py
import face_recognition
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import io
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Face Engine API is running"}

@app.post("/encode")
async def encode_face(file: UploadFile = File(...)):
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        img_array = np.array(image)
        
        # Detect faces
        face_locations = face_recognition.face_locations(img_array, model="hog")
        
        if not face_locations:
            raise HTTPException(status_code=400, detail="No face detected in the image.")
            
        if len(face_locations) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please ensure only one face is visible.")
            
        # Encode face
        encoding = face_recognition.face_encodings(img_array, [face_locations[0]])[0]
        
        return {"encoding": encoding.tolist()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# Cell 3: Start the server and localtunnel
import subprocess
import time

print("Starting Uvicorn server...")
# Start uvicorn in the background
subprocess.Popen(["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"])

# Give uvicorn a second to start
time.sleep(2)

print("Starting Localtunnel...")
# Start localtunnel
lt_process = subprocess.Popen(
    ["lt", "--port", "8000"], 
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Read the URL
time.sleep(2)
output = lt_process.stdout.readline().decode('utf-8').strip()

print("\n" + "="*50)
print("YOUR FACE ENGINE URL IS:")
print(output.replace("your url is: ", ""))
print("="*50 + "\n")
print("Keep this tab open while you want the Face Engine to be online!")
```
