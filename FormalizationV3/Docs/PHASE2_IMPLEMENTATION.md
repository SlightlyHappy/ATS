# 🚀 Phase 2: RazorPay Integration & Premium Processing

**Objective**: Transform the trial credit system into a revenue-generating B2B SaaS platform with instant payment capabilities.

## Overview

Building on the successful Phase 1 implementation, Phase 2 adds:
- **RazorPay payment integration** for Indian market 
- **Queue skip functionality** (₹40 instant processing)
- **Premium credit purchases** (10 credits ₹300, 25 credits ₹650)
- **Cloud AI routing** for premium users (OpenAI/Anthropic)
- **Automated sales triggers** based on usage patterns

## Technical Architecture

### Payment Flow Design
```
User Needs Processing → Credit Check → Payment Options
                                        ↓
┌─ SUFFICIENT CREDITS ──→ Process with Ollama/Queue ──→ Results
├─ INSUFFICIENT CREDITS ─→ Show Premium Options ────→ Payment Gateway
├─ QUEUE BUSY ──────────→ Offer Skip (₹40) ────────→ RazorPay
└─ HIGH USAGE ─────────→ Enterprise Contact ──────→ Sales Team
```

### RazorPay Integration Points
```
Frontend Request → Payment Creation → RazorPay Gateway → Webhook Verification → Credit Addition
       ↑                                                           ↓
   User Action                                               Background Processing
```

## Implementation Plan

### Step 1: RazorPay Setup & Configuration

#### 1.1 Environment Configuration
```bash
# Add to .env or Railway environment
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx        # Test key for development
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxx     # Secret key for API calls
RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxx # Webhook signature verification
```

#### 1.2 RazorPay Client Setup
Create `payment_manager.py`:
```python
class RazorPayManager:
    def __init__(self):
        self.client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
    
    def create_order(self, amount_inr: int, user_id: str, order_type: str):
        # Create RazorPay order for payment
        
    def verify_payment(self, payment_id: str, order_id: str, signature: str):
        # Verify payment signature
        
    def handle_webhook(self, webhook_body: str, signature: str):
        # Process RazorPay webhooks
```

### Step 2: Payment Endpoints

#### 2.1 Order Creation Endpoint
```python
@app.route('/api/payment/create-order', methods=['POST'])
@auth.require_auth
def create_payment_order():
    """Create RazorPay order for credit purchase or queue skip"""
    user = auth.get_current_user()
    data = request.get_json()
    
    order_type = data.get('type')  # 'queue_skip', 'credits_10', 'credits_25'
    
    # Map order types to prices
    prices = {
        'queue_skip': 40,
        'credits_10': 300, 
        'credits_25': 650
    }
    
    # Create RazorPay order
    order = payment_manager.create_order(
        amount_inr=prices[order_type],
        user_id=user['user_id'],
        order_type=order_type
    )
    
    return jsonify({
        "success": True,
        "order": order,
        "key_id": RAZORPAY_KEY_ID
    })
```

#### 2.2 Payment Verification Endpoint
```python
@app.route('/api/payment/verify', methods=['POST'])
@auth.require_auth
def verify_payment():
    """Verify payment and add credits/skip queue"""
    user = auth.get_current_user()
    data = request.get_json()
    
    # Verify payment with RazorPay
    if payment_manager.verify_payment(
        data['payment_id'], 
        data['order_id'], 
        data['signature']
    ):
        # Payment successful - add credits or skip queue
        order_type = get_order_type_from_order_id(data['order_id'])
        
        if order_type == 'queue_skip':
            # Skip queue for pending request
            success = queue_manager.skip_queue(
                data.get('request_id'), 
                payment_verified=True
            )
        else:
            # Add premium credits
            credits_map = {'credits_10': 10, 'credits_25': 25}
            credit_manager.add_premium_credits(
                user['user_id'], 
                credits_map[order_type],
                payment_id=data['payment_id']
            )
        
        return jsonify({"success": True, "message": "Payment verified"})
    else:
        return jsonify({"error": "Payment verification failed"}), 400
```

### Step 3: Cloud AI Premium Processing

#### 3.1 Premium AI Router
Enhance existing `ai_processor.py`:
```python
class PremiumAIProcessor:
    def __init__(self):
        self.openai_client = OpenAI()  # For premium processing
        self.anthropic_client = Anthropic()  # For premium processing
        
    async def process_premium_request(self, request_data, processing_type):
        """Route premium requests to cloud AI providers"""
        if processing_type == 'resume_analysis':
            return await self._premium_resume_analysis(request_data)
        elif processing_type == 'legal_query':
            return await self._premium_legal_query(request_data)
        
    async def _premium_resume_analysis(self, request_data):
        """Enhanced resume analysis using OpenAI GPT-4"""
        # Use GPT-4 for superior analysis quality
        
    async def _premium_legal_query(self, request_data):
        """Enhanced legal query using Claude-3"""
        # Use Claude-3 for legal expertise
```

#### 3.2 Smart Routing Logic
Update `queue_manager.py`:
```python
def _process_request(self, request: QueuedRequest):
    """Enhanced processing with premium routing"""
    if request.processing_tier == ProcessingTier.PREMIUM_INSTANT:
        # Route to cloud AI for premium users
        return await self._process_premium_request(request)
    else:
        # Use Ollama for trial users
        return await self._process_standard_request(request)
```

### Step 4: Enhanced Frontend Integration

#### 4.1 Payment UI Components
```javascript
// Credit status display with payment options
function CreditStatus({ credits, onPurchase }) {
    return (
        <div className="credit-status">
            <div className="credits-remaining">{credits} credits left</div>
            {credits < 20 && (
                <div className="low-credits-warning">
                    <h3>Running Low on Credits!</h3>
                    <button onClick={() => onPurchase('credits_10')}>
                        Buy 10 Credits - ₹300
                    </button>
                    <button onClick={() => onPurchase('credits_25')}>
                        Buy 25 Credits - ₹650 (Best Value)
                    </button>
                </div>
            )}
        </div>
    );
}

// Queue skip option
function QueueStatus({ position, onSkip }) {
    return (
        <div className="queue-status">
            <p>Position in queue: {position}</p>
            <p>Estimated wait: 3-5 minutes</p>
            <button onClick={onSkip} className="skip-queue-btn">
                Skip Queue for ₹40 - Get Results Instantly!
            </button>
        </div>
    );
}
```

#### 4.2 RazorPay Integration
```javascript
function initializePayment(orderData) {
    const options = {
        key: orderData.key_id,
        amount: orderData.order.amount,
        currency: 'INR',
        name: 'HR ATS Premium',
        description: 'Premium Credits Purchase',
        order_id: orderData.order.id,
        handler: function(response) {
            // Verify payment on backend
            verifyPayment(response);
        },
        prefill: {
            name: user.name,
            email: user.email
        },
        theme: {
            color: '#3399cc'
        }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
}
```

### Step 5: Sales Intelligence Enhancement

#### 5.1 Advanced Lead Scoring
Update `credit_manager.py`:
```python
def _calculate_advanced_lead_score(self, user_id: int, usage_pattern: Dict) -> int:
    """Enhanced lead scoring with payment behavior"""
    score = 0
    
    # Base usage scoring
    total_credits_used = usage_pattern.get("total_credits_used", 0)
    score += min(total_credits_used * 2, 40)  # Up to 40 points for usage
    
    # Payment behavior scoring
    payment_history = self._get_payment_history(user_id)
    if payment_history:
        score += 30  # Has made payments - high intent
        
    # Feature diversity scoring
    features = usage_pattern.get("features", {})
    if len(features) >= 3:
        score += 20  # Uses multiple features - power user
        
    # Time-based scoring
    if self._is_recent_active_user(user_id):
        score += 10  # Recent activity - hot lead
        
    return min(score, 100)
```

#### 5.2 Automated Sales Triggers
```python
def _trigger_sales_actions(self, user_id: int, credit_status: CreditStatus):
    """Automated sales actions based on user behavior"""
    
    if credit_status.lead_score >= 80:
        # Hot lead - immediate sales contact
        self._send_sales_alert("hot_lead", user_id, credit_status)
        
    elif credit_status.credits_remaining <= 5:
        # Almost out of credits - offer enterprise
        self._send_enterprise_offer_email(user_id)
        
    elif self._has_made_multiple_payments(user_id):
        # Paying customer - upsell opportunity
        self._schedule_sales_call(user_id)
```

## Testing Strategy

### Phase 2 Testing Checklist

#### Payment Flow Testing
- [ ] Order creation with correct amounts
- [ ] RazorPay gateway integration
- [ ] Payment verification and webhook handling
- [ ] Credit addition after successful payment
- [ ] Queue skip functionality with payment

#### Premium Processing Testing
- [ ] Cloud AI routing for premium users
- [ ] OpenAI integration for resume analysis
- [ ] Anthropic integration for legal queries
- [ ] Quality comparison: Premium vs Free processing

#### Sales Intelligence Testing
- [ ] Enhanced lead scoring with payment data
- [ ] Automated sales triggers
- [ ] Enterprise prospect identification
- [ ] Revenue tracking and analytics

## Deployment Strategy

### Environment Setup
1. **Development**: Use RazorPay test keys
2. **Staging**: Test complete payment flow
3. **Production**: Switch to live RazorPay keys

### Monitoring & Analytics
```python
# Key metrics to track
- Payment conversion rate
- Average revenue per user (ARPU)
- Queue skip adoption rate
- Premium feature usage
- Sales qualified leads (SQL) rate
```

## Revenue Projections

### Month 1 Targets
- **Queue Skip Revenue**: 100 users × ₹40 = ₹4,000
- **Credit Purchases**: 50 users × ₹400 avg = ₹20,000
- **Total Revenue**: ₹24,000 (~$300)

### Month 3 Targets
- **Steady Users**: 500 active users
- **Monthly Revenue**: ₹80,000-₹120,000 ($1,000-$1,500)
- **Enterprise Prospects**: 10-15 qualified leads

### Success Metrics
- **Payment Conversion**: >5% of trial users make payments
- **Queue Skip Adoption**: >15% when queue is busy
- **Enterprise Lead Rate**: >2% of users become enterprise prospects
- **Revenue Growth**: 20% month-over-month

## Risk Mitigation

### Technical Risks
- **Payment Gateway Failures**: Implement retry logic and fallbacks
- **Cloud AI Rate Limits**: Monitor usage and implement circuit breakers
- **Security**: PCI compliance for payment handling

### Business Risks
- **Low Conversion**: A/B test pricing and messaging
- **Regional Payment Issues**: Support multiple payment methods
- **Competition**: Focus on unique legal compliance features

## Next Steps

1. **Week 1**: RazorPay integration and basic payment flow
2. **Week 2**: Premium AI routing and cloud processing
3. **Week 3**: Enhanced sales intelligence and automation
4. **Week 4**: Testing, optimization, and production deployment

This Phase 2 implementation will transform the HR ATS from a trial-based system into a revenue-generating B2B SaaS platform, perfectly positioned for enterprise sales and growth.
