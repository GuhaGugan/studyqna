# QR Code Setup Guide for Premium Payment

## Location
The QR code is displayed in `frontend/src/components/PremiumBanner.jsx`

## Option 1: Use Payment Link (Recommended)

If you have a payment link (UPI, Payment Gateway, etc.), replace the URL in the QRCode component.

### Steps:

1. **Open the file**: `frontend/src/components/PremiumBanner.jsx`

2. **Find line 36** and replace `YOUR_PAYMENT_LINK_HERE` with your actual payment link:

```javascript
// Example for UPI payment link:
<QRCode value="upi://pay?pa=your-upi-id@paytm&pn=StudyQnA&am=599&cu=INR" size={120} />

// Example for Payment Gateway:
<QRCode value="https://your-payment-gateway.com/pay/599" size={120} />

// Example for Razorpay/PayU:
<QRCode value="https://razorpay.com/payment-button/your-button-id" size={120} />
```

3. **Update the price text** on line 37 if needed (currently shows ₹599)

### Common Payment Link Formats:

**UPI Payment Link:**
```
upi://pay?pa=your-upi-id@paytm&pn=StudyQnA&am=599&cu=INR
```

**Google Pay:**
```
https://gpay.app.goo.gl/your-link-id
```

**PhonePe:**
```
https://phon.pe/your-link-id
```

**Paytm:**
```
https://paytm.me/your-link-id
```

**Razorpay Payment Link:**
```
https://rzp.io/i/your-link-id
```

---

## Option 2: Use QR Code Image File

If you have a QR code image file, you can replace the QRCode component with an `<img>` tag.

### Steps:

1. **Place your QR code image** in `frontend/public/` folder
   - Example: `frontend/public/qr-code.png`

2. **Update PremiumBanner.jsx**:

```javascript
// Remove the QRCode import (line 5)
// import QRCode from 'qrcode.react'  // Remove this line

// Replace the QRCode component (line 36) with:
<img 
  src="/qr-code.png" 
  alt="Payment QR Code" 
  className="w-[120px] h-[120px]"
/>
```

### Complete Updated Code:

```javascript
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
// Remove: import QRCode from 'qrcode.react'

const PremiumBanner = () => {
  // ... existing code ...

  return (
    <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white py-4">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex-1 text-center sm:text-left">
            <h3 className="font-bold text-lg mb-1">Upgrade to Full Access</h3>
            <p className="text-sm">
              Get unlimited Q/A generation, downloads, and premium features
            </p>
          </div>
          <div className="flex items-center gap-4">
            {showQR && (
              <div className="bg-white p-4 rounded-lg">
                <img 
                  src="/qr-code.png" 
                  alt="Payment QR Code" 
                  className="w-[120px] h-[120px]"
                />
                <p className="text-xs text-gray-600 mt-2 text-center">Scan & Pay ₹599</p>
              </div>
            )}
            {/* ... rest of the code ... */}
          </div>
        </div>
      </div>
    </div>
  )
}
```

---

## Option 3: Generate QR Code from Payment Link

If you want to generate a QR code image from your payment link:

1. **Use an online QR code generator:**
   - https://www.qr-code-generator.com/
   - https://qr-code-generator.com/
   - https://www.the-qrcode-generator.com/

2. **Enter your payment link** and generate the QR code

3. **Download the QR code image** (PNG format, 200x200px or larger)

4. **Follow Option 2** to use the image file

---

## Recommended: UPI Payment Link

For Indian users, UPI payment links are most convenient:

### Create UPI Payment Link:

1. **Using PhonePe:**
   - Open PhonePe Business app
   - Create payment link for ₹599
   - Copy the link

2. **Using Google Pay:**
   - Open Google Pay Business
   - Create payment request
   - Copy the link

3. **Using Paytm:**
   - Open Paytm Business
   - Create payment link
   - Copy the link

4. **Manual UPI Link Format:**
```
upi://pay?pa=YOUR_UPI_ID@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription
```

Replace:
- `YOUR_UPI_ID@paytm` with your actual UPI ID
- `599` with your price (if different)
- `StudyQnA` with your business name

---

## Testing

After updating:

1. **Save the file**
2. **Restart the frontend** (if running)
3. **Click "Show QR Code"** button in the premium banner
4. **Verify** the QR code displays correctly
5. **Test scan** with a QR code scanner app

---

## Current Status

The QR code is currently set to: `YOUR_PAYMENT_LINK_HERE`

**Action Required:** Replace this with your actual payment link or QR code image.


