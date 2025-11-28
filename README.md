# IntelliRoute – AI-Powered Customer Feedback Router

IntelliRoute is an AI-powered tool that analyzes customer feedback, generates a summary, and automatically assigns the correct routing tag (Urgent, Billing, Bug Report, Feature Request, etc.).  
It helps support teams instantly triage issues and view all classified tickets in a real-time dashboard powered by Firebase.

---

## 🚀 Features

- AI-generated summary using Hugging Face models  
- Automatic routing tag detection (zero-shot classification)  
- Real-time ticket dashboard (Firestore live listeners)  
- Django backend + TailwindCSS UI  
- Error-safe retrying analyzer logic  
- Fully deployable on Render + Firebase  

---

## 🧠 How It Works

1. User enters customer feedback.  
2. Django backend sends text to Hugging Face API.  
3. AI returns:
   - Summary  
   - Highest-priority routing tag  
4. Ticket is saved in Firebase Firestore.  
5. Dashboard updates live with the new ticket.

---

## 📂 Project Structure

```
intelliroute_project/
│
├── core/
│   ├── templates/
│   │   ├── index.html
│   │   └── dashboard.html
│   ├── views.py
│   ├── urls.py
│   └── static/
│       └── css/styles.css
│
├── serviceAccountKey.json        # Firebase Admin key (excluded from repo)
├── requirements.txt
└── README.md
```

---

## ⚙️ Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Technologies used:

- Django  
- Firebase Admin SDK  
- Hugging Face Inference API  
- Requests  
- TailwindCSS  
- Gunicorn (for deployment)

---

## 🔧 Environment Variables

Create a `.env` file in project root:

```
HF_API_TOKEN=your_huggingface_api_key
```

Add your Firebase Admin key at:

```
/serviceAccountKey.json
```

---

## ▶️ Run Locally

```bash
python manage.py runserver
```

App will be available at:

```
http://127.0.0.1:8000/
```

Dashboard will be available at:
```
http://127.0.0.1:8000/dashboard/
```

---

## 🌐 Deployment

### Deploy Backend on Render
1. Push project to GitHub  
2. Create a new **Render Web Service**  
3. Add env var: `HF_API_TOKEN=your_token`  
4. Deploy

### Dashboard
The Firebase-powered dashboard updates instantly with no extra hosting requirements.

---

## 📊 Live Dashboard Features

- Real-time updates with Firestore  
- Prioritized ticket sorting  
- Urgent-only filter  
- Clean responsive UI  

---

## ⭐ Roadmap

- Add authentication  
- Multi-team routing logic  
- Notifications (Slack / Email)  
- Export tickets as CSV  

---

## 🤝 Contributing

Pull requests and feature suggestions are welcome!  
If you like this project, please ⭐ star the repo.

---

## 📄 License

MIT License.
