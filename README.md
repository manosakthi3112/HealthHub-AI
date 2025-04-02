# Fitness Management Platform

A web-based **Fitness Management Platform** that allows users to track their diet, watch exercise videos, and interact with an AI chatbot. The platform includes an **admin dashboard** for managing users, AI-generated workout reviews, content management, chatbot monitoring, and analytics.

## Features

### User Features

- **User Authentication**: Signup, login, and logout functionality.
- **Diet Tracking**: Users can add, view, and edit their daily meals.
- **Exercise Videos**: Browse and watch exercise videos.
- **AI Chatbot**: Get fitness-related suggestions via an AI chatbot.
- **Profile Management**: Edit user details.

### Admin Features

- **User Management**: View and manage registered users.
- **AI-Generated Workout Review**: Analyze users' workout history.
- **Content & Resource Management**: Manage diet plans and exercise videos.
- **Chatbot Monitoring**: Track user interactions with the AI chatbot.
- **User Analytics**: View total user count per day, month, and overall.

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask
- **Database**: MongoDB (PyMongo)
- **AI Integration**: Gemini Pro API
- **Authentication**: Flask Sessions

## Installation

### Prerequisites

- Python 3.x
- MongoDB

### Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/fitness-management-platform.git
   cd fitness-management-platform
   ```
2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set environment variables:
   ```sh
   export GENAI_API_KEY='your_api_key'
   export MONGO_URI='your_mongodb_connection_string'
   export SECRET_KEY='your_secret_key'
   ```
   *(For Windows: Use **`set`** instead of **`export`**)*)
5. Run the Flask application:
   ```sh
   python app.py
   ```
6. Open your browser and visit `http://127.0.0.1:5000`.

## API Endpoints

| Method    | Endpoint    | Description            |
| --------- | ----------- | ---------------------- |
| GET       | `/`         | Home Page              |
| GET, POST | `/register` | User Registration      |
| GET, POST | `/login`    | User Login             |
| GET       | `/logout`   | User Logout            |
| GET       | `/profile`  | User Profile           |
| GET, POST | `/add_diet` | Add a Meal Entry       |
| GET       | `/diet`     | View Diet Entries      |
| GET       | `/videos`   | View Exercise Videos   |
| GET, POST | `/chat`     | AI Chatbot Interaction |
| GET, POST | `/admin`    | Admin Dashboard        |

---

Made with ❤️ by Manosakthi Thiyagarajan.

