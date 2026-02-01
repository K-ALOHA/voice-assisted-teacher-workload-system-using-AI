"""
Test script to verify Voice-Assisted Teacher Workload Management System
Run this before using the main application to ensure everything is working
"""

import sys
import sqlite3
import pandas as pd

def test_imports():
    """Test if all required packages are installed"""
    print("\n" + "="*50)
    print("Testing Package Imports...")
    print("="*50)
    
    required_packages = {
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'whisper': 'OpenAI Whisper',
        'rapidfuzz': 'RapidFuzz',
        'openpyxl': 'OpenPyXL',
        'plotly': 'Plotly'
    }
    
    failed = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name} - OK")
        except ImportError:
            print(f"✗ {name} - FAILED")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All packages imported successfully!")
        return True

def test_database_module():
    """Test database module functionality"""
    print("\n" + "="*50)
    print("Testing Database Module...")
    print("="*50)
    
    try:
        from database import DatabaseManager
        
        # Create test database
        db = DatabaseManager("test_db.db")
        print("✓ Database initialization - OK")
        
        # Test student loading
        test_students = pd.DataFrame({
            'USN': ['TEST001', 'TEST002'],
            'Name': ['Test Student 1', 'Test Student 2']
        })
        
        success, message = db.load_students_from_csv(test_students)
        if success:
            print("✓ Student loading - OK")
        else:
            print(f"✗ Student loading - FAILED: {message}")
            return False
        
        # Test student retrieval
        student = db.fuzzy_find_student('TEST001')
        if student:
            print("✓ Student search - OK")
        else:
            print("✗ Student search - FAILED")
            return False
        
        # Test attendance recording
        success, message = db.record_attendance(student[0], '2024-01-01', 'Present')
        if success:
            print("✓ Attendance recording - OK")
        else:
            print(f"✗ Attendance recording - FAILED: {message}")
            return False
        
        # Test marks recording
        marks_dict = {1: 8, 3: 7, 6: 9, 8: 8}
        success, message = db.record_ia_marks(student[0], 'IA1', marks_dict, 32)
        if success:
            print("✓ Marks recording - OK")
        else:
            print(f"✗ Marks recording - FAILED: {message}")
            return False
        
        # Test export
        excel_buffer = db.export_to_excel("Complete Report")
        if excel_buffer:
            print("✓ Excel export - OK")
        else:
            print("✗ Excel export - FAILED")
            return False
        
        # Cleanup
        import os
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")
        
        print("\n✅ Database module tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database module test failed: {str(e)}")
        return False

def test_voice_processor():
    """Test voice processor module"""
    print("\n" + "="*50)
    print("Testing Voice Processor Module...")
    print("="*50)
    
    try:
        from voice_processor import VoiceProcessor
        from database import DatabaseManager
        
        # Create test database
        db = DatabaseManager("test_db.db")
        test_students = pd.DataFrame({
            'USN': ['24CS001'],
            'Name': ['Aloha Smith']
        })
        db.load_students_from_csv(test_students)
        
        vp = VoiceProcessor(db)
        print("✓ Voice processor initialization - OK")
        
        # Test attendance command
        result = vp.process_text_command(
            "Aloha is present", 
            'attendance', 
            '2024-01-01'
        )
        if result['success']:
            print("✓ Attendance command processing - OK")
        else:
            print(f"✗ Attendance command - FAILED: {result['message']}")
            return False
        
        # Test marks command
        result = vp.process_text_command(
            "Aloha IA1: Q1-8, Q3-7, Q6-9, Q8-8",
            'marks',
            ia_type='IA1'
        )
        if result['success']:
            print("✓ Marks command processing - OK")
        else:
            print(f"✗ Marks command - FAILED: {result['message']}")
            return False
        
        # Test fuzzy matching
        result = vp.process_text_command(
            "Aloka is present",  # Mispronounced
            'attendance',
            '2024-01-02'
        )
        if result['success']:
            print("✓ Fuzzy matching - OK")
        else:
            print(f"✗ Fuzzy matching - FAILED: {result['message']}")
        
        # Cleanup
        import os
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")
        
        print("\n✅ Voice processor tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Voice processor test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_analytics():
    """Test analytics module"""
    print("\n" + "="*50)
    print("Testing Analytics Module...")
    print("="*50)
    
    try:
        from analytics import AnalyticsDashboard
        from database import DatabaseManager
        
        db = DatabaseManager("test_db.db")
        analytics = AnalyticsDashboard(db)
        print("✓ Analytics initialization - OK")
        
        # Cleanup
        import os
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")
        
        print("\n✅ Analytics module tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Analytics module test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" VOICE-ASSISTED TEACHER WORKLOAD MANAGEMENT SYSTEM")
    print(" System Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Package Imports", test_imports()))
    results.append(("Database Module", test_database_module()))
    results.append(("Voice Processor", test_voice_processor()))
    results.append(("Analytics Module", test_analytics()))
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print(" ✅ ALL TESTS PASSED!")
        print(" System is ready to use. Run: streamlit run app.py")
    else:
        print(" ❌ SOME TESTS FAILED")
        print(" Please fix the issues before running the application")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
