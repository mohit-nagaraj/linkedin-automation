import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

from automation.config import load_settings, Settings
from automation.linkedin import LinkedInAutomation
from automation.gemini_client import GeminiClient
from automation.enhanced_gemini_client import EnhancedGeminiClient
from automation.scoring import compute_popularity_score
from automation.sheets import SheetsClient
from automation.enhanced_sheets import EnhancedSheetsClient
from automation.profile_extractor import ProfileExtractor

OWNER_BIO = (
    "Mohit Nagaraj is a Software Engineer at Final Round AI (Founding Engineer) and active member at Point Blank, "
    "with 6 hackathon wins including the Grand Prize (₹1.25 Lakh) at Innerve 9.0, India's largest student-driven "
    "hackathon, competing against 1,250 teams. Currently pursuing B.E. in Computer Science at Dayananda Sagar "
    "College of Engineering, Bangalore (CGPA 9.2, graduating 2026).\n\n"
    
    "At Final Round AI, he architects event-driven chargeback automation systems using FastAPI microservices, "
    "integrating Stripe webhooks, Firebase, and LiteLLM for AI-powered dispute analysis with automated PDF "
    "evidence generation via Weasyprint and S3 storage. He builds asynchronous workflow orchestration with "
    "APScheduler for email polling (IMAP/SMTP), real-time Slack notifications, and maintains 85%+ test coverage.\n\n"
    
    "Technical expertise spans Python backends, React Native apps, Go microservices, Kubernetes deployments, "
    "Docker containers, and cloud infrastructure (AWS Certified Cloud Practitioner). Notable projects include "
    "VidStreamX (scalable video transcoding pipeline with AWS S3/SQS), TrendAI (AI-powered social media analytics), "
    "and Synapse (AI-driven EdTech platform that won Innerve 9).\n\n"
    
    "Professional experience includes React Native Developer at Boho (expo framework, SDUI, tanstack queries, "
    "websockets), SDE intern at Springreen (microservices, CI/CD pipelines, EC2 instances), and DevOps intern "
    "at Finessefleet Foundation (Kubernetes, Prometheus/Grafana monitoring stack, infrastructure-as-code).\n\n"
    
    "Open source contributor to CNCF KubeVirt project, focusing on virtualization and Kubernetes CRDs. "
    "Skills include Next.js, Express.js, Full-Stack Development, Kubernetes, FastAPI, Go, Docker, AWS, "
    "Firebase, PostgreSQL, MongoDB, Redis, and comprehensive testing frameworks.\n\n"
    
    "Portfolio: mohitnagaraj.in | GitHub: github.com/mohit-nagaraj | Based in Bengaluru, Karnataka, India"
)


class LinkedInAutomationIntegration:
    def __init__(self, callbacks: Optional[Dict[str, Any]] = None):
        self.callbacks = callbacks or {}
        self.settings = None
        self.is_running = False
        self.li = None
        self.sheets = None
        self.enhanced_sheets = None
        self.gemini = None
        self.enhanced_gemini = None
        
    def update_progress(self, message: str, progress: float = 0, stats: Optional[Dict] = None):
        if "progress" in self.callbacks:
            self.callbacks["progress"](message, progress, stats)
    
    def log_message(self, message: str, level: str = "INFO"):
        if "log" in self.callbacks:
            self.callbacks["log"](message, level)
        else:
            logging.log(getattr(logging, level, logging.INFO), message)
    
    def add_profile(self, profile_data: Dict):
        if "profile" in self.callbacks:
            self.callbacks["profile"](profile_data)
    
    async def initialize(self, custom_settings: Optional[Dict] = None):
        try:
            # Load settings
            self.settings = load_settings()
            
            # Override with custom settings if provided
            if custom_settings:
                for key, value in custom_settings.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
            
            # Initialize Google Sheets
            if self.settings.gsheet_name or self.settings.gsheet_id:
                self.log_message("Initializing Google Sheets client...", "INFO")
                
                try:
                    self.enhanced_sheets = EnhancedSheetsClient(
                        json_path=self.settings.gcp_service_account_json_path,
                        json_blob=self.settings.gcp_service_account_json,
                        spreadsheet_name=self.settings.gsheet_name,
                        worksheet_name=self.settings.gsheet_worksheet,
                        oauth_client_secrets_path=self.settings.oauth_client_secrets_path,
                        oauth_token_path=self.settings.oauth_token_path,
                        spreadsheet_id=self.settings.gsheet_id,
                    )
                    self.log_message("Enhanced Google Sheets client initialized", "INFO")
                except Exception as e:
                    self.log_message(f"Enhanced Sheets failed, using regular: {str(e)}", "WARNING")
                    self.sheets = SheetsClient(
                        json_path=self.settings.gcp_service_account_json_path,
                        json_blob=self.settings.gcp_service_account_json,
                        spreadsheet_name=self.settings.gsheet_name,
                        worksheet_name=self.settings.gsheet_worksheet,
                        oauth_client_secrets_path=self.settings.oauth_client_secrets_path,
                        oauth_token_path=self.settings.oauth_token_path,
                        spreadsheet_id=self.settings.gsheet_id,
                    )
                    self.log_message("Regular Google Sheets client initialized", "INFO")
            
            # Initialize Gemini clients
            self.gemini = GeminiClient(api_key=self.settings.google_api_key, model_name="gemini-2.5-flash-preview-05-20")
            try:
                self.enhanced_gemini = EnhancedGeminiClient(api_key=self.settings.google_api_key, model_name="gemini-2.0-flash-exp")
                self.log_message("Enhanced Gemini client initialized", "INFO")
            except Exception as e:
                self.log_message(f"Enhanced Gemini initialization failed: {str(e)}", "WARNING")
            
            return True
            
        except Exception as e:
            self.log_message(f"Initialization error: {str(e)}", "ERROR")
            return False
    
    async def run_automation(self, keywords: str, locations: List[str], max_profiles: int):
        if self.is_running:
            self.log_message("Automation already running", "WARNING")
            return
        
        self.is_running = True
        
        try:
            self.update_progress("Starting LinkedIn automation...", 0)
            
            # Create LinkedIn automation instance
            async with LinkedInAutomation(
                email=self.settings.linkedin_email,
                password=self.settings.linkedin_password,
                headless=self.settings.headless,
                slow_mo_ms=self.settings.slow_mo_ms,
                navigation_timeout_ms=self.settings.navigation_timeout_ms,
                storage_state_path=self.settings.storage_state_path,
                use_persistent_context=self.settings.use_persistent_context,
                user_data_dir=self.settings.user_data_dir,
                browser_channel=self.settings.browser_channel,
                debug=self.settings.debug,
                min_action_delay_ms=self.settings.min_action_delay_ms,
                max_action_delay_ms=self.settings.max_action_delay_ms,
                test_mode=self.settings.test_mode,
            ) as self.li:
                
                # Login
                self.update_progress("Logging into LinkedIn...", 0.1)
                self.log_message("Starting LinkedIn login", "INFO")
                await self.li.login()
                
                # Search for profiles
                self.update_progress("Searching for profiles...", 0.2)
                search_results = await self.li.search_people(
                    [keywords] if isinstance(keywords, str) else keywords,
                    locations,
                    max_results=max_profiles
                )
                
                self.log_message(f"Found {len(search_results)} profiles", "INFO")
                self.update_progress(f"Found {len(search_results)} profiles", 0.3, {
                    "profiles_found": len(search_results)
                })
                
                # Initialize profile extractor
                profile_extractor = ProfileExtractor(self.li.page, debug=self.settings.debug)
                
                # Process profiles
                processed_count = 0
                connections_sent = 0
                already_connected = 0
                
                for idx, result in enumerate(search_results):
                    if not self.is_running:
                        self.log_message("Automation stopped by user", "WARNING")
                        break
                    
                    progress = 0.3 + (0.6 * (idx / len(search_results)))
                    self.update_progress(
                        f"Processing profile {idx + 1}/{len(search_results)}: {result.name}",
                        progress,
                        {
                            "profiles_found": len(search_results),
                            "profiles_processed": processed_count,
                            "connections_sent": connections_sent,
                            "already_connected": already_connected
                        }
                    )
                    
                    try:
                        # Extract detailed profile
                        if self.enhanced_sheets and self.enhanced_gemini:
                            detailed_profile = await profile_extractor.extract_profile(result.profile_url)
                            
                            # Generate AI content
                            inmail_note = await self.enhanced_gemini.generate_inmail_note(detailed_profile, OWNER_BIO)
                            detailed_profile.inmail_note = inmail_note
                            
                            ice_breakers = await self.enhanced_gemini.generate_ice_breakers(detailed_profile, count=3)
                            detailed_profile.ice_breakers = ice_breakers
                            
                            ai_summary = await self.enhanced_gemini.summarize_profile(detailed_profile, OWNER_BIO)
                            
                            popularity = compute_popularity_score(detailed_profile, self.settings.seniority_keywords)
                            
                            # Add to sheets
                            row_num = self.enhanced_sheets.add_profile(
                                detailed_profile,
                                ai_summary=ai_summary,
                                popularity_score=popularity
                            )
                            
                            # Add to UI
                            self.add_profile({
                                "name": detailed_profile.name,
                                "position": detailed_profile.headline.split(" at ")[0] if " at " in detailed_profile.headline else detailed_profile.headline,
                                "location": detailed_profile.location,
                                "status": "Processed",
                                "score": popularity,
                                "connected": "Pending",
                                "profile_url": result.profile_url,
                                "about": detailed_profile.about,
                                "skills": ", ".join(detailed_profile.skills[:5]) if detailed_profile.skills else "",
                                "ice_breakers": ice_breakers
                            })
                            
                            # Try to connect
                            if result.connection_status != "connected":
                                try:
                                    connect_sent = await self.li.connect_with_note(result.profile_url, inmail_note)
                                    if connect_sent:
                                        connections_sent += 1
                                        self.log_message(f"Connection sent to {detailed_profile.name}", "INFO")
                                        if self.enhanced_sheets:
                                            self.enhanced_sheets.mark_connect_sent(row_num)
                                except Exception as e:
                                    self.log_message(f"Connection failed for {detailed_profile.name}: {str(e)}", "WARNING")
                            else:
                                already_connected += 1
                                if self.enhanced_sheets:
                                    self.enhanced_sheets.mark_connection_accepted(row_num)
                        
                        else:
                            # Regular profile processing
                            profile = await self.li.scrape_profile(result.profile_url)
                            popularity = compute_popularity_score(profile, self.settings.seniority_keywords)
                            
                            # Generate AI content
                            summary = await self.gemini.summarize_profile(profile, OWNER_BIO)
                            note = await self.gemini.craft_connect_note(profile, OWNER_BIO)
                            
                            # Add to UI
                            self.add_profile({
                                "name": profile.name,
                                "position": profile.headline.split(" at ")[0] if " at " in profile.headline else profile.headline,
                                "location": profile.location,
                                "status": "Processed",
                                "score": popularity,
                                "connected": "Pending",
                                "profile_url": result.profile_url,
                                "about": profile.about,
                                "skills": ", ".join(profile.skills[:5]) if profile.skills else "",
                                "summary": summary
                            })
                            
                            # Try to connect
                            if result.connection_status != "connected":
                                try:
                                    connect_sent = await self.li.connect_with_note(result.profile_url, note)
                                    if connect_sent:
                                        connections_sent += 1
                                        self.log_message(f"Connection sent to {profile.name}", "INFO")
                                except Exception as e:
                                    self.log_message(f"Connection failed for {profile.name}: {str(e)}", "WARNING")
                            else:
                                already_connected += 1
                        
                        processed_count += 1
                        
                    except Exception as e:
                        self.log_message(f"Error processing profile {result.name}: {str(e)}", "ERROR")
                    
                    if processed_count >= max_profiles:
                        break
                
                # Final update
                self.update_progress(
                    "Automation completed successfully!",
                    1.0,
                    {
                        "profiles_found": len(search_results),
                        "profiles_processed": processed_count,
                        "connections_sent": connections_sent,
                        "already_connected": already_connected
                    }
                )
                
                self.log_message(f"Automation completed: {processed_count} profiles processed, {connections_sent} connections sent", "INFO")
                
        except Exception as e:
            self.log_message(f"Automation error: {str(e)}", "ERROR")
            self.update_progress(f"Error: {str(e)}", 0)
        finally:
            self.is_running = False
    
    def stop(self):
        self.is_running = False
        self.log_message("Stopping automation...", "INFO")