# Import necessary libraries
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# Define a function to generate a random AES key
def generate_aes_key(key_size=256):
    
    aes_key = get_random_bytes(key_size // 8)  # key_size is in bits, so divide by 8 to get bytes
    return aes_key

# Define a function for AES encryption
def aes_encrypt(plaintext, aes_key):
    
    # Pad the plaintext to make its length a multiple of 16 (AES block size)
    padded_plaintext = plaintext + b'\0' * (AES.block_size - len(plaintext) % AES.block_size)
    
    # Create AES cipher object
    cipher = AES.new(aes_key, AES.MODE_ECB)
    
    # Encrypt the padded plaintext
    ciphertext = cipher.encrypt(padded_plaintext)
    
    # Return the base64 encoded ciphertext for easier handling
    return base64.b64encode(ciphertext)

# Define a function for AES decryption
def aes_decrypt(ciphertext, aes_key):
    
    # Decode the base64 encoded ciphertext
    ciphertext = base64.b64decode(ciphertext)
    
    # Create AES cipher object
    cipher = AES.new(aes_key, AES.MODE_ECB)
    
    # Decrypt the ciphertext
    plaintext = cipher.decrypt(ciphertext)
    
    # Remove padding from the plaintext
    plaintext = plaintext.rstrip(b'\0')
    
    return plaintext

if __name__ == "__main__":
    # Generate a random AES key
    aes_key = generate_aes_key()
    
    # Prompt the user to enter a message
    plaintext = input("Enter a message to encrypt: ").encode()
    
    # Encrypt the plaintext message
    ciphertext = aes_encrypt(plaintext, aes_key)
    print("Encrypted message:", ciphertext.decode())
    
    # Decrypt the ciphertext message
    decrypted_plaintext = aes_decrypt(ciphertext, aes_key)
    print("Decrypted message:", decrypted_plaintext.decode())
