import os 

def validate_secret(payload):
    secret = os.getenv("SECRET_KEY")
    return secret == "my_secret_code"

