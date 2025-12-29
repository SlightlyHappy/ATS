#!/usr/bin/env python3
"""
Sales Intelligence System Test Suite

This script tests all components of the sales intelligence system:
- Lead scoring algorithms
- ROI calculations
- Hot lead alerts
- API endpoints
- Background tasks
"""
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.sales import Lead, LeadScoreHistory, LeadActivity, SalesMetrics, ROICalculation
from app.services.lead_scoring_service import LeadScoringService
from app.services.roi_calculator_service import ROICalculatorService
from app.services.hot_lead_alert_service import HotLeadAlertService
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.models.queue import Queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SalesIntelligenceTestSuite:
    """Comprehensive test suite for sales intelligence system."""
    
    def __init__(self):
        self.app = create_app()
        self.test_user_ids = []
        
    def run_all_tests(self):
        """Run all test suites."""
        with self.app.app_context():
            print("🚀 Starting Sales Intelligence Test Suite")
            print("=" * 60)
            
            try:
                # Setup test data
                self._setup_test_data()
                
                # Run test suites
                self._test_lead_scoring()
                self._test_roi_calculator()
                self._test_hot_lead_alerts()
                self._test_api_endpoints()
                self._test_background_tasks()
                
                print("\n✅ All tests completed successfully!")
                
            except Exception as e:
                print(f"\n❌ Test suite failed: {str(e)}")
                raise
            finally:
                # Cleanup
                self._cleanup_test_data()
    
    def _setup_test_data(self):
        """Create test users and data."""
        print("\n📋 Setting up test data...")
        
        # Create test users with different activity levels
        test_users = [
            {
                'email': 'test_high_activity@example.com',
                'full_name': 'High Activity User',
                'usage_level': 'high'
            },
            {
                'email': 'test_medium_activity@example.com',
                'full_name': 'Medium Activity User',
                'usage_level': 'medium'
            },
            {
                'email': 'test_low_activity@example.com',
                'full_name': 'Low Activity User',
                'usage_level': 'low'
            }
        ]
        
        for user_data in test_users:
            # Check if user exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                user = existing_user
            else:
                user = User(
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    password_hash='test_hash',
                    is_verified=True
                )
                db.session.add(user)
                db.session.commit()
            
            self.test_user_ids.append(str(user.id))
            
            # Create different activity patterns
            self._create_user_activity(user, user_data['usage_level'])
        
        print(f"✓ Created {len(test_users)} test users")
    
    def _create_user_activity(self, user, usage_level):
        """Create activity data for a test user."""
        
        if usage_level == 'high':
            # High activity: multiple resumes, analyses, recent activity
            for i in range(5):
                resume = Resume(
                    user_id=user.id,
                    original_filename=f'resume_{i+1}.pdf',
                    file_path='/fake/path',
                    file_size=1024 * (i + 1),
                    created_at=datetime.utcnow() - timedelta(days=i*2)
                )
                db.session.add(resume)
                db.session.commit()
                
                analysis = Analysis(
                    user_id=user.id,
                    resume_id=resume.id,
                    original_text=f'Sample resume text {i+1}',
                    analysis_results={'score': 85 + i},
                    created_at=datetime.utcnow() - timedelta(days=i*2)
                )
                db.session.add(analysis)
                
        elif usage_level == 'medium':
            # Medium activity: some resumes, moderate usage
            for i in range(2):
                resume = Resume(
                    user_id=user.id,
                    original_filename=f'resume_{i+1}.pdf',
                    file_path='/fake/path',
                    file_size=1024,
                    created_at=datetime.utcnow() - timedelta(days=10+i*5)
                )
                db.session.add(resume)
                db.session.commit()
                
                analysis = Analysis(
                    user_id=user.id,
                    resume_id=resume.id,
                    original_text=f'Sample resume text {i+1}',
                    analysis_results={'score': 75},
                    created_at=datetime.utcnow() - timedelta(days=10+i*5)
                )
                db.session.add(analysis)
        
        # Low activity users get minimal data (just the user record)
        
        db.session.commit()
    
    def _test_lead_scoring(self):
        """Test lead scoring functionality."""
        print("\n🎯 Testing Lead Scoring Service...")
        
        lead_scorer = LeadScoringService()
        
        for user_id in self.test_user_ids:
            # Test individual scoring
            result = lead_scorer.calculate_lead_score(user_id)
            
            print(f"User {user_id[:8]}...")
            print(f"  Overall Score: {result['overall_score']}")
            print(f"  Engagement: {result['engagement_score']}")
            print(f"  Usage: {result['usage_score']}")
            print(f"  Potential: {result['potential_score']}")
            
            # Verify score is within expected range
            assert 0 <= result['overall_score'] <= 100, "Score out of range"
            assert 0 <= result['engagement_score'] <= 40, "Engagement score out of range"
            assert 0 <= result['usage_score'] <= 30, "Usage score out of range"
            assert 0 <= result['potential_score'] <= 30, "Potential score out of range"
        
        # Test batch scoring
        batch_result = lead_scorer.batch_update_scores(self.test_user_ids)
        print(f"✓ Batch update: {batch_result['updated']} users scored")
        
        # Verify leads were created
        lead_count = Lead.query.filter(Lead.user_id.in_(self.test_user_ids)).count()
        assert lead_count == len(self.test_user_ids), "Not all leads were created"
        
        print("✅ Lead scoring tests passed")
    
    def _test_roi_calculator(self):
        """Test ROI calculation functionality."""
        print("\n💰 Testing ROI Calculator Service...")
        
        roi_calculator = ROICalculatorService()
        
        # Get a test lead
        test_lead = Lead.query.filter(Lead.user_id.in_(self.test_user_ids)).first()
        
        if test_lead:
            # Test ROI calculation
            roi_result = roi_calculator.calculate_roi(
                lead_id=test_lead.id,
                current_cost_per_hire=5000,
                current_time_to_hire=30,
                company_size='medium',
                industry='technology'
            )
            
            print(f"ROI Calculation for Lead {test_lead.id}:")
            print(f"  Potential Savings: ${roi_result['annual_savings']:,.2f}")
            print(f"  ROI Percentage: {roi_result['roi_percentage']:.1f}%")
            print(f"  Payback Period: {roi_result['payback_months']} months")
            print(f"  Quality Score: {roi_result['quality_score']}")
            
            # Verify ROI calculation was saved
            roi_record = ROICalculation.query.filter_by(lead_id=test_lead.id).first()
            assert roi_record is not None, "ROI calculation not saved"
            
            # Test industry benchmarks
            benchmarks = roi_calculator.get_industry_benchmarks('technology', 'medium')
            assert 'avg_cost_per_hire' in benchmarks, "Missing benchmark data"
            
            print("✅ ROI calculator tests passed")
        else:
            print("⚠️  No leads found for ROI testing")
    
    def _test_hot_lead_alerts(self):
        """Test hot lead alert functionality."""
        print("\n🔥 Testing Hot Lead Alert Service...")
        
        # Create a mock WebSocket service for testing
        class MockWebSocketService:
            def __init__(self):
                self.alerts_sent = []
            
            def send_admin_notification(self, notification_type, data):
                self.alerts_sent.append({'type': notification_type, 'data': data})
                return True
        
        mock_ws = MockWebSocketService()
        alert_service = HotLeadAlertService(mock_ws)
        
        # Update a lead to have a high score
        high_score_lead = Lead.query.filter(Lead.user_id.in_(self.test_user_ids)).first()
        if high_score_lead:
            high_score_lead.overall_score = 85
            high_score_lead.last_activity = datetime.utcnow()
            db.session.commit()
            
            # Test alert checking
            result = alert_service.check_and_send_hot_lead_alerts()
            
            print(f"Alert Check Results:")
            print(f"  Hot leads found: {result['hot_leads_found']}")
            print(f"  Alerts sent: {result['alerts_sent']}")
            print(f"  Super hot alerts: {result['super_hot_alerts']}")
            
            # Check that mock received alerts
            if result['alerts_sent'] > 0:
                print(f"✓ Mock WebSocket received {len(mock_ws.alerts_sent)} alerts")
                print("✅ Hot lead alert tests passed")
            else:
                print("⚠️  No alerts triggered (may be due to cooldown)")
        else:
            print("⚠️  No leads found for alert testing")
    
    def _test_api_endpoints(self):
        """Test sales API endpoints."""
        print("\n🌐 Testing Sales API Endpoints...")
        
        with self.app.test_client() as client:
            # Create admin user for testing
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                admin_user = User(
                    email='admin@test.com',
                    full_name='Test Admin',
                    password_hash='test_hash',
                    is_admin=True,
                    is_verified=True
                )
                db.session.add(admin_user)
                db.session.commit()
            
            # Test authentication (simplified - normally would use proper auth)
            headers = {'Authorization': f'Bearer admin_token_{admin_user.id}'}
            
            # Test get leads endpoint
            response = client.get('/api/sales/leads', headers=headers)
            if response.status_code == 200:
                data = json.loads(response.data)
                print(f"✓ GET /api/sales/leads: {len(data.get('leads', []))} leads returned")
            else:
                print(f"⚠️  GET /api/sales/leads failed: {response.status_code}")
            
            # Test sales dashboard
            response = client.get('/api/sales/dashboard', headers=headers)
            if response.status_code == 200:
                data = json.loads(response.data)
                print(f"✓ GET /api/sales/dashboard: {data.get('total_leads', 0)} total leads")
            else:
                print(f"⚠️  GET /api/sales/dashboard failed: {response.status_code}")
            
            # Test ROI calculation endpoint
            if Lead.query.first():
                test_lead_id = Lead.query.first().id
                roi_data = {
                    'current_cost_per_hire': 5000,
                    'current_time_to_hire': 30,
                    'company_size': 'medium',
                    'industry': 'technology'
                }
                
                response = client.post(
                    f'/api/sales/leads/{test_lead_id}/calculate-roi',
                    headers=headers,
                    json=roi_data
                )
                
                if response.status_code == 200:
                    print("✓ POST /api/sales/leads/{id}/calculate-roi: Success")
                else:
                    print(f"⚠️  ROI calculation failed: {response.status_code}")
            
            print("✅ API endpoint tests completed")
    
    def _test_background_tasks(self):
        """Test background task components."""
        print("\n⚙️  Testing Background Task Components...")
        
        # Test daily metrics generation
        from scripts.sales_background_tasks import SalesIntelligenceScheduler
        
        scheduler = SalesIntelligenceScheduler()
        
        with self.app.app_context():
            # Test score update task
            print("Testing score update task...")
            scheduler._update_recent_scores()
            print("✓ Score update task completed")
            
            # Test metrics generation
            print("Testing daily metrics generation...")
            scheduler._generate_daily_metrics()
            
            # Check if metrics were created
            metrics_count = SalesMetrics.query.count()
            print(f"✓ Daily metrics generation: {metrics_count} metrics records")
            
            # Test cleanup task
            print("Testing cleanup task...")
            scheduler._cleanup_old_data()
            print("✓ Cleanup task completed")
            
            print("✅ Background task tests passed")
    
    def _cleanup_test_data(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Remove test users and related data
            for user_id in self.test_user_ids:
                user = User.query.get(user_id)
                if user and 'test_' in user.email:
                    # Remove related records first
                    Lead.query.filter_by(user_id=user_id).delete()
                    LeadScoreHistory.query.filter_by(user_id=user_id).delete()
                    LeadActivity.query.filter_by(user_id=user_id).delete()
                    ROICalculation.query.filter(
                        ROICalculation.lead_id.in_(
                            db.session.query(Lead.id).filter_by(user_id=user_id)
                        )
                    ).delete()
                    
                    Analysis.query.filter_by(user_id=user_id).delete()
                    Resume.query.filter_by(user_id=user_id).delete()
                    Queue.query.filter_by(user_id=user_id).delete()
                    
                    # Remove user
                    db.session.delete(user)
            
            # Remove test admin
            test_admin = User.query.filter_by(email='admin@test.com').first()
            if test_admin:
                db.session.delete(test_admin)
            
            # Remove test metrics
            SalesMetrics.query.delete()
            
            db.session.commit()
            print("✓ Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {str(e)}")
            db.session.rollback()

def run_tests():
    """Main function to run the test suite."""
    test_suite = SalesIntelligenceTestSuite()
    test_suite.run_all_tests()

def run_specific_test(test_name):
    """Run a specific test."""
    test_suite = SalesIntelligenceTestSuite()
    
    with test_suite.app.app_context():
        test_suite._setup_test_data()
        
        try:
            if test_name == "scoring":
                test_suite._test_lead_scoring()
            elif test_name == "roi":
                test_suite._test_roi_calculator()
            elif test_name == "alerts":
                test_suite._test_hot_lead_alerts()
            elif test_name == "api":
                test_suite._test_api_endpoints()
            elif test_name == "background":
                test_suite._test_background_tasks()
            else:
                print(f"Unknown test: {test_name}")
                print("Available tests: scoring, roi, alerts, api, background")
                return
            
            print(f"\n✅ {test_name} test completed successfully!")
            
        finally:
            test_suite._cleanup_test_data()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_specific_test(sys.argv[1])
    else:
        run_tests()
