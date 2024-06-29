These are the dependencies for the QuizMe app, and what they are needed for.

# Dependencies
- Django -- the Django framework
- django-markdown-deux -- for "markdown" template tag to convert markdown to html
- django-pagedown -- markdown wysiwyg editor
- humanize -- converts time durations to human-readable times (e.g., "11 days")
- psycopg2 -- Postgresql API
- py2-py3-django-email-as-username -- used to allow an email address as a username; this was needed when the project was started with Django 1.4, but could now be removed, as Django now natively supports this functionality.
- python-dateutil --
- pytz -- timezones

# Development Dependencies (not used in production)

- django-debug-toolbar -- useful for viewing queries, and profiling performance
- django-extensions -- many useful development extensions, e.g., 
    - manage.py commands:  
        - manage.py shell_plus --notebook  => use iPython Jupyter Notebook  
        - manage.py shell_plus --print-sql  ==> print SQL queries as they're executed; NOTE: need Debug=True  
        - manage.py shell_plus --ipython  
    - and other manage.py commands:  
        - clean_pyc  
        - clear_cache  
        - compile_pyc  
        - create_command  
        - delete_squashed_migrations  
        - runserver_plus  
        - shell_plus  
        - validate_templates  