from django.test import TestCase

# Create your tests here.
def test_panic_button_creates_critical_report(self):
        """Test that the panic button creates a Critical report"""
        self.client.login(username='student1', password='Password123!')
        
        import json
        response = self.client.post(
            '/panic/', 
            data=json.dumps({'latitude': -28.7282, 'longitude': 24.7499}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that a report was created with Critical priority
        from dashboard.models import Report
        report = Report.objects.latest('created_at')
        self.assertEqual(report.priority, 'critical')
        self.assertIn('-28.7282', report.location)