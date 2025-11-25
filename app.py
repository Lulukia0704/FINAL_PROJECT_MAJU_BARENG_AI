from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import time
import json
from werkzeug.utils import secure_filename
import pdfplumber
from pypdf import PdfReader

app = Flask(__name__)
CORS(app)

# Konfigurasi folder upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
CONFIG_FILE = 'config.json'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Max 50MB

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_api_key():
    """Load API Key dari config.json"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('api_key', '')
    except Exception as e:
        print(f"Error loading config: {e}")
    return ''

def save_api_key(api_key):
    """Save API Key ke config.json"""
    try:
        config = {'api_key': api_key}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def extract_text_from_pdf(file_path):
    """Extract text dari PDF file dengan multiple methods"""
    text = ""
    
    try:
        print(f"[PDF] Trying pdfplumber untuk: {os.path.basename(file_path)}")
        # Method 1: Gunakan pdfplumber (lebih reliable)
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Halaman {page_num + 1} ---\n{page_text}"
                else:
                    print(f"[PDF] Halaman {page_num + 1} kosong di pdfplumber, trying pypdf...")
        
        # Method 2: Fallback ke pypdf jika pdfplumber tidak dapat banyak text
        if len(text.strip()) < 100:
            print(f"[PDF] Text kurang dari 100 char, trying pypdf fallback...")
            with open(file_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Halaman {page_num + 1} ---\n{page_text}"
        
        if not text.strip():
            raise Exception("Tidak bisa extract text dari PDF - kemungkinan file corrupted atau image-based PDF")
        
        print(f"[PDF] Success! Extracted {len(text)} chars")
        return text
        
    except Exception as e:
        error_msg = f"Error extracting PDF: {str(e)}"
        print(f"[PDF] {error_msg}")
        raise Exception(error_msg)

def configure_gemini(api_key):
    """Configure Gemini dengan API Key"""
    genai.configure(api_key=api_key)

def call_gemini(api_key, prompt, max_retries=3, retry_delay=5):
    """Panggil Gemini API dengan prompt dan retry mechanism"""
    try:
        configure_gemini(api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        for attempt in range(max_retries):
            try:
                print(f"[Gemini] Calling API... (Attempt {attempt + 1}/{max_retries})")
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.5,
                        top_k=30,
                        top_p=0.9,
                        max_output_tokens=2000,
                    )
                )
                print(f"[Gemini] Response received: {len(response.text)} chars")
                return response.text
            except Exception as e:
                error_str = str(e)
                print(f"[Gemini] Error: {error_str}")
                if '429' in error_str or 'exhausted' in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"[Gemini] Rate limit hit. Retrying dalam {wait_time} detik...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"API Rate limit exceeded. Coba lagi nanti.")
                else:
                    raise e
    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini] Final Error: {error_msg}")
        raise Exception(f"Error calling Gemini: {error_msg}")

# ============== ROUTES ==============

@app.route('/api/config/get-api-key', methods=['GET'])
def get_api_key():
    """Get API Key status (hanya check apakah sudah ada)"""
    api_key = load_api_key()
    is_set = bool(api_key)
    return jsonify({'is_set': is_set}), 200

@app.route('/api/config/set-api-key', methods=['POST'])
def set_api_key():
    """Set API Key ke config.json"""
    try:
        data = request.json
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API Key tidak boleh kosong'}), 400
        
        # Test API Key
        try:
            configure_gemini(api_key)
            genai.list_models()
        except Exception as e:
            return jsonify({'error': f'API Key tidak valid: {str(e)}'}), 400
        
        if save_api_key(api_key):
            return jsonify({'message': 'API Key berhasil disimpan'}), 200
        else:
            return jsonify({'error': 'Gagal menyimpan API Key'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/synthesis/upload', methods=['POST'])
def upload_pdf_synthesis():
    """Upload PDF untuk sintesis"""
    try:
        api_key = load_api_key()
        if not api_key:
            return jsonify({'error': 'API Key belum dikonfigurasi. Setup dulu di menu Settings'}), 400
        
        if 'files' not in request.files:
            return jsonify({'error': 'Tidak ada file yang diupload'}), 400
        
        files = request.files.getlist('files')
        print(f"\n[Synthesis] Total files received: {len(files)}")
        
        if len(files) == 0:
            return jsonify({'error': 'Pilih minimal 1 PDF'}), 400
        
        if len(files) > 5:
            return jsonify({'error': 'Maksimal 5 PDF sekaligus'}), 400
        
        all_texts = []
        file_count = 0
        
        for idx, file in enumerate(files):
            try:
                if file.filename == '':
                    print(f"[Synthesis] File {idx} kosong, skip")
                    continue
                
                if not allowed_file(file.filename):
                    return jsonify({'error': f'File {file.filename} harus PDF'}), 400
                
                # Save file
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"[Synthesis] Saving file {idx+1}: {filename}")
                file.save(filepath)
                
                # Extract text
                print(f"[Synthesis] Extracting text from {filename}...")
                text = extract_text_from_pdf(filepath)
                
                if text.strip():
                    all_texts.append(f"=== {filename} ===\n{text}")
                    file_count += 1
                    print(f"[Synthesis] ✓ File {idx+1} processed: {len(text)} chars")
                else:
                    print(f"[Synthesis] ⚠ File {idx+1} tidak ada text, skip")
                
                # Clean up
                try:
                    os.remove(filepath)
                    print(f"[Synthesis] Cleaned up: {filename}")
                except:
                    pass
                    
            except Exception as e:
                print(f"[Synthesis] Error processing file {idx+1}: {str(e)}")
                # Continue dengan file berikutnya, jangan stop
                continue
        
        if not all_texts:
            return jsonify({'error': 'Tidak ada text yang bisa diextract dari PDF. Cek apakah PDF text-based (bukan image)'}), 400
        
        # Combine all texts
        combined_text = "\n\n".join(all_texts)
        print(f"[Synthesis] Total processed: {file_count} files, {len(combined_text)} chars")
        
        # Generate synthesis
        prompt = f"""Sebagai ahli penelitian akademis, analisis jurnal-jurnal PDF berikut dan berikan ringkasan terstruktur:

{combined_text}

BERIKAN RINGKASAN DALAM FORMAT INI (GUNAKAN BAHASA INDONESIA):

## 1. TEMUAN UTAMA SETIAP JURNAL
Untuk setiap jurnal, sebutkan:
- Poin temuan utama 1
- Poin temuan utama 2
- Poin temuan utama 3

## 2. KESAMAAN DAN PERBEDAAN ANTAR JURNAL
- Kesamaan tema/topik
- Kesamaan metodologi
- Perbedaan utama
- Perbedaan fokus penelitian

## 3. RESEARCH GAP (KESENJANGAN PENELITIAN)
Identifikasi minimal 3 gap/celah dalam penelitian:
- Gap 1: [penjelasan]
- Gap 2: [penjelasan]
- Gap 3: [penjelasan]

## 4. REKOMENDASI PENELITIAN LANJUTAN
Saran arah penelitian:
- Rekomendasi 1
- Rekomendasi 2
- Rekomendasi 3

Gunakan bahasa Indonesia formal dan akademis. Berikan output yang jelas dan terstruktur."""

        print("[Synthesis] Calling Gemini API untuk generate synthesis...")
        result = call_gemini(api_key, prompt)
        print(f"[Synthesis] ✓ Result received: {len(result)} chars")
        
        return jsonify({
            'result': result, 
            'status': 'success',
            'files_processed': file_count
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Synthesis] ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 500

@app.route('/api/paraphrase', methods=['POST'])
def paraphrase():
    """Endpoint untuk parafrase dan perubahan gaya"""
    try:
        api_key = load_api_key()
        if not api_key:
            return jsonify({'error': 'API Key belum dikonfigurasi'}), 400
        
        data = request.json
        text = data.get('text')
        style_format = data.get('style_format', 'paraphrase')
        citation_style = data.get('citation_style', 'APA')

        if not text:
            return jsonify({'error': 'Teks harus diisi'}), 400

        if style_format == 'paraphrase':
            prompt = f"""Parafrase teks berikut dengan mempertahankan makna asli tetapi menggunakan kata-kata dan struktur kalimat yang berbeda:

"{text}"

Pastikan parafrase tetap akurat dan mudah dipahami."""

        elif style_format == 'formal':
            prompt = f"""Ubah teks berikut menjadi gaya penulisan formal akademis:

"{text}"

Tingkatkan formalitas, presisi, dan kejelasan tanpa mengubah makna inti."""

        elif style_format == 'citation':
            prompt = f"""Format dan jelaskan bagaimana teks berikut seharusnya dikutip dalam gaya {citation_style}:

"{text}"

Berikan:
1. Contoh kutipan langsung dalam format {citation_style}
2. Contoh parafrase dengan sitasi dalam format {citation_style}
3. Format entri dalam daftar pustaka {citation_style}"""

        result = call_gemini(api_key, prompt)
        return jsonify({'result': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quote-check', methods=['POST'])
def quote_check():
    """Endpoint untuk verifikasi kutipan"""
    try:
        api_key = load_api_key()
        if not api_key:
            return jsonify({'error': 'API Key belum dikonfigurasi'}), 400
        
        data = request.json
        quote = data.get('quote')
        source = data.get('source')

        if not quote or not source:
            return jsonify({'error': 'Kutipan dan sumber harus diisi'}), 400

        prompt = f"""Sebagai verifikator sitasi akademis, periksa kutipan berikut:

KUTIPAN: "{quote}"
SUMBER: {source}

Berikan analisis:
1. Akurasi: ✓ Akurat / ⚠ Perlu Verifikasi / ✗ Tidak Akurat
2. Kredibilitas sumber
3. Konteks penggunaan
4. Saran perbaikan (jika ada)"""

        result = call_gemini(api_key, prompt)
        return jsonify({'result': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    api_key = load_api_key()
    return jsonify({
        'status': 'ok',
        'api_key_configured': bool(api_key)
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)