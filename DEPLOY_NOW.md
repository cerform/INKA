# 🚀 DEPLOY NOW

Your INKA project is ready for production deployment!

## ⚡ Super Quick Start (2 minutes)

```bash
# 1. Login to Google Cloud
gcloud auth login

# 2. Go to project folder
cd /Users/simanbekov/projects/inka

# 3. Deploy!
bash scripts/deploy-gcp-cloudbuild.sh inka-api europe-west1 tattoo-480007

# 4. Get your URL (displayed at the end)
# Visit: https://inka-api-xxxxx.a.run.app/
```

**That's it!** Your landing page goes live in 5-10 minutes.

---

## 📖 Full Documentation

- **Quick Start**: Read [FIRST_DEPLOYMENT.md](FIRST_DEPLOYMENT.md)
- **Complete Guide**: Read [docs/GOOGLE_CLOUD_RUN_DEPLOYMENT.md](docs/GOOGLE_CLOUD_RUN_DEPLOYMENT.md)
- **What Was Done**: Read [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **Details**: Check [DEPLOYMENT_READY.txt](DEPLOYMENT_READY.txt)

---

## ✨ What You Get

✅ Modern landing page with first setup  
✅ Fully integrated with existing API  
✅ Auto-scaling (1-50 instances)  
✅ Health checks and monitoring  
✅ Production-ready configuration  

---

## 🔗 Access Points After Deployment

```
Landing Page:     https://inka-api-xxx.a.run.app/
API Docs:         https://inka-api-xxx.a.run.app/docs
Health Check:     https://inka-api-xxx.a.run.app/health
Setup API:        https://inka-api-xxx.a.run.app/api/v1/setup
```

---

## 💡 Pro Tips

**Monitor deployment:**
```bash
gcloud run logs read inka-api --follow
```

**Update after changes:**
```bash
bash scripts/deploy-gcp-cloudbuild.sh inka-api europe-west1 tattoo-480007
```

**Rollback if needed:**
```bash
gcloud run services update-traffic inka-api --to-revisions=PREVIOUS=100
```

---

**Ready?** → Run the deployment command above! 🎉
