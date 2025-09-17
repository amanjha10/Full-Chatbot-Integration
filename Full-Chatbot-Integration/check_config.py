#!/usr/bin/env python3
"""
Configuration Checker for Full Chatbot Integration
Checks all configuration files for localhost URLs and environment-specific settings
"""

import os
import re
import json
from pathlib import Path

class ConfigChecker:
    def __init__(self):
        self.issues = []
        self.localhost_patterns = [
            r'localhost:\d+',
            r'127\.0\.0\.1:\d+',
            r'http://localhost',
            r'ws://localhost',
            r'https://localhost'
        ]
        
    def check_file(self, file_path, description=""):
        """Check a single file for localhost references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            issues_found = []
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in self.localhost_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        issues_found.append({
                            'line': i,
                            'content': line.strip(),
                            'matches': matches
                        })
            
            if issues_found:
                self.issues.append({
                    'file': str(file_path),
                    'description': description,
                    'issues': issues_found
                })
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    def check_all_files(self):
        """Check all relevant configuration files"""
        base_dir = Path(__file__).parent
        
        # Django files
        django_dir = base_dir / "ChatBot_DRF_Api"
        self.check_file(django_dir / "auth_system" / "settings.py", "Django Settings")
        self.check_file(django_dir / "static" / "chatbot-iframe.html", "Chatbot Iframe")
        self.check_file(django_dir / "static" / "chatbot.js", "Chatbot Widget Script")
        
        # React files
        react_dir = base_dir / "Chat-bot-react-main"
        self.check_file(react_dir / "src" / "config" / "axiosConfig.ts", "React Axios Config")
        self.check_file(react_dir / "vite.config.ts", "Vite Config")
        
        # Environment files
        env_files = [
            django_dir / ".env.example",
            django_dir / ".env.development", 
            django_dir / ".env.production",
            react_dir / ".env.example",
            react_dir / ".env.development",
            react_dir / ".env.production"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                self.check_file(env_file, f"Environment file: {env_file.name}")
    
    def generate_report(self):
        """Generate a detailed report of all issues found"""
        print("🔍 Configuration Check Report")
        print("=" * 50)
        
        if not self.issues:
            print("✅ No localhost references found in configuration files!")
            print("✅ All files appear to be production-ready!")
            return
        
        print(f"⚠️  Found {len(self.issues)} files with localhost references:")
        print()
        
        for issue in self.issues:
            print(f"📁 File: {issue['file']}")
            if issue['description']:
                print(f"   Description: {issue['description']}")
            print(f"   Issues found: {len(issue['issues'])}")
            
            for file_issue in issue['issues']:
                print(f"   Line {file_issue['line']}: {file_issue['content']}")
                print(f"   Matches: {', '.join(file_issue['matches'])}")
            print()
    
    def check_environment_files(self):
        """Check if all required environment files exist"""
        print("\n🌍 Environment Files Check")
        print("-" * 30)
        
        base_dir = Path(__file__).parent
        django_dir = base_dir / "ChatBot_DRF_Api"
        react_dir = base_dir / "Chat-bot-react-main"
        
        required_files = [
            (django_dir / ".env.example", "Django environment example"),
            (django_dir / ".env.development", "Django development config"),
            (django_dir / ".env.production", "Django production config"),
            (react_dir / ".env.example", "React environment example"),
            (react_dir / ".env.development", "React development config"),
            (react_dir / ".env.production", "React production config"),
        ]
        
        for file_path, description in required_files:
            if file_path.exists():
                print(f"✅ {description}: {file_path.name}")
            else:
                print(f"❌ Missing {description}: {file_path}")
    
    def check_build_files(self):
        """Check if React build files exist"""
        print("\n🏗️  Build Files Check")
        print("-" * 20)
        
        base_dir = Path(__file__).parent
        react_dir = base_dir / "Chat-bot-react-main"
        dist_dir = react_dir / "dist"
        
        if dist_dir.exists():
            files = list(dist_dir.rglob("*"))
            print(f"✅ React build directory exists with {len(files)} files")
            
            # Check for key files
            key_files = ["index.html", "assets"]
            for key_file in key_files:
                if (dist_dir / key_file).exists():
                    print(f"✅ Found {key_file}")
                else:
                    print(f"❌ Missing {key_file}")
        else:
            print("❌ React build directory (dist/) not found")
            print("   Run 'npm run build' in Chat-bot-react-main directory")

def main():
    checker = ConfigChecker()
    
    print("🚀 Full Chatbot Integration - Configuration Checker")
    print("=" * 55)
    
    # Check for localhost references
    checker.check_all_files()
    checker.generate_report()
    
    # Check environment files
    checker.check_environment_files()
    
    # Check build files
    checker.check_build_files()
    
    print("\n📋 Production Readiness Summary")
    print("-" * 35)
    
    if not checker.issues:
        print("✅ Configuration files are production-ready")
    else:
        print("⚠️  Some files still contain localhost references")
        print("   Review the issues above before deployment")
    
    print("\n🔧 Next Steps for Production Deployment:")
    print("1. Review and fix any localhost references found above")
    print("2. Ensure all environment files are properly configured")
    print("3. Make sure React build files are generated (npm run build)")
    print("4. Update DNS settings to point bot.spell.com.np to 157.180.118.12")
    print("5. Run the deployment script: sudo bash deploy.sh")
    print("6. Configure SSL certificates for HTTPS")

if __name__ == "__main__":
    main()
