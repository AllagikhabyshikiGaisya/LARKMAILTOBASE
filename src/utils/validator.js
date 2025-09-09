class Validator {
    static validateEmailFormat(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static validatePhoneNumber(phone) {
        // Japanese phone number validation
        const phoneRegex = /^0[0-9]{1,4}-?[0-9]{1,4}-?[0-9]{3,4}$|^0[0-9]{9,11}$/;
        return phoneRegex.test(phone.replace(/[-\s]/g, ''));
    }

    static validatePostalCode(postalCode) {
        // Japanese postal code validation (〒XXX-XXXX)
        const postalRegex = /^〒?\d{3}-?\d{4}$/;
        return postalRegex.test(postalCode);
    }

    static validateDate(dateString) {
        if (!dateString) return false;
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }

    static validateAge(age) {
        return Number.isInteger(age) && age > 0 && age < 120;
    }

    static validateAmount(amount) {
        return Number.isInteger(amount) && amount >= 0;
    }

    static sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        return input.trim().replace(/[\r\n\t]/g, ' ').replace(/\s+/g, ' ');
    }

    static formatPhoneNumber(phone) {
        if (!phone) return phone;
        // Remove all non-digits
        const digits = phone.replace(/\D/g, '');
        // Format as Japanese phone number
        if (digits.length === 11 && digits.startsWith('0')) {
            return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`;
        }
        return phone;
    }

    static formatPostalCode(postalCode) {
        if (!postalCode) return postalCode;
        const digits = postalCode.replace(/\D/g, '');
        if (digits.length === 7) {
            return `〒${digits.slice(0, 3)}-${digits.slice(3)}`;
        }
        return postalCode;
    }
}

module.exports = Validator;
