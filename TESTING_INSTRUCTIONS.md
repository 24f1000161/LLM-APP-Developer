# Critical Environment Variables Check

## REQUIRED: Set these in your Hugging Face Space

Go to: https://huggingface.co/spaces/iamdivyam/LLM-app-developer/settings

### Required Secrets/Variables:

1. **GITHUB_USER** = `24f1000161`
   - This is YOUR GitHub username
   - Without this, repos will fail to create!

2. **GITHUB_TOKEN** = `ghp_...`
   - Your GitHub Personal Access Token
   - Must have `repo` and `workflow` scopes

3. **STUDENT_SECRET** = `your-secret-here`
   - The secret you shared in the Google Form
   - Used to authenticate incoming requests

4. **OPENAI_API_KEY** = `sk-proj-...`
   - Your OpenAI API key for GPT-5-nano

5. **GEMINI_API_KEY** = `...` (Optional but recommended)
   - Your Google Gemini API key for fallback

## To Run the Test:

```powershell
# Set your student secret locally
$env:STUDENT_SECRET = "your-actual-secret-from-hf-space"

# Run the end-to-end test
python instructor/test_e2e_repo_creation.py
```

This will:
1. ✅ Check if environment variables are configured
2. ✅ Send a real POST request with valid secret
3. ✅ Wait for GitHub repo creation
4. ✅ Verify repo exists at https://github.com/24f1000161/test-counter-app-XXXXXXXX
5. ✅ Check for LICENSE, README.md, index.html
6. ✅ Verify GitHub Pages is deployed

## Expected Result:

If everything works, you should see a new public repository created in your GitHub account:
- **URL**: https://github.com/24f1000161/test-counter-app-[timestamp]
- **Contents**: LICENSE, README.md, index.html, etc.
- **Pages**: https://24f1000161.github.io/test-counter-app-[timestamp]/

## If Test Fails:

Check:
1. Is `GITHUB_USER=24f1000161` set in HF Space?
2. Does `GITHUB_TOKEN` have `repo` permission?
3. Check HF Space logs for errors
