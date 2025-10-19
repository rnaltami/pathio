# Pathio v2 - "Perplexity of Jobs"

## 🎉 What We Built

A complete redesign of Pathio inspired by Perplexity's clean, conversational interface. Now users can:

1. **Explore Careers** through AI chat (for undecided users)
2. **Search Real Jobs** from 3 free APIs (200+ jobs available)
3. **Get Personalized Matches** based on their resume
4. **Choose Their Path**: Prepare first OR apply immediately
5. **Tailor Applications** with existing AI tools

## 🚀 How to Run the New Version

### Start Backend (Terminal 1):
```bash
cd /Users/roxana/CodingProjects/pathio/backend
uvicorn app.main:app --reload --port 8000
```

### Start New Frontend (Terminal 2):
```bash
cd /Users/roxana/CodingProjects/pathio/frontend
streamlit run app_v2.py
```

## 📁 Files Changed/Created

### New Files:
- `frontend/app_v2.py` - New Perplexity-inspired UI
- `scripts/test_job_apis.py` - API testing script
- `NEW_VERSION_README.md` - This file

### Modified Files:
- `backend/app/routers/jobs.py` - Now fetches from 3 real job APIs
- `backend/app/main.py` - Registered jobs router

### Original Files (Untouched):
- `frontend/app.py` - Your original app (still works!)
- All other backend files

## 🎨 Design Features

### Perplexity-Inspired Elements:
- ✅ Dark, clean interface
- ✅ Centered search box as primary action
- ✅ Minimal, card-based job listings
- ✅ Smooth transitions between views
- ✅ Chat-style career exploration
- ✅ No clutter, focus on content

### Color Scheme:
- Background: Deep blacks (#0A0A0A, #151515)
- Text: Light grays (#ECECEC, #B4B4B4)
- Accent: Blue gradient (#3B82F6 → #8B5CF6)
- Borders: Subtle (#2A2A2A)

## 🔌 Job APIs Integrated

### 1. RemoteOK
- **Jobs:** ~99 remote/tech jobs
- **Cost:** FREE forever
- **Status:** ✅ Working

### 2. TheMuse
- **Jobs:** 467,740+ total available
- **Cost:** FREE (public endpoint)
- **Status:** ✅ Working

### 3. Arbeitnow
- **Jobs:** ~100 Europe/remote jobs
- **Cost:** FREE forever
- **Status:** ✅ Working

**Total: 200+ jobs from free sources!**

## 🎯 User Flow

```
Landing Page
├─> "What job are you looking for?" [Search Box]
├─> "Not Sure? Chat with AI" [Career Exploration]
└─> "Have Resume? Upload" [For Personalized Matches]
         ↓
    Job Search Results (from 3 APIs)
         ↓
    Select Job → View Details
         ↓
    Choose Path:
    ├─> "Need to Prepare?" → Action Plan
    └─> "Ready to Apply?" → Tailor Resume + Cover Letter
```

## ✅ Features Completed

- [x] Perplexity-inspired UI design
- [x] Landing page with search
- [x] Real job API integration (3 sources)
- [x] Job search and results display
- [x] Job detail view
- [x] Resume upload/storage
- [x] Career chat interface structure
- [x] Decision point (prepare vs. apply)

## 🚧 Features In Progress

- [ ] Connect "Prepare" path to existing `/better-candidate` endpoint
- [ ] Connect "Apply" path to existing `/quick-tailor` endpoint
- [ ] Enhance career chat with domain-specific prompts
- [ ] Add job bookmarking/saving
- [ ] Improve match scoring algorithm

## 💡 Future Enhancements

- [ ] User accounts (save resume, track applications)
- [ ] Career progress tracking
- [ ] More job sources (paid APIs when ready)
- [ ] Email job alerts
- [ ] Interview prep assistance
- [ ] Salary negotiation guidance

## 🎨 Design Philosophy

**Like Perplexity, but for careers:**
- Start with a question, not a form
- AI guides you through discovery
- Clear, actionable results
- Minimal UI, maximum impact
- Conversational, not transactional

## 📝 Notes for Development

### Resume Persistence
- Stored in `st.session_state["user_resume"]`
- Persists throughout user journey
- Used for personalized job matching
- Future: Save to database with user accounts

### API Rate Limiting
- RemoteOK: Be conservative, no published limit
- TheMuse: Unknown limit, seems generous
- Arbeitnow: Reasonable limits
- All are truly free (no trials)

### Switching Between Old and New
- Old version: `streamlit run app.py`
- New version: `streamlit run app_v2.py`
- Both work independently

## 🐛 Known Issues

None yet! Fresh build.

## 📞 Next Steps

1. Test the new UI locally
2. Connect prepare/apply flows to existing backend
3. Deploy to production when ready
4. Monitor API usage and reliability
5. Gather user feedback

---

**Built with:** Streamlit, FastAPI, OpenAI, RemoteOK API, TheMuse API, Arbeitnow API

