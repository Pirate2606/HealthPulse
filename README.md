# **HealthPulse**

The transition from paper records to digital solutions in healthcare is imperative for accessibility and efficiency. Traditional paper documents lack digital optimization, making them difficult to scan, index, and analyze. This inaccessibility poses challenges, especially with lengthy intake forms that require printing, leading to errors and disengagement. To address these issues, a user-friendly digital platform is needed for patients to complete intake forms electronically. This platform, utilizing OpenText APIs, can parse and convert various forms into a digital format. Moreover, a secure portal for health report intake enables users to upload documents for safe storage in the cloud, leveraging OpenText APIs for data extraction. Subsequently, health report analysis becomes more effective, as pertinent information is presented in an easily comprehensible format, supporting informed decisions for patient care and healthcare management.


# Instructions:

## Prerequisites:
    1. Python3 should be installed on the system.
    2. Need an active internet connection.

## To run the project locally, follow the following steps:
    1. Setup a virtual environment:
        For ubuntu:
            1. sudo apt install virtualenv
            2. virtualenv -p python3 name_of_environment
            3. To activate: source name_of_environment/bin/activate
        For windows:
            1.	pip install virtualenv
            2.	python -m venv <path for creating virtualenv>
            3.	To activate: <virtualenv path>\Scripts\activate

    2. Clone the repository: git clone https://github.com/Pirate2606/HealthPulse
    3. Change the directory: cd HealthPulse
    4. Install the requirements: pip install -r requirements.txt
    5. Generate OAuth client ID and Secret for Google.
    6. Place the client ID and secret for Google in "config.py" file.
    7. Generate Client ID, Client Secret, Tenant ID, Account Username and Password for OpenText API and replace them in the config.py file.
    8. To access the mailing service, replace mail ID and mail password in the config.py file.
    9. Create a database in mongobd and replace the username, password and database name for that in the config.py file.
    10. Create database: flask createdb
    11. Run the server: python3 app.py
