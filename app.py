from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from io import BytesIO
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'epub', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return 'No file provided', 400

    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Save the uploaded file temporarily
        file.save(filename)

        # Process the file with your ebook formatting logic
        formatted_file = process_ebook(filename)

        # Clean up the temporary file
        os.remove(filename)

        return send_file(formatted_file, as_attachment=True)

    return 'Invalid file format', 400

def process_ebook(file_path):
    file_extension = file_path.split('.')[-1].lower()

    if file_extension == 'epub':
        formatted_file = process_epub(file_path)
    elif file_extension == 'pdf':
        formatted_file = process_pdf(file_path)
    else:
        raise ValueError('Invalid file format')

    return formatted_file

def process_epub(file_path):
    book = epub.read_epub(file_path)
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')

        text_nodes = soup.find_all(text=True)
        for text_node in text_nodes:
            formatted_text = apply_formatting(text_node.string)
            text_node.replace_with(BeautifulSoup(formatted_text, 'html.parser'))

        item.set_content(str(soup).encode('utf-8'))

    formatted_file = os.path.join(os.getcwd(), f'formatted_{os.path.basename(file_path)}')
    epub.write_epub(formatted_file, book)
    return formatted_file

def process_pdf(file_path):
    output_pdf = PdfWriter()
    original_pdf = PdfReader(file_path)

    for page_num in range(len(original_pdf.pages)):
        original_page = original_pdf.pages[page_num]
        text = original_page.extract_text()

        # Create a new PDF with the formatted text
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)

        formatted_words = apply_formatting(text).split()
        x, y = 50, 750  # Starting coordinates

        for word in formatted_words:
            if "<b>" in word:
                word = word.replace("<b>", "")
                c.setFont("Helvetica-Bold", 12)
            else:
                c.setFont("Helvetica", 12)

            c.drawString(x, y, word)
            x += c.stringWidth(word, c._fontname, c._fontsize) + 5  # Add space between words

            # Move to the next line if necessary
            if x > 550:
                x = 50
                y -= 20

        c.showPage()
        c.save()
        packet.seek(0)

        # Merge the new PDF with the original one
        formatted_pdf = PdfReader(packet)
        original_page.merge_page(formatted_pdf.getPage(0))
        output_pdf.addPage(original_page)

    formatted_file = os.path.join(os.getcwd(), f'formatted_{os.path.basename(file_path)}')
    with open(formatted_file, "wb") as output_file:
        output_pdf.write(output_file)

    return formatted_file


def apply_formatting(text):
    def format_word(word):
        if len(word) > 3:
            return f'<b>{word[:2]}</b>{word[2:]}'
        else:
            return word

    formatted_words = [format_word(word) for word in text.split()]
    return ' '.join(formatted_words)

if __name__ == '__main__':
    app.run(debug=True)
