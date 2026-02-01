import re
import tempfile
import os
from rapidfuzz import fuzz, process
import numpy as np

# Make whisper optional for testing
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: Whisper not installed. Audio transcription disabled. Text input will still work.")

class VoiceProcessor:
    def __init__(self, db_manager, usn_prefix=""):
        self.db_manager = db_manager
        self.whisper_model = None
        self.usn_prefix = usn_prefix  # Store USN prefix
    
    def load_whisper_model(self):
        """Lazy load Whisper model when needed"""
        if not WHISPER_AVAILABLE:
            return None
            
        if self.whisper_model is None:
            # Use base model for balance of speed and accuracy
            self.whisper_model = whisper.load_model("base")
        return self.whisper_model
    
    def transcribe_audio_bytes(self, audio_bytes):
        """Transcribe audio from bytes (for live recording)"""
        if not WHISPER_AVAILABLE:
            return None
            
        try:
            import soundfile as sf
            import io
            
            # Convert bytes to temporary WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            # Load model and transcribe
            model = self.load_whisper_model()
            if model is None:
                return None
                
            result = model.transcribe(tmp_path)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return result['text']
        
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio file to text using Whisper"""
        if not WHISPER_AVAILABLE:
            return None
            
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_path = tmp_file.name
            
            # Load model and transcribe
            model = self.load_whisper_model()
            if model is None:
                return None
                
            result = model.transcribe(tmp_path)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return result['text']
        
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return None
    
    def process_audio_file(self, audio_file, command_type, date=None, ia_type=None):
        """Process uploaded audio file"""
        # Transcribe audio
        transcribed_text = self.transcribe_audio(audio_file)
        
        if transcribed_text is None:
            return {'success': False, 'message': 'Failed to transcribe audio'}
        
        # Process the transcribed text
        return self.process_text_command(transcribed_text, command_type, date, ia_type)
    
    def process_text_command(self, text, command_type, date=None, ia_type=None):
        """Process voice command text"""
        if command_type == 'attendance':
            return self.process_attendance_command(text, date)
        elif command_type == 'marks':
            return self.process_marks_command(text, ia_type)
        else:
            return {'success': False, 'message': 'Invalid command type'}
    
    def process_attendance_command(self, text, date):
        """Process attendance voice command"""
        # Normalize text
        text = text.lower().strip()
        
        # Extract identifier (USN or Name)
        identifier = self.extract_identifier(text)
        
        if not identifier:
            return {'success': False, 'message': 'Could not identify student from command'}
        
        # Extract status
        status = self.extract_attendance_status(text)
        
        if not status:
            return {'success': False, 'message': 'Could not determine attendance status (Present/Absent)'}
        
        # Find student in database
        student = self.db_manager.fuzzy_find_student(identifier)
        
        if not student:
            return {'success': False, 'message': f'Student "{identifier}" not found in database'}
        
        student_id, usn, name = student
        
        # Record attendance
        success, message = self.db_manager.record_attendance(student_id, date, status)
        
        if success:
            return {
                'success': True, 
                'message': f'{name} ({usn}) marked {status} for {date}'
            }
        else:
            return {'success': False, 'message': message}
    
    def process_marks_command(self, text, ia_type):
        """Process IA marks voice command"""
        # Normalize text
        text = text.lower().strip()
        
        # Extract identifier
        identifier = self.extract_identifier(text)
        
        if not identifier:
            return {'success': False, 'message': 'Could not identify student from command'}
        
        # Find student
        student = self.db_manager.fuzzy_find_student(identifier)
        
        if not student:
            return {'success': False, 'message': f'Student "{identifier}" not found in database'}
        
        student_id, usn, name = student
        
        # Extract marks
        marks_dict = self.extract_marks(text)
        
        if not marks_dict:
            return {'success': False, 'message': 'Could not extract marks from command'}
        
        # Calculate total
        total = sum(marks_dict.values())
        
        if total > 40:
            return {'success': False, 'message': f'Total marks ({total}) exceeds maximum (40)'}
        
        # Record marks
        success, message = self.db_manager.record_ia_marks(
            student_id, ia_type, marks_dict, total
        )
        
        if success:
            questions_str = ', '.join([f'Q{q}={m}' for q, m in sorted(marks_dict.items())])
            return {
                'success': True,
                'message': f'{name} ({usn}) - {ia_type}: {questions_str}, Total: {total}/40'
            }
        else:
            return {'success': False, 'message': message}
    
    def extract_identifier(self, text):
        """Extract student identifier (USN or Name) from text - IMPROVED with USN prefix support"""
        noise_words = ['i', 'scored', 'as', 'a', 'the', 'has', 'have', 'had']
        
        # Pattern 1: USN with optional prefix expansion
        # SMART PADDING: Handles both 2-digit (024) and 3-digit (106) USNs
        # "usn 24" → "1GA23CI024" if prefix is "1GA23CI0"
        # "usn 106" → "1GA23CI106" if prefix is "1GA23CI"
        usn_pattern = r'usn\s+(\w+)'
        match = re.search(usn_pattern, text, re.IGNORECASE)
        if match:
            usn_part = match.group(1)
            # If it's just 2-3 digits, prepend the prefix
            if usn_part.isdigit() and len(usn_part) <= 3 and self.usn_prefix:
                full_usn = self._expand_usn(usn_part)
                print(f"🔧 Expanded USN: {usn_part} → {full_usn}")
                return full_usn
            return usn_part
        
        # Pattern 1.5: Just digits at start (common in voice: "24 is present")
        # Only if we have a prefix set
        if self.usn_prefix:
            digit_pattern = r'^(\d{2,3})\s+(is|has|scored)'
            match = re.search(digit_pattern, text, re.IGNORECASE)
            if match:
                digits = match.group(1)
                full_usn = self._expand_usn(digits)
                print(f"🔧 Expanded short USN: {digits} → {full_usn}")
                return full_usn
        
        # Pattern 2: Name before status word (for attendance)
        # "aloha is present" or "bob johnson is absent"
        status_pattern = r'^([\w\s]+?)\s+is\s+(present|absent)'
        match = re.search(status_pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean noise words
            name_parts = [w for w in name.split() if w.lower() not in noise_words]
            return ' '.join(name_parts) if name_parts else name
        
        # Pattern 3: For marks - extract name before "scored", "has", or "ia"
        # "aloha has scored" → "aloha"
        # "aloha scored" → "aloha"
        marks_patterns = [
            r'^([\w\s]+?)\s+(?:has\s+)?scored',  # "aloha scored" or "aloha has scored"
            r'^([\w\s]+?)\s+has\s+',  # "aloha has"
            r'^([\w\s]+?)\s+ia[12]',  # "aloha ia1"
        ]
        
        for pattern in marks_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean noise words
                name_parts = [w for w in name.split() if w.lower() not in noise_words]
                return ' '.join(name_parts) if name_parts else name
        
        # Pattern 4: Extract first valid name-like word before keywords
        keywords = ['is', 'has', 'have', 'scored', 'marks', 'mark', 'ia1', 'ia2', 'question', 'i']
        words = text.split()
        
        # Take words before first keyword
        identifier_words = []
        for word in words:
            if word.lower() in keywords:
                break
            # Only keep words that are likely names (length > 1, not numbers)
            if word.lower() not in noise_words and len(word) > 1 and not word.isdigit():
                identifier_words.append(word)
        
        if identifier_words:
            return ' '.join(identifier_words)
        
        return None
    
    def extract_attendance_status(self, text):
        """Extract attendance status from text"""
        if 'present' in text:
            return 'Present'
        elif 'absent' in text:
            return 'Absent'
        return None
    
    def extract_marks(self, text):
        """Extract question-wise marks from text"""
        marks_dict = {}
        
        # First, try to fix common transcription errors
        # "question 18" likely means "question 1, 8 marks"
        # "question 37" likely means "question 3, 7 marks"
        text = self.fix_transcription_errors(text)
        
        # Pattern 1: Various formats for question and marks
        patterns = [
            # "question 1, 8 marks" (comma separator - common in voice)
            r'question\s*(\d+)\s*,\s*(\d+)\s*marks?',
            # "question 1 8 marks" or "question 1 - 8 marks"
            r'question\s*(\d+)[\s\-–—]*(\d+)\s*mark',
            # "question 1 8" or "question 1-8"
            r'question\s*(\d+)[\s\-–—]+(\d+)(?!\d)',
            # "q1 8 marks" or "q1-8"
            r'q(\d+)[\s\-–—]+(\d+)\s*mark',
            r'q(\d+)[\s\-–—]+(\d+)(?!\d)',
            # "1 mark in question 1" or "8 marks in question 1"
            r'(\d+)\s*mark[s]?\s+in\s+question\s+(\d+)',
            # Natural: "scored 1 mark in question 1"
            r'scored[\s\w]*?(\d+)\s*mark[s]?\s+in\s+question\s+(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Handle different group orders
                g1, g2 = match.group(1), match.group(2)
                
                # Check if it's "marks in question N" format
                if 'mark' in pattern and 'question' in pattern and pattern.index('question') > pattern.index(r'(\d+)'):
                    # Marks first, then question number
                    marks = int(g1)
                    question_num = int(g2)
                else:
                    # Question number first, then marks
                    question_num = int(g1)
                    marks = int(g2)
                
                if 1 <= question_num <= 8 and 0 <= marks <= 10:
                    marks_dict[question_num] = marks
        
        # If still empty, try more flexible pattern
        if not marks_dict:
            # Look for any numbers followed by "question" followed by number
            flexible_pattern = r'(\d+)[\s\w]*?question\s*(\d+)'
            matches = re.finditer(flexible_pattern, text, re.IGNORECASE)
            for match in matches:
                marks = int(match.group(1))
                question_num = int(match.group(2))
                if 1 <= question_num <= 8 and 0 <= marks <= 10:
                    marks_dict[question_num] = marks
        
        return marks_dict
    
    def fix_transcription_errors(self, text):
        """Fix common transcription errors where Whisper mishears question numbers and marks"""
        # Pattern: "question 18" → "question 1, 8"
        # "question 37" → "question 3, 7"
        # This handles when Whisper hears "one eight" as "18"
        
        def replace_question_number(match):
            full_text = match.group(0)
            two_digit = match.group(1)
            
            # Split into individual digits
            digit1 = int(two_digit[0])  # First digit
            digit2 = int(two_digit[1])  # Second digit
            
            # Valid question numbers are 1-8, valid marks are 0-10
            if 1 <= digit1 <= 8 and 0 <= digit2 <= 10:
                # Likely "question 1, 8 marks"
                return f"question {digit1} {digit2} marks"
            
            return full_text
        
        # Replace "question 18 marks" → "question 1 8 marks"
        text = re.sub(r'question\s*(\d{2})\s*mark', replace_question_number, text, flags=re.IGNORECASE)
        
        # Also handle without "marks" word: "question 18" → "question 1 8"
        text = re.sub(r'question\s*(\d{2})(?!\d)', replace_question_number, text, flags=re.IGNORECASE)
        
        return text
    
    def _expand_usn(self, digits):
        """
        Smart USN expansion that handles mixed 2-digit and 3-digit USNs
        
        Examples:
        - Prefix "1GA23CI0", digits "24" → "1GA23CI024"
        - Prefix "1GA23CI", digits "24" → "1GA23CI24"
        - Prefix "1GA23CI0", digits "106" → "1GA23CI106" (removes trailing 0)
        - Prefix "1GA23CI", digits "106" → "1GA23CI106"
        """
        if not self.usn_prefix:
            return digits
        
        # If prefix ends with 0 and we have 3 digits (like 106)
        # Remove the trailing 0 from prefix
        if self.usn_prefix.endswith('0') and len(digits) == 3:
            # Remove trailing 0 for 3-digit USNs
            return self.usn_prefix[:-1] + digits
        else:
            # Just append for 2-digit USNs
            return self.usn_prefix + digits
    
    def text_to_number(self, text):
        """Convert text numbers to integers"""
        # Simple conversion for common numbers
        number_map = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
            'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
            'eighteen': 18, 'nineteen': 19, 'twenty': 20,
            'thirty': 30, 'forty': 40, 'fifty': 50
        }
        
        text = text.lower().strip()
        
        # Check if already a number
        if text.isdigit():
            return int(text)
        
        # Direct mapping
        if text in number_map:
            return number_map[text]
        
        # Handle compound numbers like "twenty three"
        words = text.split()
        if len(words) == 2:
            tens = number_map.get(words[0], 0)
            ones = number_map.get(words[1], 0)
            return tens + ones
        
        return None