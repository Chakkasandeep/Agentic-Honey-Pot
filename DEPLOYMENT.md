# 🚀 Complete Deployment Guide

## Step-by-Step Instructions for Deploying Your Honeypot API

---

## 📋 Pre-Deployment Checklist

- [ ] Groq API Key obtained from https://console.groq.com/keys
- [ ] Generated secure HONEYPOT_API_KEY
- [ ] Tested locally with `test_api.py`
- [ ] All tests passing

---

## 🎯 Option 1: Railway.app (RECOMMENDED)

### Why Railway?
✅ Free tier available  
✅ Automatic HTTPS  
✅ Easy environment variables  
✅ Fast deployment (2 minutes)  
✅ Great for hackathons  

### Steps:

#### 1. Create Railway Account
- Go to https://railway.app/
- Sign up with GitHub

#### 2. Install Railway CLI (Optional but recommended)
```bash
npm i -g @railway/cli
```

#### 3. Deploy via GitHub (Easiest)

**a. Push code to GitHub:**
```bash
cd honeypot-api
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/honeypot-api.git
git push -u origin main
```

**b. Deploy on Railway:**
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `honeypot-api` repository
5. Railway will auto-detect Python and deploy

**c. Add Environment Variables:**
1. Click on your deployed service
2. Go to "Variables" tab
3. Add:
   - `HONEYPOT_API_KEY` = your-generated-secure-key
   - `GROQ_API_KEY` = gsk_your_groq_api_key

**d. Get Your Public URL:**
1. Go to "Settings" tab
2. Under "Networking", click "Generate Domain"
3. You'll get: `https://your-app-name.up.railway.app`

**e. Test Your Deployment:**
```bash
curl https://your-app-name.up.railway.app/health
```

#### 4. Deploy via CLI (Alternative)

```bash
cd honeypot-api
railway login
railway init
railway up
railway variables set HONEYPOT_API_KEY=your-key
railway variables set GROQ_API_KEY=gsk_your_key
railway open  # Opens your app in browser
```

---

## 🎯 Option 2: Render.com

### Why Render?
✅ Free tier with 750 hours/month  
✅ Auto-deploy from GitHub  
✅ Easy setup  

### Steps:

#### 1. Prepare Your Code
Create `render.yaml` in your project:
```yaml
services:
  - type: web
    name: honeypot-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: HONEYPOT_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
```

#### 2. Push to GitHub
```bash
git add render.yaml
git commit -m "Add Render config"
git push
```

#### 3. Deploy on Render
1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Render auto-detects settings
5. Add environment variables:
   - `HONEYPOT_API_KEY`
   - `GROQ_API_KEY`
6. Click "Create Web Service"

#### 4. Get Your URL
Your app will be at: `https://honeypot-api-xxxx.onrender.com`

---

## 🎯 Option 3: Fly.io

### Why Fly.io?
✅ Global edge network  
✅ Fast performance  
✅ Free tier available  

### Steps:

#### 1. Install Fly CLI
```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

#### 2. Login and Launch
```bash
cd honeypot-api
fly auth login
fly launch
```

Answer the prompts:
- App name: `your-honeypot-api`
- Region: Choose closest to India (Singapore/Mumbai)
- PostgreSQL: No
- Redis: No

#### 3. Set Environment Variables
```bash
fly secrets set HONEYPOT_API_KEY=your-key
fly secrets set GROQ_API_KEY=gsk_your_key
```

#### 4. Deploy
```bash
fly deploy
```

#### 5. Get Your URL
```bash
fly status
# URL will be: https://your-honeypot-api.fly.dev
```

---

## 🎯 Option 4: Heroku

### Steps:

#### 1. Create `Procfile`
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 2. Create `runtime.txt`
```
python-3.11.7
```

#### 3. Deploy
```bash
heroku login
heroku create your-honeypot-api
git push heroku main
heroku config:set HONEYPOT_API_KEY=your-key
heroku config:set GROQ_API_KEY=gsk_your_key
```

---

## ✅ Post-Deployment Verification

### 1. Test Health Endpoint
```bash
curl https://your-deployed-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Agentic Honeypot API",
  "version": "1.0.0",
  "active_sessions": 0
}
```

### 2. Test Honeypot Endpoint
```bash
curl -X POST https://your-deployed-url.com/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-honeypot-api-key" \
  -d '{
    "sessionId": "verification-test",
    "message": {
      "sender": "scammer",
      "text": "Your account will be blocked. Verify at http://fake.com",
      "timestamp": "2026-01-31T10:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS"}
  }'
```

Expected response:
```json
{
  "status": "success",
  "reply": "What? Why is my account being blocked?"
}
```

### 3. Update Test Script
```python
# In test_api.py, change:
API_URL = "https://your-deployed-url.com/honeypot"
API_KEY = "your-honeypot-api-key"
```

Run tests:
```bash
python test_api.py
```

---

## 📤 Submit to GUVI

### What to Submit:

1. **Public API URL:**
   ```
   https://your-app.railway.app/honeypot
   ```

2. **API Key:**
   ```
   your-honeypot-api-key
   ```

3. **Test with GUVI Tester:**
   - Go to GUVI hackathon dashboard
   - Find "API Endpoint Tester"
   - Enter your URL and API key
   - Click "Test Honeypot Endpoint"
   - Verify it returns "success"

---

## 🐛 Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'groq'"
**Solution:**
```bash
pip install -r requirements.txt
# Or specifically:
pip install groq
```

### Issue 2: Deployment fails with "Port already in use"
**Solution:**
- Railway/Render/Fly handle ports automatically via `$PORT`
- Make sure your app uses `port = os.getenv("PORT", 8000)`

### Issue 3: "Invalid API key" in production
**Solution:**
- Verify environment variables are set correctly
- Check Railway/Render dashboard → Variables
- Redeploy after setting variables

### Issue 4: Slow responses (>5 seconds)
**Solution:**
- Groq should be fast (<2s)
- Check Groq API status: https://status.groq.com/
- Verify your Groq API key is valid
- Check server logs for errors

### Issue 5: Final report not being sent
**Solution:**
- Check server logs for "Final report sent" message
- Verify GUVI endpoint is reachable
- Ensure conversation meets end conditions (5+ turns or good intel)

---

## 📊 Performance Optimization

### 1. Reduce Response Time
```python
# In main.py, reduce max_tokens:
max_tokens=80  # Instead of 100
```

### 2. Faster Groq Model
```python
# Use mixtral-8x7b instead of llama-3.3-70b for speed:
model="mixtral-8x7b-32768"
```

### 3. Caching (Advanced)
```python
# Add Redis for session storage instead of in-memory
import redis
r = redis.Redis(host='localhost', port=6379)
```

---

## 🏆 Final Checklist Before Submission

- [ ] API deployed and accessible publicly
- [ ] Health endpoint returns 200
- [ ] Honeypot endpoint requires x-api-key header
- [ ] Scam detection working (test with sample messages)
- [ ] AI agent generating natural responses
- [ ] Intelligence extraction working (check logs)
- [ ] Final report callback implemented
- [ ] Tested with GUVI endpoint tester
- [ ] All environment variables set correctly
- [ ] Server logs showing no errors
- [ ] Response time < 3 seconds
- [ ] Submitted URL and API key to GUVI

---

## 🎉 You're Ready!

Your honeypot API is now:
- ✅ Deployed and publicly accessible
- ✅ Secured with API key authentication
- ✅ Detecting scams with high accuracy
- ✅ Engaging scammers autonomously
- ✅ Extracting intelligence effectively
- ✅ Reporting results to GUVI

**Good luck with the hackathon! 🚀**

---

## 📞 Need Help?

- **Groq Issues:** https://console.groq.com/docs
- **Railway Support:** https://docs.railway.app/
- **Render Support:** https://render.com/docs
- **Fly.io Support:** https://fly.io/docs/

---

## 💡 Pro Tips

1. **Monitor Your Deployment:**
   - Railway: Check logs in dashboard
   - Render: View logs in real-time
   - Fly.io: `fly logs`

2. **Cost Management:**
   - All platforms have free tiers
   - Groq free tier: 14,400 requests/day
   - Should be plenty for hackathon testing

3. **Debugging:**
   - Add more logging to track issues
   - Use `logger.info()` liberally
   - Check both app logs and platform logs

4. **Testing Strategy:**
   - Test locally first
   - Deploy to staging (if available)
   - Test production endpoint
   - Submit to GUVI only when confident