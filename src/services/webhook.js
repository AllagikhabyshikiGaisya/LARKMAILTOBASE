const crypto = require('crypto');

class WebhookService {
    verifySignature(req) {
        // Skip signature verification in development mode
        if (process.env.NODE_ENV === 'development') {
            console.log('⚠️ Skipping webhook signature verification (development mode)');
            return true;
        }

        const signature = req.headers['x-lark-signature'];
        const timestamp = req.headers['x-lark-request-timestamp'];
        const nonce = req.headers['x-lark-request-nonce'];
        
        if (!signature || !timestamp || !nonce) {
            console.log('❌ Missing webhook headers');
            return false;
        }

        const body = JSON.stringify(req.body);
        const secret = process.env.LARK_WEBHOOK_SECRET;
        
        // Create signature string
        const signatureString = timestamp + nonce + secret + body;
        
        // Generate expected signature
        const expectedSignature = crypto
            .createHash('sha256')
            .update(signatureString, 'utf8')
            .digest('hex');

        const isValid = signature === expectedSignature;
        console.log(isValid ? '✅ Webhook signature verified' : '❌ Invalid webhook signature');
        
        return isValid;
    }
}

module.exports = new WebhookService();