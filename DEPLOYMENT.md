# Deployment Checklist — Tharun AI Portfolio v1

## Backend (Render.com)
1. Push code to GitHub (main branch)
2. Render dashboard → New → Web Service
3. Connect GitHub repo
4. Settings:
   - Name: tharun-ai-backend
   - Region: Singapore
   - Branch: main
   - Root Directory: backend
   - Runtime: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   - Plan: Free
5. Add ALL environment variables from .env (manually, one by one)
6. Add FRONTEND_URL — will update after Vercel deploy
7. Deploy — wait for build to complete
8. Test: https://your-service.onrender.com/health

## Frontend (Vercel)
1. Vercel dashboard → New Project
2. Import GitHub repo
3. Settings:
   - Root Directory: frontend
   - Framework: Next.js
   - Build Command: npm run build
   - Output Directory: .next
4. Environment Variables:
   - NEXT_PUBLIC_BACKEND_URL=https://your-service.onrender.com
   - NEXT_PUBLIC_BACKEND_WS_URL=wss://your-service.onrender.com
5. Deploy
6. Copy the Vercel URL (e.g. https://tharun-ai.vercel.app)

## Final Step — Update CORS
1. Go back to Render → Environment Variables
2. Update FRONTEND_URL to your real Vercel URL
3. Manual redeploy (Render → Manual Deploy → Deploy latest commit)

## Post-Deploy Smoke Test
- [ ] GET /health → 200
- [ ] Frontend loads at Vercel URL
- [ ] Type "hi" → instant response
- [ ] Ask about TaxSetu → grounded RAG response
- [ ] Ask "how can I contact you" → email action button appears
- [ ] Click mic → grant permission → speak → get response
- [ ] Download resume button works
- [ ] Mobile view — sidebar collapses correctly

## Known Limitations (v1)
- Gemini free tier quota may cause slower responses under load (falls back to Groq)
- Render free tier cold starts after 15 min inactivity (~30s first request)
- ElevenLabs free tier limited — falls back to Web Speech API
- Wake word removed in v1 — manual mic click only
