# 🧭 FindNaija - Lost & Found Web App

FindNaija is a user-friendly web application designed to help people in Nigeria report and find lost items. Whether you've lost something or found an item, FindNaija provides a simple platform to connect with others.

---

## 🔐 Key Features

-Easy Posting: Quickly post details about lost or found items, including descriptions and images.
-Browse Listings: Easily view all public listings to help find what you're looking for.
-Manage Your Items: Keep track of your posts through a personal dashboard.
-API Integration: Developers can interact with FindNaija programmatically using the API for adding, modifying, or retrieving data.
-Secure Authentication: Utilizes tokens for secure API access, ensuring only authorized users can make changes.

---

## 🛠️ Technologies Used

-Python: The core programming language.
-Flask: A web framework for building the application.
-SQLite: A lightweight database for storing data.
-Various Libraries: Additional tools for enhanced security, testing, and functionality.

---

## 🚀 Setup Instructions

Follow these steps to get FindNaija up and running on your local machine:

1.  **Clone the Repository**

    Open your terminal and run:

    git clone https://github.com/aeprnts/findnaija.git
    cd findnaija
    git checkout enhancement-api

Create a Virtual Environment
Isolate project dependencies:
use this command:
python -m venv venv

Activate the Virtual Environment
Windows:

venv\Scripts\activate

macOS/Linux:

source venv/bin/activate

Install Dependencies
Install required packages:

pip install -r requirements.txt

Configure Environment Variables (Recommended)
Create a .env file in the project directory:

SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:///findnaija.db

Note: Replace your_secret_key and your_jwt_secret_key with random, secure strings.
Initialize the Database
Set up the database tables:
flask db upgrade

Run the Application
Start the FindNaija application:

python run.py

Access the Application
Open your web browser and navigate to http://127.0.0.1:5000/.
💻 API Usage (For Developers)
The FindNaija API allows programmatic interaction with the application.

📍 API Endpoints
Action	Method	Endpoint
Authenticate and get token	POST	/api/auth/login
Get all items	GET	/api/items
Add a new item	POST	/api/items
Update an item	PUT	/api/items/{id}
Delete an item	DELETE	/api/items/{id}

🔑 Authentication
After logging in, you will receive a unique token.
Include this token in the Authorization header for secure API requests that modify data.
Example: Authorization: Bearer your_token
📝 Example: Adding a Lost Wallet
Send a POST request to /api/items with the following JSON payload:

json
{
  "title": "Lost Wallet",
  "description": "Black leather wallet lost near Central Park.",
  "image_file": "http://example.com/images/wallet.jpg" or your file
}

Remember to include your authentication token in the Authorization header.

RUNNING TEST
To ensure the application and API are functioning correctly, run the following test command:

python -m pytest --maxfail=1 --disable-warnings -q --cov=app --cov-report=term-missing tests/test_claims.py

*Make sure your virtual environment is activated before running the tests.

MANUAL API TESTING/RUNNING IN POSTMAN
Start the application: python run.py
Open Postman.
Send a POST request to /api/auth/login with your credentials to obtain a token.
Copy the received token.
For subsequent API requests, go to the Authorization tab, select Bearer Token, and paste your token.
You can now send requests to create, read, update, or delete items.

PROJECT STRUCTURE
app/: Contains the main application code.
app/extensions.py: Initializes extensions like the database and login manager.
app/models.py: Defines the structure of database tables.
app/routes/api.py: Handles API endpoints and logic.
tests/test_api.py: Includes tests for the API.
run.py: Starts the Flask development server.

Thank you for using FindNaija!
