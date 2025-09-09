const moment = require('moment');
const logger = require('../utils/logger');

class EmailParser {
    isEventRegistrationEmail(emailData) {
        const subject = emailData.subject || '';
        return subject.includes('[STYLE HOUSE]') && 
               subject.includes('イベントの参加お申し込みがありました');
    }

    parseEventRegistration(emailData) {
        try {
            const content = emailData.body || '';
            const receivedTime = emailData.received_time;

            console.log('📧 Parsing email content...');
            
            // Extract event information
            const eventInfo = this.extractEventInfo(content);
            console.log('🎪 Event info:', eventInfo);
            
            // Extract reservation information
            const reservationInfo = this.extractReservationInfo(content);
            console.log('📅 Reservation info:', reservationInfo);
            
            // Extract customer information
            const customerInfo = this.extractCustomerInfo(content);
            console.log('👤 Customer info:', customerInfo);
            
            // Extract survey responses
            const surveyInfo = this.extractSurveyInfo(content);
            console.log('📋 Survey info:', surveyInfo);

            const parsedData = {
                // System fields
                emailReceivedDate: receivedTime,
                createdAt: new Date().toISOString(),
                status: '新規',
                
                // Event information
                eventName: eventInfo.name,
                eventDateStart: eventInfo.dateStart,
                eventDateEnd: eventInfo.dateEnd,
                eventTime: eventInfo.time,
                eventVenue: eventInfo.venue,
                eventUrl: eventInfo.url,
                
                // Reservation details
                desiredDate: reservationInfo.date,
                desiredTime: reservationInfo.time,
                
                // Customer information
                customerName: customerInfo.name,
                customerFurigana: customerInfo.furigana,
                customerEmail: customerInfo.email,
                customerPhone: customerInfo.phone,
                customerAge: customerInfo.age,
                monthlyRent: customerInfo.rent,
                monthlyPayment: customerInfo.payment,
                postalCode: customerInfo.postalCode,
                address: customerInfo.address,
                comments: customerInfo.comments,
                leadSource: customerInfo.leadSource,
                
                // Survey information
                housingType: surveyInfo.housingType,
                considerationPeriod: surveyInfo.considerationPeriod
            };

            const validation = this.validateData(parsedData);
            
            return {
                isValid: validation.isValid,
                data: parsedData,
                errors: validation.errors
            };

        } catch (error) {
            logger.error('Error parsing email', { error: error.message });
            return {
                isValid: false,
                data: null,
                errors: [error.message]
            };
        }
    }

    extractEventInfo(content) {
        const eventSection = this.extractSection(content, 'イベント情報');
        
        return {
            name: this.extractField(eventSection, 'イベント名'),
            dateStart: this.parseEventDate(this.extractField(eventSection, '開催日'), true),
            dateEnd: this.parseEventDate(this.extractField(eventSection, '開催日'), false),
            time: this.extractField(eventSection, '時間'),
            venue: this.extractField(eventSection, '会場'),
            url: this.extractField(eventSection, 'URL')
        };
    }

    extractReservationInfo(content) {
        const reservationSection = this.extractSection(content, 'ご予約情報');
        
        return {
            date: this.parseReservationDate(this.extractField(reservationSection, 'ご希望日')),
            time: this.extractField(reservationSection, 'ご希望時間')
        };
    }

    extractCustomerInfo(content) {
        const customerSection = this.extractSection(content, 'お客様情報');
        
        return {
            name: this.extractField(customerSection, 'お名前'),
            furigana: this.extractField(customerSection, 'フリガナ'),
            email: this.extractField(customerSection, 'メールアドレス'),
            phone: this.extractField(customerSection, '電話番号'),
            age: this.parseAge(this.extractField(customerSection, '年齢')),
            rent: this.parseAmount(this.extractField(customerSection, '毎月の家賃')),
            payment: this.parseAmount(this.extractField(customerSection, '月々の返済額')),
            postalCode: this.extractField(customerSection, '郵便番号'),
            address: this.extractField(customerSection, 'ご住所'),
            comments: this.extractField(customerSection, 'ご意見・ご質問等'),
            leadSource: this.extractField(customerSection, 'ご予約のきっかけ')
        };
    }

    extractSurveyInfo(content) {
        const surveySection = this.extractSection(content, 'アンケート');
        
        return {
            housingType: this.extractSurveyAnswer(surveySection, '新しいお住まいのご希望を教えてください'),
            considerationPeriod: this.extractSurveyAnswer(surveySection, 'いつ頃からご検討を始められましたか')
        };
    }

    extractSection(content, sectionName) {
        const regex = new RegExp(`${sectionName}[\\s\\S]*?(?=={8,}|$)`, 'g');
        const match = content.match(regex);
        return match ? match[0] : '';
    }

    extractField(section, fieldName) {
        const regex = new RegExp(`${fieldName}\\s*[:：]\\s*(.+?)(?=\\n|$)`, 'g');
        const match = regex.exec(section);
        return match ? match[1].trim() : '';
    }

    extractSurveyAnswer(section, question) {
        const regex = new RegExp(`▼${question}[\\s\\S]*?▼\\s*(.+?)(?=▼|$)`, 'g');
        const match = regex.exec(section);
        return match ? match[1].trim() : '';
    }

    parseEventDate(dateStr, isStart) {
        if (!dateStr) return null;
        
        // Handle date ranges like "2025年9月1日(月) - 9月15日(月)"
        const match = dateStr.match(/(\d{4})年(\d+)月(\d+)日.*?-.*?(\d+)月(\d+)日/);
        if (match) {
            const year = parseInt(match[1]);
            const startMonth = parseInt(match[2]);
            const startDay = parseInt(match[3]);
            const endMonth = parseInt(match[4]);
            const endDay = parseInt(match[5]);
            
            if (isStart) {
                return `${year}-${startMonth.toString().padStart(2, '0')}-${startDay.toString().padStart(2, '0')}`;
            } else {
                return `${year}-${endMonth.toString().padStart(2, '0')}-${endDay.toString().padStart(2, '0')}`;
            }
        }
        
        return null;
    }

    parseReservationDate(dateStr) {
        if (!dateStr) return null;
        
        const match = dateStr.match(/(\d{4})年(\d+)月(\d+)日/);
        if (match) {
            const year = parseInt(match[1]);
            const month = parseInt(match[2]);
            const day = parseInt(match[3]);
            return `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        }
        
        return null;
    }

    parseAge(ageStr) {
        if (!ageStr) return null;
        const match = ageStr.match(/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    parseAmount(amountStr) {
        if (!amountStr) return null;
        const match = amountStr.match(/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    validateData(data) {
        const errors = [];
        const required = ['customerName', 'customerEmail'];
        
        required.forEach(field => {
            if (!data[field]) {
                errors.push(`Missing required field: ${field}`);
            }
        });
        
        // Email validation
        if (data.customerEmail && !this.isValidEmail(data.customerEmail)) {
            errors.push('Invalid email format');
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
}

module.exports = new EmailParser();