const axios = require('axios');
require('dotenv').config();

const testEmailContent = `[STYLE HOUSE] イベントの参加お申し込みがありました。 2025-09-02 22:34:57
========================================
イベント情報
========================================
イベント名 : 【花博記念公園ハウジングガーデン】モンテッソーリの木製パズルボックスがもらえる♪豪華特典つき・9月限定イベント！
開催日 : 2025年9月1日(月) - 9月15日(月)
時間 : am9:30~pm6:00 (定休日:水曜日)
会場 : STYLE HOUSE　花博記念公園ハウジングガーデン
URL : https://www.taniue.jp/event/details_105.html
========================================
ご予約情報
========================================
ご希望日 ： 2025年9月8日
ご希望時間 ： 11:30～13:00
========================================
お客様情報
========================================
お名前 : 浜崎沙綾
フリガナ : ハマザキサヤ
メールアドレス : utosabu.adhikari@allagi.jp
電話番号 : 09092734235
年齢 : 23歳
毎月の家賃 : 9万円
月々の返済額 : 9万円
郵便番号 : 〒655-0852
ご住所 : 兵庫県神戸市垂水区名谷町字奥之坊2107-1リヴェールコート名谷101
ご意見・ご質問等 : 
ご予約のきっかけ : インスタグラム
========================================
アンケート
========================================
▼新しいお住まいのご希望を教えてください。▼
土地があって新築
▼新しいお住まいについて、いつ頃からご検討を始められましたか？▼
3ヶ月前から
▼ご希望エリアを教えてください。エリアまたは小中学区をご記入ください。▼

▼ご職場の最寄り駅はどちらですか？▼

▼ご希望の通勤方法は何でしょうか？▼

▼ご実家はどちらにございますか？▼

▼ご入居希望時期はありますか？▼

▼今までスタイルハウスの展示場にご来場された事がありますか？▼

▼新しいお住まいをご検討される理由は何ですか？▼

▼その他のご検討理由▼

▼今後のスケジュールはどの様なイメージですか？▼

▼現在のお住まいはどのタイプですか？▼

▼お家の広さはどのぐらいでお考えですか？▼
建物：　土地：　間取り：

▼ご入居予定の方▼

▼土地や諸費用を含む総予算はいくらですか？▼

▼ご希望の返済額を教えて頂けますか？▼

▼年度のご年収を教えて頂けますか？▼

▼勤続年数を教えて頂けますか？▼

▼その他、ご年収がある方はいらっしゃいますか？▼

▼頭金のご予算はお決まりですか▼

▼その他ローンはございますか？▼

▼STYLE HOUSEに期待することは何ですか？▼

▼ご質問・ご相談など、先に伝えておきたいことはございますか？▼
========================================`;

async function testEmailParsing() {
    const baseUrl = process.env.TEST_URL || 'http://localhost:3000';
    
    console.log('🧪 Testing Email Parsing...');
    console.log('📧 Target Email: utosabu.adhikari@allagi.jp');
    console.log('🔗 Testing URL:', baseUrl);
    console.log('=====================================\n');
    
    try {
        const response = await axios.post(`${baseUrl}/test/parse-email`, {
            content: testEmailContent
        }, {
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('🎉 TEST SUCCESSFUL!');
        console.log('=====================================');
        console.log('📊 Extracted Data:');
        console.log('   👤 Customer:', response.data.data.customerName);
        console.log('   📧 Email:', response.data.data.customerEmail);
        console.log('   🎪 Event:', response.data.data.eventName);
        console.log('   📅 Desired Date:', response.data.data.desiredDate);
        console.log('   🕐 Desired Time:', response.data.data.desiredTime);
        console.log('   📍 Address:', response.data.data.address);
        console.log('   📱 Phone:', response.data.data.customerPhone);
        
        if (response.data.recordId) {
            console.log('   💾 Lark Base Record ID:', response.data.recordId);
            console.log('   ✅ Data successfully saved to Lark Base!');
        } else {
            console.log('   ⚠️ Email parsing worked, but Lark Base connection needed');
        }
        
        console.log('\n📋 Next Steps:');
        console.log('1. Check your Lark Base for the new record');
        console.log('2. Verify all field mappings are correct');
        console.log('3. Deploy to production');
        
    } catch (error) {
        console.log('❌ TEST FAILED!');
        console.log('=====================================');
        if (error.response) {
            console.log('🔥 Error Status:', error.response.status);
            console.log('📝 Error Details:', JSON.stringify(error.response.data, null, 2));
        } else {
            console.log('🔥 Error Message:', error.message);
        }
        
        console.log('\n🛠️ Troubleshooting:');
        console.log('1. Make sure the server is running (npm run dev)');
        console.log('2. Check your .env file configuration');
        console.log('3. Verify Lark credentials are correct');
    }
}

// Health check function
async function testHealthCheck() {
    const baseUrl = process.env.TEST_URL || 'http://localhost:3000';
    
    console.log('🏥 Testing Server Health...');
    
    try {
        const response = await axios.get(`${baseUrl}/health`, { timeout: 10000 });
        console.log('✅ Server is healthy:', response.data.message);
        return true;
    } catch (error) {
        console.log('❌ Server health check failed:', error.message);
        console.log('💡 Make sure to run: npm run dev');
        return false;
    }
}

// Run tests
async function runAllTests() {
    console.log('🚀 LARK MAIL AUTOMATION - TEST SUITE');
    console.log('=====================================\n');
    
    const isHealthy = await testHealthCheck();
    if (isHealthy) {
        console.log(''); // Add spacing
        await testEmailParsing();
    }
    
    console.log('\n🎉 Testing Complete!');
}

if (require.main === module) {
    runAllTests();
}

module.exports = { testEmailParsing, testHealthCheck };