# make a fastapi app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.validate_secrets import validate_secret
app = FastAPI()

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# post endpoint to read from json given in the format
#  {
#   // Student email ID
#   "email": "student@example.com",
#   // Student-provided secret
#   "secret": "...",
#   // A unique task ID.
#   "task": "captcha-solver-...",
#   // There will be multiple rounds per task. This is the round index
#   "round": 1,
#   // Pass this nonce back to the evaluation URL below
#   "nonce": "ab12-...",
#   // brief: mentions what the app needs to do
#   "brief": "Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample.",
#   // checks: mention how it will be evaluated
#   "checks": [
#     "Repo has MIT license"
#     "README.md is professional",
#     "Page displays captcha URL passed at ?url=...",
#     "Page displays solved captcha text within 15 seconds",
#   ],
#   // Send repo & commit details to the URL below
#   "evaluation_url": "https://example.com/notify",
#   // Attachments will be encoded as data URIs
#   "attachments": [{ "name": "sample.png", "url": "data:image/png;base64,iVBORw..." }]
# }

@app.post("/submit")
async def submit(data: dict):
    # get the data from the json
    
    # validate the secret
    if not validate_secret(data.get("secret", "")):
        return {"error": "Invalid secret"}
    
    # check the rounds
    if data.get('round') == 1:
        pass

    if data.get('round') == 2:
        pass



    print(data)
    # Return a simple JSON response
    return {"status": "received", "data": data}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)