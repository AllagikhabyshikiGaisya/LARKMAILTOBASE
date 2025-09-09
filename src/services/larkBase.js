const axios = require('axios');
const logger = require('../utils/logger');

class LarkBaseService {
    constructor() {
        this.baseUrl = 'https://open.larksuite.com/open-apis';
        this.accessToken = null;
        this.tokenExpiry = null;
    }

    async getAccessToken() {
        if (this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry) {
            return this.accessToken;
        }

        try {
            console.log('🔑 Getting Lark access token...');
            const response = await axios.post(`${this.baseUrl}/auth/v3/tenant_access_token/internal`, {
                app_id: process.env.LARK_APP_ID,
                app_secret: process.env.LARK_APP_SECRET
            });

            this.accessToken = response.data.tenant_access_token;
            this.tokenExpiry = Date.now() + (response.data.expire - 60) * 1000; // 1 minute buffer
            
            console.log('✅ Access token obtained successfully');
            return this.accessToken;
        } catch (error) {
            console.error('❌ Failed to get access token:', error.message);
            logger.error('Failed to get access token', { error: error.message });
            throw new Error('Authentication failed');
        }
    }

    async createRecord(data) {
        try {
            const token = await this.getAccessToken();
            
            const recordData = {
                fields: this.formatRecordFields(data)
            };

            console.log('💾 Saving to Lark Base...');
            const response = await axios.post(
                `${this.baseUrl}/bitable/v1/apps/${process.env.LARK_BASE_ID}/tables/${process.env.LARK_TABLE_ID}/records`,
                recordData,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            console.log('✅ Record saved successfully!');
            logger.info('Record created successfully', { 
                recordId: response.data.data.record.record_id 
            });

            return response.data.data.record;

        } catch (error) {
            console.error('❌ Failed to save to Lark Base:', error.message);
            logger.error('Failed to create record', { 
                error: error.message,
                response: error.response?.data 
            });
            throw error;
        }
    }

    formatRecordFields(data) {
        const fields = {};

        // Map data to Lark Base field names
        const fieldMapping = {
            'Email Received Date': this.formatDateTime(data.emailReceivedDate),
            'Event Name': data.eventName,
            'Event Date Start': this.formatDate(data.eventDateStart),
            'Event Date End': this.formatDate(data.eventDateEnd),
            'Event Time': data.eventTime,
            'Event Venue': data.eventVenue,
            'Event URL': data.eventUrl,
            'Customer Name': data.customerName,
            'Customer Furigana': data.customerFurigana,
            'Customer Email': data.customerEmail,
            'Customer Phone': data.customerPhone,
            'Customer Age': data.customerAge,
            'Monthly Rent': data.monthlyRent,
            'Monthly Payment': data.monthlyPayment,
            'Postal Code': data.postalCode,
            'Address': data.address,
            'Desired Date': this.formatDate(data.desiredDate),
            'Desired Time': data.desiredTime,
            'Comments': data.comments,
            'Lead Source': data.leadSource,
            'Housing Type': data.housingType,
            'Consideration Period': data.considerationPeriod,
            'Status': data.status,
            'Created At': this.formatDateTime(data.createdAt)
        };

        // Only include fields with values
        Object.keys(fieldMapping).forEach(key => {
            if (fieldMapping[key] !== null && fieldMapping[key] !== undefined && fieldMapping[key] !== '') {
                fields[key] = fieldMapping[key];
            }
        });

        return fields;
    }

    formatDateTime(dateString) {
        if (!dateString) return null;
        return Math.floor(new Date(dateString).getTime() / 1000);
    }

    formatDate(dateString) {
        if (!dateString) return null;
        return Math.floor(new Date(dateString + 'T00:00:00Z').getTime() / 1000);
    }

    async testConnection() {
        try {
            console.log('🧪 Testing Lark Base connection...');
            const token = await this.getAccessToken();
            
            const response = await axios.get(
                `${this.baseUrl}/bitable/v1/apps/${process.env.LARK_BASE_ID}/tables/${process.env.LARK_TABLE_ID}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            console.log('✅ Lark Base connection successful!');
            logger.info('Connection test successful', { tableId: response.data.data.table.table_id });
            return true;
        } catch (error) {
            console.error('❌ Lark Base connection failed:', error.message);
            logger.error('Connection test failed', { error: error.message });
            return false;
        }
    }
}

module.exports = new LarkBaseService();