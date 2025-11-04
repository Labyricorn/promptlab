#!/usr/bin/env python3
"""
Demo script to test the import/export functionality
"""

import json
import requests
import time

# Configuration
BASE_URL = "http://127.0.0.1:5000/api"

def test_import_export():
    """Test the import/export functionality"""
    print("Testing PromptLab Import/Export Functionality")
    print("=" * 50)
    
    # Create a test prompt
    test_prompt = {
        "name": "Demo Prompt",
        "description": "A demonstration prompt for testing import/export",
        "system_prompt": "You are a helpful assistant for demonstration purposes.",
        "model": "llama2",
        "temperature": 0.8
    }
    
    print("1. Creating test prompt...")
    try:
        response = requests.post(f"{BASE_URL}/prompts", json=test_prompt)
        if response.status_code == 201:
            print("✓ Test prompt created successfully")
            prompt_data = response.json()['prompt']
            print(f"  Created prompt ID: {prompt_data['id']}")
        else:
            print(f"✗ Failed to create prompt: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to PromptLab server. Make sure it's running on port 5000.")
        return
    
    # Export library
    print("\n2. Exporting library...")
    try:
        response = requests.post(f"{BASE_URL}/export-library", json={"format": "json"})
        if response.status_code == 200:
            print("✓ Library exported successfully")
            export_data = response.json()
            print(f"  Total prompts exported: {export_data['metadata']['total_prompts']}")
            exported_library = export_data['export_data']
        else:
            print(f"✗ Failed to export library: {response.text}")
            return
    except Exception as e:
        print(f"✗ Export failed: {e}")
        return
    
    # Delete the prompt
    print("\n3. Deleting test prompt...")
    try:
        response = requests.delete(f"{BASE_URL}/prompts/{prompt_data['id']}")
        if response.status_code == 200:
            print("✓ Test prompt deleted successfully")
        else:
            print(f"✗ Failed to delete prompt: {response.text}")
    except Exception as e:
        print(f"✗ Delete failed: {e}")
    
    # Import library back
    print("\n4. Importing library back...")
    try:
        import_request = {
            "import_data": exported_library,
            "conflict_resolution": "skip"
        }
        response = requests.post(f"{BASE_URL}/import-library", json=import_request)
        if response.status_code == 200:
            print("✓ Library imported successfully")
            import_result = response.json()
            print(f"  Imported: {import_result['summary']['imported']} prompts")
            print(f"  Skipped: {import_result['summary']['skipped']} prompts")
            print(f"  Errors: {import_result['summary']['errors']} prompts")
        else:
            print(f"✗ Failed to import library: {response.text}")
            return
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return
    
    # Verify the prompt was restored
    print("\n5. Verifying restored prompt...")
    try:
        response = requests.get(f"{BASE_URL}/prompts")
        if response.status_code == 200:
            prompts = response.json()['prompts']
            restored_prompt = next((p for p in prompts if p['name'] == 'Demo Prompt'), None)
            if restored_prompt:
                print("✓ Prompt successfully restored")
                print(f"  Name: {restored_prompt['name']}")
                print(f"  Description: {restored_prompt['description']}")
                print(f"  Model: {restored_prompt['model']}")
                print(f"  Temperature: {restored_prompt['temperature']}")
            else:
                print("✗ Prompt not found after import")
        else:
            print(f"✗ Failed to retrieve prompts: {response.text}")
    except Exception as e:
        print(f"✗ Verification failed: {e}")
    
    print("\n" + "=" * 50)
    print("Import/Export functionality test completed!")

if __name__ == "__main__":
    test_import_export()