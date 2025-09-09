class EventRegistration {
    constructor(data) {
        // System fields
        this.id = data.id || null;
        this.emailReceivedDate = data.emailReceivedDate;
        this.createdAt = data.createdAt || new Date().toISOString();
        this.status = data.status || '新規';
        
        // Event information
        this.eventName = data.eventName;
        this.eventDateStart = data.eventDateStart;
        this.eventDateEnd = data.eventDateEnd;
        this.eventTime = data.eventTime;
        this.eventVenue = data.eventVenue;
        this.eventUrl = data.eventUrl;
        
        // Reservation details
        this.desiredDate = data.desiredDate;
        this.desiredTime = data.desiredTime;
        
        // Customer information
        this.customerName = data.customerName;
        this.customerFurigana = data.customerFurigana;
        this.customerEmail = data.customerEmail;
        this.customerPhone = data.customerPhone;
        this.customerAge = data.customerAge;
        this.monthlyRent = data.monthlyRent;
        this.monthlyPayment = data.monthlyPayment;
        this.postalCode = data.postalCode;
        this.address = data.address;
        this.comments = data.comments;
        this.leadSource = data.leadSource;
        
        // Survey information
        this.housingType = data.housingType;
        this.considerationPeriod = data.considerationPeriod;
    }

    validate() {
        const errors = [];
        
        // Required fields validation
        if (!this.customerName) errors.push('Customer name is required');
        if (!this.customerEmail) errors.push('Customer email is required');
        if (!this.eventName) errors.push('Event name is required');
        
        // Email format validation
        if (this.customerEmail && !this.isValidEmail(this.customerEmail)) {
            errors.push('Invalid email format');
        }
        
        // Phone number validation
        if (this.customerPhone && !this.isValidPhone(this.customerPhone)) {
            errors.push('Invalid phone number format');
        }
        
        // Age validation
        if (this.customerAge && !this.isValidAge(this.customerAge)) {
            errors.push('Invalid age value');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }

    isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    isValidPhone(phone) {
        const regex = /^0[0-9]{1,4}-?[0-9]{1,4}-?[0-9]{3,4}$|^0[0-9]{9,11}$/;
        return regex.test(phone.replace(/[-\s]/g, ''));
    }

    isValidAge(age) {
        return Number.isInteger(age) && age > 0 && age < 120;
    }

    toJSON() {
        return {
            id: this.id,
            emailReceivedDate: this.emailReceivedDate,
            createdAt: this.createdAt,
            status: this.status,
            eventName: this.eventName,
            eventDateStart: this.eventDateStart,
            eventDateEnd: this.eventDateEnd,
            eventTime: this.eventTime,
            eventVenue: this.eventVenue,
            eventUrl: this.eventUrl,
            desiredDate: this.desiredDate,
            desiredTime: this.desiredTime,
            customerName: this.customerName,
            customerFurigana: this.customerFurigana,
            customerEmail: this.customerEmail,
            customerPhone: this.customerPhone,
            customerAge: this.customerAge,
            monthlyRent: this.monthlyRent,
            monthlyPayment: this.monthlyPayment,
            postalCode: this.postalCode,
            address: this.address,
            comments: this.comments,
            leadSource: this.leadSource,
            housingType: this.housingType,
            considerationPeriod: this.considerationPeriod
        };
    }
}

module.exports = EventRegistration;
