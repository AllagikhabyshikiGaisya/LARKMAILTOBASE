const LARK_CONFIG = {
    APP_ID: process.env.LARK_APP_ID,
    APP_SECRET: process.env.LARK_APP_SECRET,
    WEBHOOK_SECRET: process.env.LARK_WEBHOOK_SECRET,
    BASE_ID: process.env.LARK_BASE_ID,
    TABLE_ID: process.env.LARK_TABLE_ID,
    
    // API endpoints
    BASE_URL: 'https://open.larksuite.com/open-apis',
    
    // Allowed email addresses for processing
    ALLOWED_EMAILS: [
        'utosabu.adhikari@allagi.jp',
        // Add more emails after testing
    ],
    
    // Field mappings for Lark Base
    FIELD_MAPPINGS: {
        'Email Received Date': 'emailReceivedDate',
        'Event Name': 'eventName',
        'Event Date Start': 'eventDateStart',
        'Event Date End': 'eventDateEnd',
        'Event Time': 'eventTime',
        'Event Venue': 'eventVenue',
        'Event URL': 'eventUrl',
        'Customer Name': 'customerName',
        'Customer Furigana': 'customerFurigana',
        'Customer Email': 'customerEmail',
        'Customer Phone': 'customerPhone',
        'Customer Age': 'customerAge',
        'Monthly Rent': 'monthlyRent',
        'Monthly Payment': 'monthlyPayment',
        'Postal Code': 'postalCode',
        'Address': 'address',
        'Desired Date': 'desiredDate',
        'Desired Time': 'desiredTime',
        'Comments': 'comments',
        'Lead Source': 'leadSource',
        'Housing Type': 'housingType',
        'Consideration Period': 'considerationPeriod',
        'Status': 'status',
        'Created At': 'createdAt'
    }
};

module.exports = LARK_CONFIG;
