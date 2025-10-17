# Quick Start Guide

This guide will help you get the LLM App Developer running in minutes.

## Prerequisites

- Python 3.10 or higher
- Git installed
- A GitHub account

## Step 1: Get Your Credentials

### 1.1 GitHub Personal Access Token
1. Go to https://github.com/settings/tokens/new
2. Select scopes:
   - ✓ repo (Full control of private repositories)
   - ✓ delete_repo (Delete repositories)
3. Click "Generate token"
4. Copy the token (you won't see it again!)

### 1.2 OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up or sign in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

Note: You'll need to have credits/payment set up with OpenAI to use the API.

## Step 2: Setup the Project

```bash
# Clone the repository
git clone <repo-url>
cd llm-app-developer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Step 3: Configure Environment

Create a `.env` file in the project root:

```env
# Get this from the evaluation server
SECRET_KEY=your-secret-from-form

# GitHub configuration
GITHUB_TOKEN=ghp_your_token_from_github
GITHUB_USER=your-github-username

# OpenAI configuration
OPENAI_API_KEY=sk_your_key_from_openai

# Server
HOST=0.0.0.0
PORT=8000
```

**Tip:** Use `.env.example` as a template:
```bash
cp .env.example .env
# Then edit .env with your actual credentials
```

## Step 4: Run the Server

```bash
python main.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Step 5: Test the Endpoint

In another terminal, test the API:

```bash
curl -X GET http://localhost:8000/docs
```

This opens the interactive API documentation.

Or test with a simple request:

```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "secret": "your-secret-key",
    "task": "test-001",
    "round": 1,
    "nonce": "test-nonce",
    "brief": "Create a simple web app that displays hello world",
    "checks": ["Has MIT license"],
    "evaluation_url": "https://example.com/notify",
    "attachments": []
  }'
```

## Step 6: Submit Your URL to the Evaluation Form

Once the server is running:

1. Go to the Google Form provided by instructors
2. Fill in:
   - **Email**: Your student email
   - **API Endpoint URL**: Your server URL (e.g., `https://myserver.com/submit`)
   - **Secret**: The same value in your `.env` file
   - **GitHub Repository**: Your GitHub username

3. Submit the form

The evaluation server will then send requests to your endpoint!

## Troubleshooting

### "GITHUB_TOKEN not set"
Check that:
- `.env` file exists in the project root
- Line reads: `GITHUB_TOKEN=ghp_...`
- No extra spaces or quotes

### "Invalid secret"
Make sure:
- The `SECRET_KEY` in `.env` matches what you submitted in the form
- Case is exactly the same

### "Failed to create repository"
- Token may have expired: regenerate at https://github.com/settings/tokens
- Token may have wrong scopes: delete and create new one with required scopes
- May need to wait: GitHub sometimes rate-limits requests

### "Anthropic API error"
- Check that `ANTHROPIC_API_KEY` is correct
- Check that you have credits/quota on Anthropic console
- Try a simple request first

### "Port 8000 already in use"
Change the port in `.env`:
```env
PORT=8001
```

Then start the server: `python main.py`

## Production Deployment

### Using Heroku

```bash
# Install Heroku CLI
# Then:

heroku login
heroku create your-app-name
heroku config:set SECRET_KEY=... GITHUB_TOKEN=... etc.
git push heroku main
```

### Using Railway

1. Push your code to GitHub
2. Connect your GitHub repo to Railway
3. Add environment variables in Railway dashboard
4. Deploy!

### Using your own server

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Next Steps

1. **Read the README**: For detailed API documentation
2. **Check the source code**: To understand how it works
3. **Submit tasks**: Wait for requests from the evaluation server
4. **Debug issues**: Check logs in the console output

## Getting Help

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Console Logs**: Watch for errors in the terminal running the server

## Key Files

- `main.py`: FastAPI application entry point
- `src/round1.py`: Handles initial task requests
- `src/round2.py`: Handles revision requests
- `src/push_llm_code.py`: LLM-based code generation
- `src/create_repo.py`: GitHub repository management
- `.env.example`: Template for environment variables

Good luck! 🚀
