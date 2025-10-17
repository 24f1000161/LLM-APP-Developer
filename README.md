# LLM App Developer - Student Side

A FastAPI application that enables students to build and deploy web applications using LLM-assisted code generation with **Pydantic AI** and **OpenAI's GPT-4o**. This is the **student-side** implementation that receives tasks, generates code, and deploys to GitHub Pages.

## Overview

This project implements the **Build** and **Revise** phases of an automated code deployment system:

1. **Build Phase (Round 1)**: 
   - Receives a task request with brief and requirements
   - Generates a complete web application using Claude LLM
   - Creates a GitHub repository
   - Deploys to GitHub Pages
   - Notifies the evaluation server

2. **Revise Phase (Round 2)**:
   - Receives a revision request with updated requirements
   - Updates the existing application based on feedback
   - Re-deploys to GitHub Pages
   - Notifies the evaluation server of changes

## Architecture

```
main.py
├── /api/submit (POST)
│   ├── Validates secret
│   ├── Routes to round1() or round2()
│   └── Returns status
│
src/
├── round1.py          # Round 1 task handler
├── round2.py          # Round 2 revision handler
├── create_repo.py     # GitHub repository creation
├── push_llm_code.py   # LLM-based code generation
├── enable_github_pages.py  # GitHub Pages configuration
└── validate_secrets.py # Secret validation
```

## Setup

### Prerequisites

- Python 3.10+
- Git
- GitHub account with personal access token
- Anthropic API key (for Claude)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd llm-app-developer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Configure environment variables:**
   Create a `.env` file with:
   ```
   SECRET_KEY=your-student-secret
   GITHUB_TOKEN=your-github-pat-token
   GITHUB_USER=your-github-username
   ANTHROPIC_API_KEY=your-anthropic-api-key
   HOST=0.0.0.0
   PORT=8000
   ```

   **Environment Variables Explanation:**
   - `SECRET_KEY`: Secret shared with the evaluation server (for verification)
   - `GITHUB_TOKEN`: GitHub Personal Access Token (with repo, delete_repo, write:packages scopes)
   - `GITHUB_USER`: Your GitHub username
   - `OPENAI_API_KEY`: OpenAI API key from https://platform.openai.com/api-keys
   - `HOST`, `PORT`: Server configuration

### Running the Server

```bash
python main.py
```

The server will start at `http://0.0.0.0:8000`

Access the API documentation at: `http://localhost:8000/docs`

## API Endpoints

### POST /submit

Accepts task requests from the evaluation server.

**Request Payload:**
```json
{
  "email": "student@example.com",
  "secret": "your-shared-secret",
  "task": "captcha-solver-abc123",
  "round": 1,
  "nonce": "ab12-cd34-ef56",
  "brief": "Create a captcha solver...",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Page displays captcha image"
  ],
  "evaluation_url": "https://example.com/notify",
  "attachments": [
    {
      "name": "sample.png",
      "url": "data:image/png;base64,iVBORw0KGgoAAAANS..."
    }
  ]
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "repo_url": "https://github.com/username/task-abc123",
  "pages_url": "https://username.github.io/task-abc123/",
  "commit_sha": "abc123def456..."
}
```

**Error Response (400/401/500):**
```json
{
  "status": "error",
  "message": "Description of the error"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### GET /

API information endpoint.

## Features

### Round 1: Build Phase

1. **Request Validation**
   - Verifies all required fields
   - Validates secret against `SECRET_KEY`

2. **Code Generation**
   - Sends task brief and requirements to Claude API
   - Generates HTML, CSS, JavaScript, README, and LICENSE
   - Handles data URI attachments (base64 encoded)

3. **Repository Management**
   - Creates public GitHub repository
   - Initializes with MIT license
   - Configures git with student email

4. **Code Deployment**
   - Writes generated files and attachments to repo
   - Commits with descriptive messages
   - Pushes to GitHub main branch

5. **GitHub Pages**
   - Enables GitHub Pages for the repository
   - Configures to deploy from main branch root

6. **Evaluation Notification**
   - POSTs repository details to evaluation server
   - Includes repo URL, commit SHA, and Pages URL
   - Retries with exponential backoff on failure

### Round 2: Revise Phase

1. **Clones existing repository** from Round 1
2. **Generates updated code** based on revision brief
3. **Pushes changes** to the same repository
4. **Notifies evaluation server** with updated commit SHA

## Task Examples

### Sum of Sales
Students build a page that:
- Fetches data from CSV attachment
- Sums a sales column
- Displays total in an element
- Uses Bootstrap 5

### Markdown to HTML
Students build a page that:
- Converts Markdown to HTML using marked.js
- Highlights code blocks with highlight.js
- Renders in a designated container

### GitHub User Info
Students build a page that:
- Fetches GitHub user data via API
- Displays account creation date
- Supports optional ?token= parameter
- Uses Bootstrap for styling

## Code Quality

The generated applications follow these principles:

- **Minimal and Clean**: Only necessary code, no bloat
- **Well-Commented**: Clear explanations of functionality
- **Error Handling**: User feedback on failures
- **Responsive Design**: Works on mobile and desktop
- **Bootstrap 5**: Professional, consistent styling
- **Standards-Compliant**: Valid HTML5, CSS3, ES6+

## Security Considerations

1. **Secret Validation**: Uses constant-time comparison to prevent timing attacks
2. **Token Protection**: GitHub token never exposed in logs or responses
3. **Secure Git Operations**: Uses HTTPS with token authentication
4. **No Hardcoded Secrets**: All credentials via environment variables
5. **Repository Safety**: Public repos minimize security issues, checked for secrets

## Error Handling

The system includes comprehensive error handling:

- **Invalid requests**: 400 Bad Request
- **Authentication failures**: 401 Unauthorized
- **Server errors**: 500 Internal Server Error with detailed logging
- **GitHub API errors**: Caught and reported clearly
- **LLM API errors**: Graceful fallback with error message

Logs are written to console with timestamps and severity levels.

## Deployment

### Local Development

```bash
python main.py
```

### Production Deployment

Using Gunicorn + Uvicorn:

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t llm-app-developer .
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e GITHUB_TOKEN=your-token \
  -e GITHUB_USER=your-user \
  -e ANTHROPIC_API_KEY=your-key \
  llm-app-developer
```

## Workflow

```
┌─────────────────────────────────────┐
│  Evaluation Server Sends Request    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Student Server (/submit endpoint)  │
│  - Validate secret                  │
│  - Parse attachments                │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   Round 1        Round 2
   (Build)        (Revise)
        │             │
        ▼             ▼
   ┌─────────────────────────────────┐
   │ Generate code with Claude LLM   │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │ Create/Update GitHub Repo       │
   │ - Create repo (Round 1)         │
   │ - Clone repo (Round 2)          │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │ Write files & commit            │
   │ - HTML, CSS, JS                 │
   │ - README.md                     │
   │ - LICENSE (MIT)                 │
   │ - Attachments                   │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │ Push to GitHub & Enable Pages   │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │ POST to Evaluation Server       │
   │ - repo_url                      │
   │ - pages_url                     │
   │ - commit_sha                    │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │ Return 200 Success to Student   │
   └─────────────────────────────────┘
```

## Testing

### Test the Endpoint

Using curl:
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "secret": "your-secret",
    "task": "test-task-001",
    "round": 1,
    "nonce": "test-nonce",
    "brief": "Create a simple calculator web app",
    "checks": ["Has MIT license", "Displays calculator"],
    "evaluation_url": "https://example.com/notify",
    "attachments": []
  }'
```

## License

MIT License - See LICENSE file in generated repositories

## Support

For issues or questions:
1. Check the logs in the console output
2. Verify environment variables are set correctly
3. Ensure GitHub token has required permissions
4. Check that Anthropic API key is valid
5. Review the FastAPI documentation at `/docs`

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub API Reference](https://docs.github.com/en/rest)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [GitHub Pages](https://pages.github.com/)
