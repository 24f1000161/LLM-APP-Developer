# LLM App Developer

A FastAPI application that generates and deploys web applications using OpenAI's GPT-5-nano. This server receives task requests from an evaluation platform, generates complete web applications, deploys them to GitHub Pages, and notifies the evaluation server with the results.

## Overview

This project automates the process of building and deploying web applications:

- **Round 1 (Build)**: Receives a task, generates complete web app code, creates GitHub repo, deploys to Pages
- **Round 2 (Revise)**: Updates existing app based on feedback, re-deploys changes

## Quick Start

### Prerequisites

- Python 3.10+
- Git
- GitHub account with personal access token
- OpenAI API key

### Installation

```bash
# Clone the repository
cd llm-app-developer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

Create a `.env` file:

```env
STUDENT_SECRET=your-student-secret
GITHUB_TOKEN=your-github-pat-token
GITHUB_USER=your-github-username
OPENAI_API_KEY=your-openai-api-key
HOST=0.0.0.0
PORT=8000
```

**Environment Variables:**
- `STUDENT_SECRET`: Secret for request verification
- `GITHUB_TOKEN`: GitHub Personal Access Token (with repo, delete_repo scopes)
- `GITHUB_USER`: Your GitHub username
- `OPENAI_API_KEY`: OpenAI API key from https://platform.openai.com/api-keys

### Running the Server

```bash
python main.py
```

Server will be available at `http://localhost:8000`

API documentation: http://localhost:8000/docs

## API Endpoints

### POST /submit

Main endpoint for task requests.

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "your-shared-secret",
  "task": "task-id-123",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Create a web app that...",
  "checks": ["Must have MIT license", "Should use Bootstrap 5"],
  "evaluation_url": "https://example.com/notify",
  "attachments": []
}
```

**Response (Success):**
```json
{
  "status": "success",
  "repo_url": "https://github.com/username/task-123",
  "pages_url": "https://username.github.io/task-123/",
  "commit_sha": "abc123def..."
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Error description"
}
```

### GET /health

Health check endpoint.

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-17T10:30:00+00:00",
  "secrets_configured": {
    "github_token": true,
    "openai_key": true,
    "student_secret": true
  }
}
```

### GET /

API information and available endpoints.

## How It Works

1. **Evaluation server** sends a task request to `/submit`
2. **Your server** validates the request and secret
3. **LLM generates** complete web app code (HTML, CSS, JavaScript)
4. **GitHub repo** is created and code is committed
5. **GitHub Pages** is enabled for hosting
6. **Evaluation server** is notified with repository details
7. **App is live** at `https://{username}.github.io/{repo-name}/`

## Features

- ✅ Automatic code generation using OpenAI GPT-5-nano
- ✅ GitHub repository creation and management
- ✅ Automatic GitHub Pages deployment
- ✅ Secret validation with timing attack protection
- ✅ Comprehensive error handling and logging
- ✅ Fallback to Google Gemini if OpenAI fails
- ✅ Support for file attachments (base64 encoded)

## Project Structure

```
main.py                    # FastAPI application entry point
src/
├── round1.py             # Build phase handler
├── round2.py             # Revise phase handler
├── create_repo.py        # GitHub repository management
├── push_llm_code.py      # LLM code generation
├── enable_github_pages.py # GitHub Pages configuration
├── validate_secrets.py   # Secret validation
├── config.py             # Configuration management
└── utils.py              # Utility functions
```

## Security

- **Secret Validation**: Uses constant-time comparison to prevent timing attacks
- **Token Protection**: GitHub tokens never exposed in logs
- **Environment Variables**: All credentials via `.env` (never hardcoded)
- **HTTPS**: Secure communication with GitHub API and OpenAI

## Error Handling

The application handles errors gracefully:

- Invalid requests → 400 Bad Request
- Authentication failures → 401 Unauthorized
- Server errors → 500 Internal Server Error with logging
- API failures → Automatic fallback and retry with exponential backoff

All errors are logged to console with timestamps.

## Troubleshooting

**"Invalid secret"**
- Verify `STUDENT_SECRET` in `.env` matches what was provided
- Check for extra whitespace in the environment variable

**"GitHub token expired"**
- Regenerate token at https://github.com/settings/tokens
- Ensure token has required scopes: `repo`, `delete_repo`

**"OPENAI_API_KEY not set"**
- Check `.env` file exists in project root
- Verify API key is correct and has remaining quota

**"Port already in use"**
- Change `PORT` in `.env` to a different port (e.g., 8001)
- Or kill existing process: `lsof -i :8000` (Unix) / `netstat -ano` (Windows)

## License

MIT License

## References

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [GitHub Pages](https://pages.github.com/)
- [GitHub API](https://docs.github.com/en/rest)
