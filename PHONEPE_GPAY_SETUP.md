# PhonePe & Google Pay Payment Setup Guide

## Quick Setup Instructions

### Step 1: Get Your Payment Links

You have **3 options** to set up payments:

---

## Option 1: Use Universal UPI Link (Recommended - Works with ALL UPI apps)

This is the **easiest** option - one link works with PhonePe, Google Pay, Paytm, and all other UPI apps.

### Format:
```
upi://pay?pa=YOUR_UPI_ID@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription
```

### How to Create:

1. **Get your UPI ID** (e.g., `yourname@paytm`, `yourname@ybl`, `yourname@okaxis`)

2. **Replace in the format:**
   - `YOUR_UPI_ID@paytm` → Your actual UPI ID
   - `599` → Your price (change if different)
   - `StudyQnA` → Your business name
   - `Premium%20Subscription` → Payment description

3. **Example:**
```
upi://pay?pa=gugan@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription
```

4. **Update in PremiumBanner.jsx:**
   - Find line: `const UPI_PAYMENT_LINK = "YOUR_UPI_PAYMENT_LINK_HERE"`
   - Replace with your UPI link

---

## Option 2: PhonePe Payment Link

### Method A: Using PhonePe Business App

1. **Download PhonePe Business App** (if you don't have it)
2. **Create a Payment Link:**
   - Open PhonePe Business app
   - Go to "Payment Links" or "Collect Payments"
   - Create new link for ₹599
   - Set description: "Premium Subscription"
   - Copy the link (format: `https://phon.pe/xxxxx` or `https://pay.phonepe.com/xxxxx`)

3. **Update in PremiumBanner.jsx:**
   - Find line: `const PHONEPE_LINK = "YOUR_PHONEPE_PAYMENT_LINK_HERE"`
   - Replace with your PhonePe link

### Method B: Using PhonePe Merchant Dashboard

1. **Login to PhonePe Merchant Dashboard** (https://merchant.phonepe.com)
2. **Navigate to Payment Links**
3. **Create a new payment link** for ₹599
4. **Copy the link**

---

## Option 3: Google Pay Payment Link

### Method A: Using Google Pay Business

1. **Set up Google Pay Business** (if not done)
2. **Create Payment Request:**
   - Open Google Pay Business app
   - Create payment request for ₹599
   - Copy the payment link (format: `https://gpay.app.goo.gl/xxxxx`)

3. **Update in PremiumBanner.jsx:**
   - Find line: `const GPAY_LINK = "YOUR_GPAY_PAYMENT_LINK_HERE"`
   - Replace with your Google Pay link

### Method B: Using Google Pay for Business API

1. **Register for Google Pay for Business**
2. **Get your payment link** from the dashboard
3. **Update in PremiumBanner.jsx**

---

## Recommended Setup (Easiest)

**Use Option 1 (Universal UPI Link)** - It's the simplest and works with all UPI apps:

### Steps:

1. **Open:** `frontend/src/components/PremiumBanner.jsx`

2. **Find line 12:**
```javascript
const UPI_PAYMENT_LINK = "YOUR_UPI_PAYMENT_LINK_HERE"
```

3. **Replace with your UPI link:**
```javascript
const UPI_PAYMENT_LINK = "upi://pay?pa=your-upi-id@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription"
```

4. **Replace `your-upi-id@paytm`** with your actual UPI ID

5. **Save the file**

**That's it!** Both QR codes will use the same UPI link and work with PhonePe, Google Pay, and all other UPI apps.

---

## Advanced Setup (Separate Links for Each)

If you want **different links** for PhonePe and Google Pay:

1. **Get PhonePe link** (from PhonePe Business app)
2. **Get Google Pay link** (from Google Pay Business)
3. **Update both in PremiumBanner.jsx:**

```javascript
const PHONEPE_LINK = "https://phon.pe/your-phonepe-link-id"
const GPAY_LINK = "https://gpay.app.goo.gl/your-gpay-link-id"
```

---

## Testing Your Payment Links

### Test UPI Link:
1. Copy your UPI link
2. Open any UPI app (PhonePe, Google Pay, Paytm)
3. The app should automatically open with payment details
4. Verify amount (₹599) and merchant name

### Test PhonePe Link:
1. Copy your PhonePe link
2. Open PhonePe app
3. Payment should be pre-filled

### Test Google Pay Link:
1. Copy your Google Pay link
2. Open Google Pay app
3. Payment should be pre-filled

---

## Current File Status

**File:** `frontend/src/components/PremiumBanner.jsx`

**Lines to Update:**
- **Line 12:** `UPI_PAYMENT_LINK` (Recommended - works with all apps)
- **Line 10:** `PHONEPE_LINK` (Optional - if you want separate PhonePe link)
- **Line 11:** `GPAY_LINK` (Optional - if you want separate Google Pay link)

---

## Example UPI IDs

Common UPI ID formats:
- `yourname@paytm` (Paytm)
- `yourname@ybl` (PhonePe)
- `yourname@okaxis` (Axis Bank)
- `yourname@okhdfcbank` (HDFC Bank)
- `yourname@okicici` (ICICI Bank)
- `yourname@oksbi` (SBI)

---

## Troubleshooting

### QR Code not scanning?
- Ensure the link is valid and starts with `upi://` or `https://`
- Test the link in a UPI app first
- Check if the link is too long (some QR scanners have limits)

### Payment not working?
- Verify your UPI ID is correct
- Check if amount is correct (₹599)
- Ensure your UPI is activated and linked to a bank account

### Need help?
- Contact your bank for UPI activation
- Check PhonePe/Google Pay support for payment link creation
- Verify merchant account setup if using business apps

---

## Quick Reference

**Minimum Setup (Recommended):**
```javascript
const UPI_PAYMENT_LINK = "upi://pay?pa=YOUR_UPI_ID@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription"
```

**Full Setup (Separate Links):**
```javascript
const PHONEPE_LINK = "https://phon.pe/your-link-id"
const GPAY_LINK = "https://gpay.app.goo.gl/your-link-id"
const UPI_PAYMENT_LINK = "upi://pay?pa=YOUR_UPI_ID@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription"
```


