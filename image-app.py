from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import uvicorn

app = FastAPI()

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Input prompt for AI
input_prompt = """
You are an expert nutritionist. Analyze the food items visible in the image and calculate their total calories. 
Respond with a JSON-like database format that includes the following fields:

- id: Unique identifier for the item.
- item_name: The name of the food item.
- quantity: The number of each item visible in the image.
- calories: The calorie count for the given quantity of the item.

Example response format:
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "name": "apple",
            "color": "green",
            "weight": 150,
            "delicious": true
        },
        {
            "id": 2,
            "name": "banana",
            "color": "yellow",
            "weight": 116,
            "delicious": true
        },
        {
            "id": 3,
            "name": "strawberry",
            "color": "red",
            "weight": 12,
            "delicious": true
        }
    ]
}
"""

def get_gemini_response(prompt: str, image_data):
    """
    Generates a response using the Gemini AI model.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([prompt, image_data[0]])
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Gemini API: {str(e)}")

def input_image_setup(uploaded_file: UploadFile):
    """
    Prepares the uploaded image for API submission.
    """
    try:
        # Read file content
        bytes_data = uploaded_file.file.read()
        
        # Validate if the file is a valid image
        Image.open(uploaded_file.file)
        uploaded_file.file.seek(0)  # Reset file pointer for further use

        return [
            {
                "mime_type": uploaded_file.content_type,
                "data": bytes_data
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def main():
    """
    Render a basic HTML form for file upload.
    """
    content = """
    <html>
        <head>
            <title>Fruit Counter</title>
        </head>
        <body>
            <h1>Upload an Image of Fruits</h1>
            <form action="/count_fruits/" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept="image/*">
                <input type="submit">
            </form>
        </body>
    </html>
    """
    return content

@app.post("/count_fruits/", response_class=JSONResponse)
async def count_fruits(file: UploadFile = File(...)):
    """
    Endpoint to analyze the uploaded image and return calorie information.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JPEG or PNG image.")

    try:
        # Prepare image data
        image_data = input_image_setup(file)

        # Get AI response
        response = get_gemini_response(input_prompt, image_data)

        # Return response as JSON
        return {"success": True, "data": response}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

#port = int(os.getenv("PORT", 8000))  # Default to 8000 if not set

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
