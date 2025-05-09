"""Helper module to request secrets from the user"""

def ask_secrets(secret_keys, user_message):
    """
    Request sensitive environment variables from the user
    
    Parameters:
    -----------
    secret_keys : list
        A list of environment variable names to request
    user_message : str
        A message explaining why these secrets are needed
    """
    # This function will be replaced by the actual implementation
    # in the Replit environment, which will securely prompt the user
    # to provide these secret values
    print(f"Requesting secrets: {secret_keys}")
    print(f"Message: {user_message}")
    
    # Return True to indicate success
    return True