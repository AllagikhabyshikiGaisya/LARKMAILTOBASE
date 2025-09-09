const express = require('express');
const crypto = require('crypto');
require('dotenv').config();

const emailParser = require('./services/emailParser');
const larkBase = require('./services/larkBase');
const webhook = require('./services/webhook');
const logger = require('./utils/logger');

const app = express();
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ 
        status: 'OK', 
        timestamp: new Date().toISOString(),
        message: 'Lark Mail Automation is running!'
    });
});

// Test endpoint for development
app.get('/', (req, res) => {
    res.json({
        message: 'Lark Mail to Base Automation System',
        status: 'Running',
        endpoints: {
            health: '/health',
            webhook: '/webhook/lark-mail',
            test: '/test/parse-email'
        }
    });
});

// Webhook endpoint for Lark Mail
app.post('/webhook/lark-mail', async (req, res) => {
    try {
        // Verify webhook signature
        const isValid = webhook.verifySignature(req);
        if (!isValid) {
            logger.error('Invalid webhook signature');
            return res.status(401).json({ error: 'Invalid signature' });
        }

        // Process the email
        const emailData = req.body;
        logger.info('Received email webhook', { 
            messageId: emailData.message_id,
            subject: emailData.subject 
        });

        // Check if it's our target email format
        if (!emailParser.isEventRegistrationEmail(emailData)) {
            logger.info('Email is not an event registration, skipping');
            return res.status(200).json({ status: 'skipped' });
        }

        // Parse email content
        const parsedData = emailParser.parseEventRegistration(emailData);
        
        // Validate parsed data
        if (!parsedData.isValid) {
            logger.error('Failed to parse email data', { errors: parsedData.errors });
            return res.status(400).json({ error: 'Invalid email format' });
        }

        // Save to Lark Base
        const result = await larkBase.createRecord(parsedData.data);
        
        logger.info('Successfully processed email', { 
            recordId: result.record_id,
            customerEmail: parsedData.data.customerEmail 
        });

        res.status(200).json({ 
            status: 'success', 
            recordId: result.record_id 
        });

    } catch (error) {
        logger.error('Error processing webhook', { error: error.message });
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Test endpoint for development
app.post('/test/parse-email', async (req, res) => {
    try {
        const emailContent = req.body.content;
        const mockEmailData = {
            subject: '[STYLE HOUSE] イベントの参加お申し込みがありました。',
            body: emailContent,
            received_time: new Date().toISOString()
        };

        const parsedData = emailParser.parseEventRegistration(mockEmailData);
        
        if (parsedData.isValid) {
            console.log('✅ Email parsed successfully!');
            console.log('📊 Parsed data:', JSON.stringify(parsedData.data, null, 2));
            
            // Try to save to Lark Base
            try {
                const result = await larkBase.createRecord(parsedData.data);
                res.json({ 
                    success: true, 
                    recordId: result.record_id, 
                    data: parsedData.data,
                    message: '✅ Data saved to Lark Base successfully!'
                });
            } catch (larkError) {
                console.log('⚠️ Lark Base save failed, but parsing worked:', larkError.message);
                res.json({ 
                    success: true, 
                    recordId: null, 
                    data: parsedData.data,
                    message: '✅ Email parsing successful! ⚠️ Lark Base connection needed.'
                });
            }
        } else {
            res.status(400).json({ success: false, errors: parsedData.errors });
        }
    } catch (error) {
        logger.error('Test endpoint error', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
    console.log(`🏥 Health check: http://localhost:${PORT}/health`);
    console.log(`🧪 Test endpoint: http://localhost:${PORT}/test/parse-email`);
    logger.info(`Server started on port ${PORT}`);
});

module.exports = app;