
# Software Engineering Project

## Overview

This project is designed to demonstrate a comprehensive application utilizing Flask, Celery, and SQLAlchemy, among other technologies. It requires a MySQL database and is intended for educational and demonstration purposes.

## Prerequisites

- Python 3.8 or later
- MySQL Database
- MySQL Workbench (Recommended for database manipulation)

## Setup

### Clone the Repository

First, clone this repository to your local machine using Git:

```bash
git clone <repository-url>
cd Software-Engineering-Project
```

### Environment Setup

#### For Mac Users:

Run the provided `setup_env.sh` script to create a virtual environment, activate it, and install the required Python packages:

```bash
./setup_env.sh
```

#### For Windows and Linux Users:

Ensure you have Python and pip installed on your system. Then, create a virtual environment and activate it:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### Database Setup

1. Ensure MySQL is installed and running on your system.
2. Open MySQL Workbench and connect to your MySQL server.
3. Create a new database named `sustainability_app_data`:
   
   ```sql
   CREATE DATABASE sustainability_app_data;
   ```
   
4. Ensure the `admin` user exists and set the password to `Hanad2020@`. If not, create the user and grant it permissions:

   ```sql
   CREATE USER 'admin'@'localhost' IDENTIFIED BY 'Hanad2020@';
   GRANT ALL PRIVILEGES ON sustainability_app_data.* TO 'admin'@'localhost';
   FLUSH PRIVILEGES;
   ```

   Make sure the `admin` user has full read and write access to the `sustainability_app_data` database.

## Running the Application

To run the application, use the following command:

```bash
python3 app.py
```

The application will start, and you can access it through your web browser.

## Contributing

Contributions to this project are welcome. Please ensure you follow the existing code style and submit your pull requests for review.

Thank you for participating in our project and stay tuned! more is coming!

::::::::
