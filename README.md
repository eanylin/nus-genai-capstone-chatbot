## Multi-Tool AI Agent Chatbot

- **NOTE**: The application was tested on RHEL 9, running Python 3.9.21

### Steps:

- Create virtual environment with Python 3.9.21
- Install all the required packages
```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ pip install --upgrade pip
```

- Setup the events database as well as company's database
```
$ python setup_db.py
$ python setup_events_db.py
```

- Ensure that `company.db` and `events.db` are present in the directory
- Run the application
```
$ streamlit run app.py
```

- Open the web browser, e.g. Google Chrome or Firefox and the streamlit application will be accessible at http://127.0.0.1:8501
