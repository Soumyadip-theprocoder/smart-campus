# Google Colab Face Recognition API

To offload the heavy `face_recognition` and `dlib` processing from your Render backend, run this script in a Google Colab notebook. It spins up a FastAPI server and exposes it publicly using `pyngrok`.

## Instructions
1. Open [Google Colab](https://colab.research.google.com/).
2. Create a new Notebook.
3. Paste the following code block into a cell and run it.
4. Copy the `NgrokTunnel` URL printed at the bottom of the cell output.
5. In your Django backend `.env` (or Render Environment Variables), set:
   `FACE_ENGINE_URL=<the_ngrok_url>`

## Code

```python
# 1. Install dependencies
!pip install fastapi uvicorn python-multipart face_recognition pyngrok nest-asyncio

import face_recognition
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import nest_asyncio
from pyngrok import ngrok
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
        
        # Convert to RGB (face_recognition expects RGB)
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

# Setup ngrok
# (Optional) You can authenticate your ngrok agent if required by ngrok:
# ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")

ngrok_tunnel = ngrok.connect(8000)
print("Public URL:", ngrok_tunnel.public_url)
print("Use this URL as your FACE_ENGINE_URL in Django settings.")

# Run the server
nest_asyncio.apply()
uvicorn.run(app, host="0.0.0.0", port=8000)
```
