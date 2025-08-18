"""
Test for UI integration with orchestrator
"""
import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from ui_app import LinkedInAutomationUI


class TestUIIntegration:
    """Test the UI integration with the orchestrator"""
    
    def test_ui_app_initialization(self):
        """Test that the UI app can be initialized"""
        # This test verifies the UI can be created without errors
        # We'll mock the mainloop to avoid actually opening a window
        with patch('customtkinter.CTk.mainloop'):
            app = LinkedInAutomationUI()
            assert app is not None
            assert hasattr(app, 'start_automation')
            assert hasattr(app, 'run_automation_async')
    
    @pytest.mark.asyncio
    async def test_run_automation_async_integration(self):
        """Test that the UI's run_automation_async method properly calls the orchestrator"""
        with patch('customtkinter.CTk.mainloop'):
            app = LinkedInAutomationUI()
            
            # Mock the orchestrator's run function
            with patch('automation.orchestrator.run') as mock_run:
                mock_run.return_value = None
                
                # Mock environment variables
                with patch.dict(os.environ, {
                    'LINKEDIN_EMAIL': 'test@example.com',
                    'LINKEDIN_PASSWORD': 'testpass',
                    'SEARCH_KEYWORDS': 'software engineer'
                }):
                    # Mock UI input values
                    app.email_entry = MagicMock()
                    app.email_entry.get.return_value = 'test@example.com'
                    
                    app.password_entry = MagicMock()
                    app.password_entry.get.return_value = 'testpass'
                    
                    app.headless_var = MagicMock()
                    app.headless_var.get.return_value = True
                    
                    app.test_mode_var = MagicMock()
                    app.test_mode_var.get.return_value = True
                    
                    # Mock logging
                    with patch.object(app, 'add_log_message'):
                        # Call the method
                        await app.run_automation_async(
                            keywords='software engineer',
                            location='San Francisco',
                            max_profiles=5
                        )
                        
                        # Verify the orchestrator was called
                        mock_run.assert_called_once()
    
    def test_start_automation_method_exists(self):
        """Test that the start_automation method exists and is callable"""
        with patch('customtkinter.CTk.mainloop'):
            app = LinkedInAutomationUI()
            assert callable(app.start_automation)
    
    def test_ui_has_required_input_fields(self):
        """Test that the UI has all required input fields"""
        with patch('customtkinter.CTk.mainloop'):
            app = LinkedInAutomationUI()
            
            # Check that required input fields exist
            assert hasattr(app, 'email_entry')
            assert hasattr(app, 'password_entry')
            assert hasattr(app, 'keywords_entry')
            assert hasattr(app, 'location_entry')
            assert hasattr(app, 'max_profiles_slider')
    
    def test_main_py_imports_ui(self):
        """Test that main.py correctly imports and runs the UI"""
        # This test verifies the main.py file structure
        with open('main.py', 'r') as f:
            content = f.read()
            assert 'from ui_app import main as run_ui' in content
            assert 'run_ui()' in content


if __name__ == "__main__":
    pytest.main([__file__])
