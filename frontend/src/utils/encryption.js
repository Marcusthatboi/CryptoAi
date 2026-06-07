/**
 * Client-side encryption utility for sensitive payment data
 * Uses SubtleCrypto API (Web Crypto API) for AES-GCM encryption
 */

/**
 * Generate a random encryption key
 */
async function generateEncryptionKey() {
  return await window.crypto.subtle.generateKey(
    {
      name: 'AES-GCM',
      length: 256
    },
    true,
    ['encrypt', 'decrypt']
  )
}

/**
 * Export key for transmission to server
 */
async function exportKey(key) {
  const exported = await window.crypto.subtle.exportKey('raw', key)
  return btoa(String.fromCharCode(...new Uint8Array(exported)))
}

/**
 * Encrypt credit card data using AES-GCM
 * @param {Object} cardData - { cardNumber, expiryMonth, expiryYear, cvv, cardholderName }
 * @returns {Promise<Object>} Encrypted data with IV and key for transmission
 */
export async function encryptCardData(cardData) {
  try {
    // Generate encryption key
    const key = await generateEncryptionKey()
    
    // Generate random IV (Initialization Vector)
    const iv = window.crypto.getRandomValues(new Uint8Array(12))
    
    // Convert card data to JSON string
    const dataString = JSON.stringify({
      cardNumber: cardData.cardNumber.replace(/\s/g, ''),
      expiryMonth: String(cardData.expiryMonth).padStart(2, '0'),
      expiryYear: String(cardData.expiryYear),
      cvv: cardData.cvv,
      cardholderName: cardData.cardholderName
    })
    
    // Convert to Uint8Array
    const encoder = new TextEncoder()
    const data = encoder.encode(dataString)
    
    // Encrypt the data
    const encryptedData = await window.crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      data
    )
    
    // Export the key for server-side decryption
    const exportedKey = await exportKey(key)
    
    // Convert encrypted data to base64
    const encryptedBase64 = btoa(String.fromCharCode(...new Uint8Array(encryptedData)))
    const ivBase64 = btoa(String.fromCharCode(...iv))
    
    return {
      encryptedData: encryptedBase64,
      iv: ivBase64,
      key: exportedKey,
      algorithm: 'AES-GCM-256'
    }
  } catch (error) {
    console.error('Encryption error:', error)
    throw new Error('Failed to encrypt payment data')
  }
}

/**
 * Validate credit card format (Luhn algorithm)
 */
export function validateCardNumber(cardNumber) {
  const sanitized = cardNumber.replace(/\s/g, '')
  if (!/^\d{13,19}$/.test(sanitized)) return false
  
  let sum = 0
  let isEven = false
  
  for (let i = sanitized.length - 1; i >= 0; i--) {
    let digit = parseInt(sanitized[i], 10)
    
    if (isEven) {
      digit *= 2
      if (digit > 9) digit -= 9
    }
    
    sum += digit
    isEven = !isEven
  }
  
  return sum % 10 === 0
}

/**
 * Detect card type from card number
 */
export function detectCardType(cardNumber) {
  const patterns = {
    visa: /^4[0-9]{12}(?:[0-9]{3})?$/,
    mastercard: /^5[1-5][0-9]{14}$/,
    amex: /^3[47][0-9]{13}$/,
    discover: /^6(?:011|5[0-9]{2})[0-9]{12}$/
  }
  
  const sanitized = cardNumber.replace(/\s/g, '')
  
  for (const [type, pattern] of Object.entries(patterns)) {
    if (pattern.test(sanitized)) return type
  }
  
  return 'unknown'
}

/**
 * Format credit card number with spaces
 */
export function formatCardNumber(value) {
  const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '')
  const matches = v.match(/\d{4,16}/g)
  const match = (matches && matches[0]) || ''
  const parts = []
  
  for (let i = 0, len = match.length; i < len; i += 4) {
    parts.push(match.substring(i, i + 4))
  }
  
  if (parts.length) {
    return parts.join(' ')
  } else {
    return value
  }
}

/**
 * Hash sensitive data for logging (returns only last 4 digits for cards)
 */
export function maskCardNumber(cardNumber) {
  const sanitized = cardNumber.replace(/\s/g, '')
  const lastFour = sanitized.slice(-4)
  return `****-****-****-${lastFour}`
}

/**
 * Encrypt generic data using AES-GCM-256
 * Used for account settings updates (email, password)
 * @param {Object} data - Data to encrypt (will be JSON stringified)
 * @returns {Promise<Object>} Encrypted payload with encryptedData, iv, key, algorithm
 */
export async function encryptAESGCM(data) {
  try {
    // Generate a random 256-bit key
    const key = await window.crypto.subtle.generateKey(
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );

    // Generate a random 96-bit (12-byte) IV for GCM
    const iv = window.crypto.getRandomValues(new Uint8Array(12));

    // Encode data to JSON and convert to bytes
    const encodedData = new TextEncoder().encode(JSON.stringify(data));

    // Encrypt the data
    const encryptedData = await window.crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      encodedData
    );

    // Export the key to raw format
    const exportedKey = await window.crypto.subtle.exportKey('raw', key);

    // Convert to base64 for transmission
    const encryptedDataB64 = btoa(String.fromCharCode(...new Uint8Array(encryptedData)));
    const ivB64 = btoa(String.fromCharCode(...iv));
    const keyB64 = btoa(String.fromCharCode(...new Uint8Array(exportedKey)));

    return {
      encryptedData: encryptedDataB64,
      iv: ivB64,
      key: keyB64,
      algorithm: 'AES-GCM-256'
    };
  } catch (error) {
    console.error('Encryption error:', error);
    throw new Error(`Failed to encrypt data: ${error.message}`);
  }
}

/**
 * Decrypt data using AES-GCM
 * @param {Object} encryptedPayload - Encrypted payload with encryptedData, iv, key
 * @returns {Promise<Object>} Decrypted data
 */
export async function decryptAESGCM(encryptedPayload) {
  try {
    // Decode from base64
    const encryptedData = Uint8Array.from(atob(encryptedPayload.encryptedData), c => c.charCodeAt(0));
    const iv = Uint8Array.from(atob(encryptedPayload.iv), c => c.charCodeAt(0));
    const keyData = Uint8Array.from(atob(encryptedPayload.key), c => c.charCodeAt(0));

    // Import the key
    const key = await window.crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM', length: 256 },
      true,
      ['decrypt']
    );

    // Decrypt the data
    const decryptedData = await window.crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      encryptedData
    );

    // Decode and parse JSON
    const decodedString = new TextDecoder().decode(decryptedData);
    return JSON.parse(decodedString);
  } catch (error) {
    console.error('Decryption error:', error);
    throw new Error(`Failed to decrypt data: ${error.message}`);
  }
}
