// Simple test script to verify frontend can connect to backend
const http = require('http');

async function testConnection() {
    console.log('🧪 Testing frontend -> backend connection...');
    
    return new Promise((resolve, reject) => {
        console.log('📡 Making request to http://localhost:8000/api/health...');
        
        const req = http.get('http://localhost:8000/api/health', (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                console.log('✅ SUCCESS! Backend connection working:');
                console.log('Status:', res.statusCode);
                console.log('Headers:', res.headers);
                console.log('Data:', data);
                resolve();
            });
        });
        
        req.on('error', (error) => {
            console.error('❌ FAILED! Backend connection error:');
            console.error('Error message:', error.message);
            console.error('Error code:', error.code);
            reject(error);
        });
        
        req.setTimeout(5000, () => {
            console.error('❌ TIMEOUT: Request took too long');
            req.destroy();
            reject(new Error('Timeout'));
        });
    });
}

testConnection();
