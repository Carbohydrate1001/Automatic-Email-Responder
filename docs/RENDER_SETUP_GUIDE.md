# Detailed Render Setup Guide

## Prerequisites

Before starting, make sure you have:
- [ ] GitHub account with your code pushed to a repository
- [ ] Azure App Registration credentials (Client ID, Client Secret)
- [ ] OpenAI API key
- [ ] Render account (free - sign up at https://render.com)

---

## Part 1: Initial Render Setup

### Step 1: Create Render Account

1. Go to https://render.com
2. Click **"Get Started"** or **"Sign Up"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if required

### Step 2: Connect GitHub Repository

1. After logging in, you'll see the Render Dashboard
2. Click **"New +"** button in the top right
3. Select **"Blueprint"** from the dropdown
4. Click **"Connect GitHub"** if not already connected
5. Authorize Render to access your GitHub account
6. Select your repository: `Automatic-Email-Responder`
7. Click **"Connect"**

### Step 3: Deploy from Blueprint (render.yaml)

1. Render will automatically detect your `render.yaml` file
2. You'll see a preview showing:
   - **email-responder-backend** (Web Service)
   - **email-responder-frontend** (Static Site)
3. Review the configuration
4. Click **"Apply"** to create both services

**What happens next:**
- Render creates two services simultaneously
- Backend starts installing Python dependencies (~3-5 minutes)
- Frontend starts installing npm packages and building (~2-3 minutes)
- You'll see both services in your dashboard

---

## Part 2: Configure Backend Service

### Step 4: Get Backend URL

1. In your Render Dashboard, click on **"email-responder-backend"**
2. Wait for the deployment to complete (status: "Live" with green dot)
3. At the top, you'll see your backend URL:
   ```
   https://email-responder-backend.onrender.com
   ```
4. **Copy this URL** - you'll need it multiple times

### Step 5: Test Backend Health Check

1. Open a new browser tab
2. Visit: `https://email-responder-backend.onrender.com/health`
3. You should see:
   ```json
   {"status": "ok"}
   ```
4. If you see this, the backend is running correctly!

**Note:** First request may take 30 seconds if the service was sleeping (free tier).

### Step 6: Configure Backend Environment Variables

1. In the backend service page, click **"Environment"** in the left sidebar
2. You'll see some variables already set from `render.yaml`
3. Click **"Add Environment Variable"** for each of the following:

#### Required Variables to Add/Update:

**Azure Credentials:**
```
Key: AZURE_CLIENT_ID
Value: 29353893-0dc6-4537-a98a-5d87c59f8f1b
(or your actual Azure Client ID)
```

```
Key: AZURE_CLIENT_SECRET
Value: [Your Azure Client Secret]
(from your .env file or Azure Portal)
```

```
Key: AZURE_REDIRECT_URI
Value: https://email-responder-backend.onrender.com/auth/callback
(replace with your actual backend URL)
```

**OpenAI Credentials:**
```
Key: OPENAI_API_KEY
Value: [Your OpenAI API Key]
(from your .env file)
```

**Frontend URL (will update later):**
```
Key: FRONTEND_URL
Value: https://email-responder-frontend.onrender.com
(placeholder - will update after frontend deploys)
```

4. After adding each variable, click **"Save Changes"**
5. Render will automatically redeploy the backend

**Variables already set by render.yaml:**
- `FLASK_SECRET_KEY`: demo-secret-key-for-classroom
- `FLASK_DEBUG`: False
- `FLASK_PORT`: 10000
- `AZURE_TENANT_ID`: consumers
- `OPENAI_BASE_URL`: https://api.n1n.ai/v1
- `OPENAI_MODEL`: gpt-4o-mini
- `CONFIDENCE_THRESHOLD`: 0.75
- `DEMO_MODE`: True

---

## Part 3: Configure Frontend Service

### Step 7: Get Frontend URL

1. Go back to Render Dashboard
2. Click on **"email-responder-frontend"**
3. Wait for the build to complete (status: "Live")
4. At the top, you'll see your frontend URL:
   ```
   https://email-responder-frontend.onrender.com
   ```
5. **Copy this URL** - you'll need it

### Step 8: Configure Frontend Environment Variable

1. In the frontend service page, click **"Environment"** in the left sidebar
2. Click **"Add Environment Variable"**
3. Add:
   ```
   Key: VITE_API_BASE_URL
   Value: https://email-responder-backend.onrender.com
   (use your actual backend URL from Step 4)
   ```
4. Click **"Save Changes"**
5. Render will automatically rebuild and redeploy the frontend (~2-3 minutes)

### Step 9: Update Backend with Frontend URL

1. Go back to **"email-responder-backend"** service
2. Click **"Environment"** in the left sidebar
3. Find the `FRONTEND_URL` variable
4. Click the **Edit** icon (pencil)
5. Update the value to your actual frontend URL:
   ```
   https://email-responder-frontend.onrender.com
   ```
6. Click **"Save Changes"**
7. Backend will redeploy automatically

---

## Part 4: Update Azure App Registration

### Step 10: Add Production Redirect URI

1. Go to **Azure Portal**: https://portal.azure.com
2. Navigate to **Azure Active Directory** → **App registrations**
3. Find your app (Client ID: `29353893-0dc6-4537-a98a-5d87c59f8f1b`)
4. Click on it to open
5. In the left sidebar, click **"Authentication"**
6. Under **"Platform configurations"** → **"Web"** → **"Redirect URIs"**
7. Click **"Add URI"**
8. Add your production callback URL:
   ```
   https://email-responder-backend.onrender.com/auth/callback
   ```
9. Keep the localhost URI for local development:
   ```
   http://localhost:5005/auth/callback
   ```
10. Click **"Save"** at the bottom

---

## Part 5: Verification and Testing

### Step 11: Test Backend Endpoints

Open these URLs in your browser:

1. **Health Check:**
   ```
   https://email-responder-backend.onrender.com/health
   ```
   Expected: `{"status": "ok"}`

2. **Root Endpoint:**
   ```
   https://email-responder-backend.onrender.com/
   ```
   Expected: `{"message": "Automated Email Reply System API", "status": "running"}`

3. **Auth Status:**
   ```
   https://email-responder-backend.onrender.com/auth/status
   ```
   Expected: `{"authenticated": false}` (before login)

### Step 12: Test Frontend Application

1. Open your frontend URL in a browser:
   ```
   https://email-responder-frontend.onrender.com
   ```

2. You should see the login page

3. **Open Browser DevTools** (F12) → **Console** tab
   - Check for any errors
   - Should see no CORS errors

4. **Network Tab** in DevTools
   - Click login button
   - Verify requests are going to your backend URL

### Step 13: Test Full Authentication Flow

1. On the frontend, click **"Login with Microsoft"**
2. You'll be redirected to Microsoft login page
3. Sign in with your Microsoft account
4. You should be redirected back to the app
5. You should now see the email list page

**If authentication fails:**
- Check Azure redirect URI is correct
- Check backend logs in Render dashboard
- Verify `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` are correct

### Step 14: Test Email Functionality

1. Click **"Fetch Emails"** button
2. System should fetch emails from your Outlook inbox
3. Emails should appear in the list
4. Try viewing an email detail
5. Test approve/reject/delete operations
6. Check the Dashboard for statistics

---

## Part 6: Monitoring and Maintenance

### Viewing Logs

**Backend Logs:**
1. Go to backend service in Render Dashboard
2. Click **"Logs"** in the left sidebar
3. You'll see real-time logs of:
   - Startup messages
   - API requests
   - Errors and warnings
   - Database operations

**Frontend Logs:**
1. Go to frontend service in Render Dashboard
2. Click **"Logs"** in the left sidebar
3. You'll see build logs and deployment status

### Manual Redeploy

If you need to redeploy manually:

1. Go to the service page
2. Click **"Manual Deploy"** button in the top right
3. Select **"Clear build cache & deploy"** if you want a fresh build
4. Click **"Deploy"**

### Updating Environment Variables

1. Go to service → **"Environment"**
2. Edit any variable
3. Click **"Save Changes"**
4. Service will automatically redeploy

---

## Part 7: Sharing with Students

### Step 15: Prepare for Classroom Demo

1. **Get your frontend URL:**
   ```
   https://email-responder-frontend.onrender.com
   ```

2. **Test the full flow yourself first:**
   - Login
   - Fetch emails
   - View email details
   - Test all features

3. **Keep the app awake during class:**
   - Open the frontend URL in a browser tab
   - Keep it open during your presentation
   - This prevents the backend from sleeping

4. **Share the URL with students:**
   - Write it on the board
   - Send it in chat/email
   - Students can access it directly from any device

### Step 16: Classroom Demo Tips

**Before class:**
- [ ] Test the deployment 30 minutes before class
- [ ] Make sure you have demo data (fetch some emails)
- [ ] Open the app in a browser tab to keep it awake

**During class:**
- [ ] Warn students about 30-second wake-up time if app was sleeping
- [ ] Show the login flow first
- [ ] Demonstrate fetching emails
- [ ] Show the classification and auto-reply features
- [ ] Let students try it themselves

**After class:**
- [ ] Database will reset on next deployment (ephemeral storage)
- [ ] No cleanup needed - it's a demo environment

---

## Troubleshooting

### Issue: Backend shows "Service Unavailable"

**Solution:**
1. Check Render Dashboard → Backend service → Logs
2. Look for error messages during startup
3. Common issues:
   - Missing environment variables
   - Python dependency installation failed
   - Port binding issues

**Fix:**
- Verify all environment variables are set
- Check `requirements.txt` is correct
- Ensure `FLASK_PORT=10000`

### Issue: Frontend shows blank page

**Solution:**
1. Open browser DevTools → Console
2. Look for errors
3. Common issues:
   - CORS errors (backend `FRONTEND_URL` not set correctly)
   - API connection errors (wrong `VITE_API_BASE_URL`)
   - Build errors

**Fix:**
- Verify `VITE_API_BASE_URL` points to correct backend URL
- Verify backend `FRONTEND_URL` matches frontend URL
- Check frontend build logs in Render

### Issue: Login redirects to wrong URL

**Solution:**
1. Check Azure redirect URI matches backend URL exactly
2. Check `AZURE_REDIRECT_URI` environment variable in backend
3. Must be: `https://your-backend.onrender.com/auth/callback`

**Fix:**
- Update Azure App Registration redirect URI
- Update backend `AZURE_REDIRECT_URI` environment variable
- Redeploy backend

### Issue: CORS errors in browser console

**Solution:**
```
Access to XMLHttpRequest at 'https://backend...' from origin 'https://frontend...' 
has been blocked by CORS policy
```

**Fix:**
1. Go to backend service → Environment
2. Verify `FRONTEND_URL` is set to your frontend URL
3. Must match exactly (including https://)
4. Redeploy backend

### Issue: Backend sleeps during demo

**Solution:**
- Free tier sleeps after 15 minutes of inactivity
- First request takes ~30 seconds to wake up

**Fix:**
- Keep a browser tab open during class
- Or upgrade to Starter plan ($7/month) to prevent sleeping
- Warn students about potential 30s delay

### Issue: Database is empty after redeploy

**Solution:**
- This is expected behavior (ephemeral storage)
- Database resets on every deployment

**Fix:**
- This is acceptable for classroom demo
- Fetch emails again after deployment
- Or upgrade to use Render Disk for persistence

---

## Quick Reference

### Your URLs (Update these after deployment)

```
Backend:  https://email-responder-backend.onrender.com
Frontend: https://email-responder-frontend.onrender.com
Health:   https://email-responder-backend.onrender.com/health
```

### Environment Variables Checklist

**Backend (13 variables):**
- [x] FLASK_SECRET_KEY (auto-set)
- [x] FLASK_DEBUG (auto-set)
- [x] FLASK_PORT (auto-set)
- [ ] AZURE_CLIENT_ID (manual)
- [ ] AZURE_CLIENT_SECRET (manual)
- [x] AZURE_TENANT_ID (auto-set)
- [ ] AZURE_REDIRECT_URI (manual)
- [ ] OPENAI_API_KEY (manual)
- [x] OPENAI_BASE_URL (auto-set)
- [x] OPENAI_MODEL (auto-set)
- [x] CONFIDENCE_THRESHOLD (auto-set)
- [x] DEMO_MODE (auto-set)
- [ ] FRONTEND_URL (manual - after frontend deploys)

**Frontend (1 variable):**
- [ ] VITE_API_BASE_URL (manual - after backend deploys)

### Azure Configuration Checklist

- [ ] Add production redirect URI: `https://your-backend.onrender.com/auth/callback`
- [ ] Keep localhost URI: `http://localhost:5005/auth/callback`

---

## Cost Summary

- **Backend Web Service (Free tier):** $0/month
- **Frontend Static Site:** $0/month
- **Total:** $0/month

**Free tier limitations:**
- Backend sleeps after 15 min inactivity
- 750 hours/month (enough for classroom demos)
- Ephemeral storage (database resets on redeploy)

**Optional upgrades:**
- Starter plan ($7/month): No sleeping, always available
- Render Disk ($1/GB/month): Persistent database storage

---

## Support

If you encounter issues:

1. **Check Render Logs:** Service → Logs (most issues show here)
2. **Check Browser Console:** F12 → Console (for frontend errors)
3. **Render Documentation:** https://render.com/docs
4. **Render Community:** https://community.render.com

---

## Summary

You've successfully deployed your Email Responder system to Render! 🎉

**What you have:**
- ✅ Backend API running on Render (free tier)
- ✅ Frontend app accessible via public URL
- ✅ Azure OAuth authentication configured
- ✅ OpenAI integration working
- ✅ Ready for classroom demonstration

**Share this URL with your students:**
```
https://email-responder-frontend.onrender.com
```

They can access it from any device with a browser - no installation needed!
