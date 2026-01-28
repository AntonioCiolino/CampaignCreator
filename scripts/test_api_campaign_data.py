#!/usr/bin/env python3
"""
Direct test of Campaign Crafter API to see what sections/display_toc actually look like.
Run this from CampaignCreator directory with: python scripts/test_api_campaign_data.py
"""

import requests
import os
import json
from dotenv import load_dotenv

# Load env from campaign_crafter_api
load_dotenv("campaign_crafter_api/.env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
USERNAME = os.getenv("CAMPAIGN_CRAFTER_USERNAME", "admin")
PASSWORD = os.getenv("CAMPAIGN_CRAFTER_PASSWORD", "changeme")

def main():
    print("=" * 60)
    print("Testing Campaign Crafter API - Raw Data Inspection")
    print("=" * 60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Username: {USERNAME}")
    
    # Step 1: Authenticate
    print("\n1. Authenticating...")
    try:
        auth_response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={"username": USERNAME, "password": PASSWORD},
            timeout=30
        )
        auth_response.raise_for_status()
        token = auth_response.json()["access_token"]
        print(f"   ✅ Got token: {token[:20]}...")
    except Exception as e:
        print(f"   ❌ Auth failed: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: List campaigns
    print("\n2. Listing campaigns...")
    try:
        campaigns_response = requests.get(
            f"{API_BASE_URL}/api/v1/campaigns/",
            headers=headers,
            timeout=30
        )
        campaigns_response.raise_for_status()
        campaigns = campaigns_response.json()
        print(f"   Found {len(campaigns)} campaigns")
        
        if not campaigns:
            print("   No campaigns found. Create one first.")
            return
        
        # Show available campaigns
        for c in campaigns[:5]:
            print(f"   - ID: {c.get('id')}, Title: {c.get('title')}")
    except Exception as e:
        print(f"   ❌ List failed: {e}")
        return
    
    # Step 3: Use campaign 39 which has a TOC
    campaign_id = 52
    
    print(f"\n3. Getting campaign {campaign_id} details...")
    try:
        campaign_response = requests.get(
            f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}/",
            headers=headers,
            timeout=30
        )
        campaign_response.raise_for_status()
        campaign = campaign_response.json()
        
        print(f"\n   Campaign title: {campaign.get('title')}")
        print(f"\n   === RAW JSON RESPONSE ===")
        print(json.dumps(campaign, indent=2, default=str)[:2000])
        
        # Inspect sections
        print(f"\n   === SECTIONS ANALYSIS ===")
        sections = campaign.get("sections")
        print(f"   sections type: {type(sections)}")
        print(f"   sections value: {sections}")
        
        if sections is None:
            print("   ⚠️  sections is None!")
        elif isinstance(sections, str):
            print(f"   ❌ sections is a STRING (length {len(sections)})")
            print(f"   First 200 chars: {sections[:200]}")
        elif isinstance(sections, list):
            print(f"   ✅ sections is a LIST with {len(sections)} items")
            if sections:
                print(f"   First item type: {type(sections[0])}")
                print(f"   First item: {sections[0]}")
        
        # Inspect display_toc
        print(f"\n   === DISPLAY_TOC ANALYSIS ===")
        display_toc = campaign.get("display_toc")
        print(f"   display_toc type: {type(display_toc)}")
        print(f"   display_toc value: {display_toc}")
        
        if display_toc is None:
            print("   ⚠️  display_toc is None!")
        elif isinstance(display_toc, str):
            print(f"   ❌ display_toc is a STRING (length {len(display_toc)})")
            print(f"   First 200 chars: {display_toc[:200]}")
        elif isinstance(display_toc, list):
            print(f"   ✅ display_toc is a LIST with {len(display_toc)} items")
            if display_toc:
                print(f"   First item: {display_toc[0]}")
        
    except Exception as e:
        print(f"   ❌ Get campaign failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("Test complete - check the output above for data types")
    print("=" * 60)

if __name__ == "__main__":
    main()
