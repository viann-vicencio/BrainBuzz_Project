# BrainBuzz

BrainBuzz is a web application that uses the Gemini AI to generate quizzes from user-provided notes. It's a tool for students and learners who want to test their knowledge on a specific topic.

## Features

*   Create and manage notes.
*   Generate quizzes from your notes using the Gemini API.
*   Track your quiz history and progress.
*   Review your quiz results and see the correct answers.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/viann-vicencio/BrainBuzz.git
    cd BrainBuzz
    ```

2.  **Create and activate a virtual environment:**

    *   **Windows:**
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

    *   **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    Create a `.env` file in the root directory of the project and add your Gemini API key:

    ```
    GEMINI_API_KEY=your_api_key
    ```

    You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

## Running the application

1.  **Change into the `BrainBuzz` directory:**
    ```bash
    cd BrainBuzz
    ```
2.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000/`.

## Technologies Used
*   Python
*   Django
*   Google Gemini AI
*   HTML/CSS
*   JavaScript