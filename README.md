# Green Finance Risk Prediction Web Application

A FastAPI web application for predicting green finance risks based on sustainability impact areas and company information.

## Features

- User authentication (login/signup)
- Company selection and information display
- Impact area input for prediction
- Machine learning model for risk prediction
- LLM-powered detailed green finance reports
- Dashboard for viewing prediction history
- Responsive design for all devices

## Project Structure

```
├── app/
│   ├── database/          # Database models and connection
│   ├── models/            # ML and LLM models
│   ├── routers/           # FastAPI route handlers
│   ├── static/            # Static assets (CSS, JS)
│   ├── templates/         # HTML templates
│   ├── utils/             # Utility functions
│   ├── config.py          # Configuration settings
│   └── main.py            # Main application entry point
├── data/                  # Company data
├── final_models/          # Saved ML models
├── .env                   # Environment variables
├── requirements.txt       # Dependencies
└── README.md              # Project documentation
```

## Setup Instructions

1. Clone the repository
2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```
   python -m app.main
   ```
6. Open your browser and navigate to http://localhost:8000

## Usage

1. Create an account or log in
2. Select a company from the dropdown
3. Adjust the impact area values as needed
4. Click "Predict" to generate a risk assessment
5. View the prediction results with ESG score and risk probability
6. Check detailed LLM-generated recommendations
7. Visit the dashboard to view your prediction history

## Technologies Used

- FastAPI: Web framework for building the API
- SQLite: Database for storing user and prediction data
- SQLAlchemy: ORM for database interactions
- Jinja2: Templating engine for HTML
- Groq API: For LLM-powered report generation
- scikit-learn: For ML model predictions
- Bootstrap 5: For responsive UI design
- JavaScript/jQuery: For interactive frontend features

## License

MIT 