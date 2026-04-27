# Quick Deployment Guide for Render

## What Was Changed

### Backend Changes:
1. ✅ `backend/config.py` - Added `FRONTEND_URL` environment variable
2. ✅ `backend/app.py` - Dynamic CORS using `Config.FRONTEND_URL` and added `/health` endpoint

### Frontend Changes:
3. ✅ `frontend/src/api/index.ts` - Dynamic API URL using `VITE_API_BASE_URL`
4. ✅ `frontend/.env.development` - Local development configuration
5. ✅ `frontend/.env.production` - Production configuration (placeholder)

### New Files:
6. ✅ `render.yaml` - Render deployment configuration

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Deploy on Render
1. Go to https://render.com and sign in
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml` and create both services

### 3. Configure Environment Variables

**Backend Service** - Set these in Render dashboard:
- `AZURE_CLIENT_ID`: Your Azure app client ID
- `AZURE_CLIENT_SECRET`: Your Azure app secret
- `AZURE_REDIRECT_URI`: `https://your-backend.onrender.com/auth/callback`
- `OPENAI_API_KEY`: Your OpenAI API key
- `FRONTEND_URL`: `https://your-frontend.onrender.com` (after frontend deploys)

**Frontend Service** - Set this in Render dashboard:
- `VITE_API_BASE_URL`: `https://your-backend.onrender.com`

### 4. Update Azure App Registration
1. Go to Azure Portal → App Registrations
2. Add redirect URI: `https://your-backend.onrender.com/auth/callback`

### 5. Test the Deployment
- Backend health: `https://your-backend.onrender.com/health`
- Frontend: `https://your-frontend.onrender.com`

## Important Notes for Classroom Demo

- **Free tier**: Backend sleeps after 15 min inactivity (30s wake-up time)
- **Database**: Resets on each deployment (ephemeral storage)
- **Cost**: $0/month (completely free)
- **Tip**: Keep a browser tab open during class to prevent sleep

## URLs to Share with Students
After deployment, you'll get two URLs:
- Frontend: `https://email-responder-frontend.onrender.com` (students use this)
- Backend: `https://email-responder-backend.onrender.com` (API only)

Share the frontend URL with your students for easy access!
