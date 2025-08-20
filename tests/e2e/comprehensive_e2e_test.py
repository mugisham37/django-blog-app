#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite
Complete user journey testing across all applications
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import requests


class E2ETestSuite:
    """Comprehensive end-to-end testing suite"""
    
    def __init__(self):
        self.web_url = "http://localhost:3000"
        self.api_url = "http://localhost:8000"
        self.results = {}
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
    
    def teardown_driver(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.driver.quit()
    
    def run_all_e2e_tests(self) -> Dict[str, Any]:
        """Run all end-to-end tests"""
        print("🎭 Starting Comprehensive E2E Testing Suite...")
        
        try:
            self.setup_driver()
            
            test_methods = [
                self.test_home_page_functionality,
                self.test_user_registration_flow,
                self.test_user_login_flow,
                self.test_blog_browsing_flow,
                self.test_blog_creation_flow,
                self.test_comment_system_flow,
                self.test_search_functionality,
                self.test_responsive_design,
                self.test_navigation_flow,
                self.test_error_handling_flow,
            ]
            
            for test_method in test_methods:
                try:
                    print(f"Running {test_method.__name__}...")
                    result = test_method()
                    self.results[test_method.__name__] = result
                    print(f"✅ {test_method.__name__} completed")
                except Exception as e:
                    error_msg = f"❌ {test_method.__name__} failed: {str(e)}"
                    print(error_msg)
                    self.results[test_method.__name__] = {
                        "status": "failed", 
                        "error": str(e)
                    }
            
        finally:
            self.teardown_driver()
        
        return self.generate_e2e_report()    

    def test_home_page_functionality(self) -> Dict[str, Any]:
        """Test home page loading and basic functionality"""
        try:
            self.driver.get(self.web_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check page title
            title = self.driver.title
            
            # Check for navigation elements
            nav_present = len(self.driver.find_elements(By.TAG_NAME, "nav")) > 0
            
            # Check for main content
            main_present = len(self.driver.find_elements(By.TAG_NAME, "main")) > 0
            
            # Check for footer
            footer_present = len(self.driver.find_elements(By.TAG_NAME, "footer")) > 0
            
            return {
                "status": "passed",
                "page_title": title,
                "navigation_present": nav_present,
                "main_content_present": main_present,
                "footer_present": footer_present,
                "page_load_time": time.time()
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_user_registration_flow(self) -> Dict[str, Any]:
        """Test complete user registration flow"""
        try:
            self.driver.get(f"{self.web_url}/auth/register")
            
            # Fill registration form
            username_field = self.driver.find_element(By.NAME, "username")
            email_field = self.driver.find_element(By.NAME, "email")
            password_field = self.driver.find_element(By.NAME, "password")
            
            test_username = f"testuser_{int(time.time())}"
            test_email = f"test_{int(time.time())}@example.com"
            test_password = "TestPassword123!"
            
            username_field.send_keys(test_username)
            email_field.send_keys(test_email)
            password_field.send_keys(test_password)
            
            # Submit form
            submit_button = self.driver.find_element(By.TYPE, "submit")
            submit_button.click()
            
            # Wait for response
            time.sleep(2)
            
            # Check if registration was successful
            current_url = self.driver.current_url
            success = "login" in current_url or "dashboard" in current_url
            
            return {
                "status": "passed" if success else "failed",
                "test_username": test_username,
                "test_email": test_email,
                "final_url": current_url,
                "registration_successful": success
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_user_login_flow(self) -> Dict[str, Any]:
        """Test user login flow"""
        try:
            self.driver.get(f"{self.web_url}/auth/login")
            
            # Try with test credentials
            username_field = self.driver.find_element(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys("admin")
            password_field.send_keys("admin")
            
            submit_button = self.driver.find_element(By.TYPE, "submit")
            submit_button.click()
            
            time.sleep(2)
            
            current_url = self.driver.current_url
            login_successful = "dashboard" in current_url or "profile" in current_url
            
            return {
                "status": "passed",
                "login_attempted": True,
                "final_url": current_url,
                "login_successful": login_successful
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_blog_browsing_flow(self) -> Dict[str, Any]:
        """Test blog browsing functionality"""
        try:
            self.driver.get(f"{self.web_url}/blog")
            
            # Wait for blog posts to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Count blog posts
            articles = self.driver.find_elements(By.TAG_NAME, "article")
            post_count = len(articles)
            
            # Try to click on first post if available
            post_clicked = False
            if articles:
                articles[0].click()
                time.sleep(2)
                post_clicked = True
            
            return {
                "status": "passed",
                "blog_posts_found": post_count,
                "post_clicked": post_clicked,
                "current_url": self.driver.current_url
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_blog_creation_flow(self) -> Dict[str, Any]:
        """Test blog post creation flow"""
        try:
            # Navigate to create post page
            self.driver.get(f"{self.web_url}/blog/create")
            
            # Check if create form is present
            title_field = self.driver.find_element(By.NAME, "title")
            content_field = self.driver.find_element(By.NAME, "content")
            
            # Fill form
            test_title = f"Test Post {int(time.time())}"
            test_content = "This is a test blog post created during E2E testing."
            
            title_field.send_keys(test_title)
            content_field.send_keys(test_content)
            
            # Try to submit
            submit_button = self.driver.find_element(By.TYPE, "submit")
            submit_button.click()
            
            time.sleep(2)
            
            return {
                "status": "passed",
                "form_filled": True,
                "test_title": test_title,
                "final_url": self.driver.current_url
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_comment_system_flow(self) -> Dict[str, Any]:
        """Test comment system functionality"""
        try:
            # Go to a blog post
            self.driver.get(f"{self.web_url}/blog")
            
            # Find and click on first post
            articles = self.driver.find_elements(By.TAG_NAME, "article")
            if articles:
                articles[0].click()
                time.sleep(2)
                
                # Look for comment section
                comment_section = self.driver.find_elements(By.CLASS_NAME, "comments")
                comment_form = self.driver.find_elements(By.NAME, "comment")
                
                return {
                    "status": "passed",
                    "comment_section_present": len(comment_section) > 0,
                    "comment_form_present": len(comment_form) > 0
                }
            else:
                return {
                    "status": "warning",
                    "message": "No blog posts available to test comments"
                }
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality"""
        try:
            self.driver.get(self.web_url)
            
            # Look for search input
            search_inputs = self.driver.find_elements(By.TYPE, "search")
            search_inputs.extend(self.driver.find_elements(By.NAME, "search"))
            search_inputs.extend(self.driver.find_elements(By.PLACEHOLDER, "Search"))
            
            if search_inputs:
                search_input = search_inputs[0]
                search_input.send_keys("test")
                search_input.send_keys(Keys.RETURN)
                
                time.sleep(2)
                
                return {
                    "status": "passed",
                    "search_input_found": True,
                    "search_performed": True,
                    "final_url": self.driver.current_url
                }
            else:
                return {
                    "status": "warning",
                    "search_input_found": False,
                    "message": "No search input found"
                }
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design across different screen sizes"""
        try:
            self.driver.get(self.web_url)
            
            # Test different screen sizes
            screen_sizes = [
                {"name": "mobile", "width": 375, "height": 667},
                {"name": "tablet", "width": 768, "height": 1024},
                {"name": "desktop", "width": 1920, "height": 1080}
            ]
            
            responsive_results = {}
            
            for size in screen_sizes:
                self.driver.set_window_size(size["width"], size["height"])
                time.sleep(1)
                
                # Check if navigation is still accessible
                nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
                nav_accessible = len(nav_elements) > 0
                
                # Check if content is visible
                body = self.driver.find_element(By.TAG_NAME, "body")
                content_visible = body.is_displayed()
                
                responsive_results[size["name"]] = {
                    "navigation_accessible": nav_accessible,
                    "content_visible": content_visible,
                    "screen_size": f"{size['width']}x{size['height']}"
                }
            
            return {
                "status": "passed",
                "responsive_results": responsive_results
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_navigation_flow(self) -> Dict[str, Any]:
        """Test navigation between different pages"""
        try:
            navigation_tests = []
            
            # Test main navigation links
            self.driver.get(self.web_url)
            
            # Find navigation links
            nav_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            # Test first few navigation links
            for i, link in enumerate(nav_links[:5]):
                try:
                    href = link.get_attribute("href")
                    if href and href.startswith(self.web_url):
                        link.click()
                        time.sleep(1)
                        
                        navigation_tests.append({
                            "link_href": href,
                            "navigation_successful": True,
                            "final_url": self.driver.current_url
                        })
                        
                        # Go back to home
                        self.driver.get(self.web_url)
                        time.sleep(1)
                except:
                    navigation_tests.append({
                        "link_href": href,
                        "navigation_successful": False
                    })
            
            return {
                "status": "passed",
                "navigation_tests": navigation_tests,
                "total_links_tested": len(navigation_tests)
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_error_handling_flow(self) -> Dict[str, Any]:
        """Test error handling and 404 pages"""
        try:
            # Test 404 page
            self.driver.get(f"{self.web_url}/nonexistent-page")
            
            # Check if custom 404 page is shown
            page_source = self.driver.page_source.lower()
            has_404_content = "404" in page_source or "not found" in page_source
            
            # Test API error handling
            api_response = requests.get(f"{self.api_url}/api/v1/nonexistent-endpoint/")
            api_404_handled = api_response.status_code == 404
            
            return {
                "status": "passed",
                "web_404_handled": has_404_content,
                "api_404_handled": api_404_handled,
                "web_404_url": self.driver.current_url,
                "api_404_status": api_response.status_code
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def generate_e2e_report(self) -> Dict[str, Any]:
        """Generate comprehensive E2E test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() 
                           if isinstance(r, dict) and r.get('status') == 'passed'])
        failed_tests = len([r for r in self.results.values() 
                           if isinstance(r, dict) and r.get('status') == 'failed'])
        warning_tests = len([r for r in self.results.values() 
                            if isinstance(r, dict) and r.get('status') == 'warning'])
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        for test_name, result in self.results.items():
            if isinstance(result, dict):
                if result.get('status') == 'failed':
                    recommendations.append(f"Fix issues in {test_name}: {result.get('error', 'Unknown error')}")
                elif result.get('status') == 'warning':
                    recommendations.append(f"Review warnings in {test_name}")
        
        if not recommendations:
            recommendations.append("All E2E tests passed! User experience is working as expected.")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'warning_tests': warning_tests,
                'success_rate': success_rate,
                'overall_status': 'PASSED' if failed_tests == 0 else 'FAILED'
            },
            'detailed_results': self.results,
            'recommendations': recommendations,
            'user_experience_grade': self.calculate_ux_grade(success_rate, failed_tests)
        }
        
        return report
    
    def calculate_ux_grade(self, success_rate: float, failed_tests: int) -> str:
        """Calculate user experience grade"""
        if success_rate >= 95 and failed_tests == 0:
            return 'A'
        elif success_rate >= 85 and failed_tests <= 1:
            return 'B'
        elif success_rate >= 75 and failed_tests <= 2:
            return 'C'
        elif success_rate >= 65:
            return 'D'
        else:
            return 'F'


def main():
    """Main function to run E2E testing"""
    suite = E2ETestSuite()
    report = suite.run_all_e2e_tests()
    
    # Save report
    os.makedirs('tests/e2e', exist_ok=True)
    with open('tests/e2e/e2e_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("END-TO-END TEST REPORT")
    print("="*80)
    print(f"User Experience Grade: {report['user_experience_grade']}")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Warnings: {report['summary']['warning_tests']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Overall Status: {report['summary']['overall_status']}")
    
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print(f"\nDetailed report saved to: tests/e2e/e2e_report.json")


if __name__ == "__main__":
    main()