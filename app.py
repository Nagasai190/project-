from flask import Flask, render_template, request
from aes_cryptography import aes_encrypt, aes_decrypt, generate_aes_key

app = Flask(__name__)

# Generate a random AES key (you could also allow users to input their own key securely)
aes_key = generate_aes_key()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    encrypted_message = ''
    decrypted_message = ''

    if request.method == 'POST':
        message = request.form['message']
        if message:
            encrypted_message = aes_encrypt(message.encode(), aes_key).decode()
            decrypted_message = aes_decrypt(encrypted_message.encode(), aes_key).decode()

    return render_template('index.html', message=message, encrypted_message=encrypted_message, decrypted_message=decrypted_message)

if __name__ == '__main__':
    app.run(debug=True)
