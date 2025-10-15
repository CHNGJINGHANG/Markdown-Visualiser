import streamlit as st
import base64
from io import BytesIO
import markdown
from fpdf import FPDF
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
from matplotlib import mathtext
import tempfile
import os

# ---------- Streamlit App ----------
st.set_page_config(page_title="Markdown Visualizer", layout="wide")
st.title("📄 Markdown Visualizer with PDF Printing")

# Initialize session state
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'file_content' not in st.session_state:
    st.session_state.file_content = ""

# ---------- PDF Generation Class ----------
class MarkdownPDF(FPDF):
    def __init__(self, title="Document"):
        super().__init__()
        self.title_text = title
        
    def header(self):
        """Add header to each page"""
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, self.title_text, 0, 0, 'L')
        self.ln(15)
        
    def footer(self):
        """Add footer with page number"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
    def chapter_title(self, title, level=1):
        """Add chapter title"""
        if level == 1:
            self.set_font('Arial', 'B', 18)
            self.set_text_color(44, 62, 80)
            self.ln(5)
            self.multi_cell(0, 10, title)
            self.ln(2)
            # Add underline
            self.set_draw_color(52, 152, 219)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)
        elif level == 2:
            self.set_font('Arial', 'B', 14)
            self.set_text_color(52, 73, 94)
            self.ln(4)
            self.multi_cell(0, 8, title)
            self.ln(2)
            # Add underline
            self.set_draw_color(149, 165, 166)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        else:
            self.set_font('Arial', 'B', 12)
            self.set_text_color(52, 73, 94)
            self.ln(3)
            self.multi_cell(0, 7, title)
            self.ln(2)
            
    def chapter_body(self, body):
        """Add body text"""
        self.set_font('Arial', '', 11)
        self.set_text_color(51, 51, 51)
        
        # Handle bold and italic
        body = body.replace('<strong>', '')
        body = body.replace('</strong>', '')
        body = body.replace('<b>', '')
        body = body.replace('</b>', '')
        body = body.replace('<em>', '')
        body = body.replace('</em>', '')
        body = body.replace('<i>', '')
        body = body.replace('</i>', '')
        
        self.multi_cell(0, 6, body)
        self.ln(2)
        
    def add_code_block(self, code):
        """Add code block"""
        self.set_fill_color(248, 248, 248)
        self.set_font('Courier', '', 9)
        self.set_text_color(51, 51, 51)
        
        # Add border
        self.ln(2)
        x_start = self.get_x()
        y_start = self.get_y()
        
        # Draw left border
        self.set_draw_color(52, 152, 219)
        self.set_line_width(1)
        
        lines = code.split('\n')
        for line in lines:
            if self.get_y() > 270:  # Page break
                self.add_page()
            self.cell(0, 5, line, 0, 1, 'L', True)
        
        # Draw left blue line
        self.set_line_width(2)
        self.line(10, y_start, 10, self.get_y())
        self.ln(2)
        
    def add_list_item(self, text, ordered=False, number=1):
        """Add list item"""
        self.set_font('Arial', '', 11)
        self.set_text_color(51, 51, 51)
        
        bullet = f"{number}." if ordered else "•"
        self.cell(10, 6, bullet, 0, 0)
        self.multi_cell(0, 6, text)
        
    def add_blockquote(self, text):
        """Add blockquote"""
        self.set_fill_color(249, 249, 249)
        self.set_font('Arial', 'I', 11)
        self.set_text_color(127, 140, 141)
        
        self.ln(2)
        # Draw left border
        self.set_draw_color(189, 195, 199)
        self.set_line_width(1.5)
        y_start = self.get_y()
        
        self.multi_cell(0, 6, text, 0, 'L', True)
        
        # Draw left line
        self.line(10, y_start, 10, self.get_y())
        self.ln(2)

def create_pdf_from_markdown(markdown_content, filename="document"):
    """Create PDF from markdown content using FPDF"""
    
    try:
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content, 
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create PDF
        pdf = MarkdownPDF(title=filename)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Add title page
        pdf.set_font('Arial', 'B', 24)
        pdf.set_text_color(44, 62, 80)
        pdf.ln(40)
        pdf.cell(0, 15, filename, 0, 1, 'C')
        pdf.set_font('Arial', 'I', 12)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 10, 'Generated from Markdown', 0, 1, 'C')
        pdf.ln(10)
        pdf.set_draw_color(52, 152, 219)
        pdf.set_line_width(0.5)
        pdf.line(60, pdf.get_y(), 150, pdf.get_y())
        
        pdf.add_page()
        
        # Process content
        in_code_block = False
        code_content = []
        list_counter = 0
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'pre', 'code', 'ul', 'ol', 'li', 'blockquote']):
            try:
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    level = int(element.name[1])
                    text = element.get_text().strip()
                    if text:
                        pdf.chapter_title(text, level)
                        
                elif element.name == 'p':
                    text = element.get_text().strip()
                    if text and not element.find_parent('li'):
                        pdf.chapter_body(text)
                        
                elif element.name == 'pre':
                    code_text = element.get_text().strip()
                    if code_text:
                        pdf.add_code_block(code_text)
                        
                elif element.name == 'blockquote':
                    quote_text = element.get_text().strip()
                    if quote_text:
                        pdf.add_blockquote(quote_text)
                        
                elif element.name == 'li':
                    text = element.get_text().strip()
                    if text:
                        parent = element.find_parent(['ul', 'ol'])
                        is_ordered = parent.name == 'ol' if parent else False
                        
                        if is_ordered:
                            list_counter += 1
                        else:
                            list_counter = 0
                            
                        pdf.add_list_item(text, is_ordered, list_counter)
                        
            except Exception as e:
                # Skip problematic elements
                continue
        
        # Output PDF to buffer
        pdf_buffer = BytesIO()
        pdf_output = pdf.output()  # Returns bytes directly in fpdf2
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)
        
        return pdf_buffer
        
    except Exception as e:
        st.error(f"PDF Generation Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def get_pdf_download_link(pdf_buffer, filename):
    """Generate a download link for PDF"""
    b64 = base64.b64encode(pdf_buffer.read()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}.pdf" style="display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center; border: none; cursor: pointer; font-size: 16px;">📄 Download PDF</a>'
    return href

# ---------- File Upload and Management ----------
st.subheader("📁 File Management")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload a text file", 
        type=['txt', 'md'],
        help="Upload a .txt or .md file to visualize"
    )

with col2:
    if st.session_state.uploaded_file and st.button("🗑️ Remove File", use_container_width=True):
        st.session_state.uploaded_file = None
        st.session_state.file_content = ""
        st.rerun()

# Handle file upload
if uploaded_file is not None:
    if uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.file_content = content
        except:
            st.error("Error reading file. Please ensure it's a valid text file.")
    st.success(f"✅ File loaded: {uploaded_file.name}")

# ---------- Print Button ----------
if st.session_state.file_content:
    st.subheader("🖨️ PDF Export")
    
    col_print1, col_print2 = st.columns([1, 2])
    
    with col_print1:
        pdf_filename = st.text_input(
            "PDF Filename", 
            value=st.session_state.uploaded_file.name.replace('.txt', '').replace('.md', '') 
            if st.session_state.uploaded_file else "document",
            help="Name for the PDF file (without extension)"
        )
        
        if st.button("🖨️ Generate PDF", use_container_width=True, type="primary"):
            with st.spinner("Generating PDF..."):
                pdf_buffer = create_pdf_from_markdown(
                    st.session_state.file_content, 
                    pdf_filename
                )
                
                if pdf_buffer:
                    st.markdown(
                        get_pdf_download_link(pdf_buffer, pdf_filename), 
                        unsafe_allow_html=True
                    )
                    st.success("✅ PDF generated successfully!")
                else:
                    st.error("❌ Failed to generate PDF. Please check the error message above.")
    
    with col_print2:
        st.info("""
        **PDF Features:**
        - 📄 Professional A4 formatting
        - 🔢 Automatic page numbers
        - 📏 Clean margins & spacing
        - 🎨 Styled headers & code blocks
        - 📑 Smart page breaks
        - ✅ **Zero system dependencies!**
        
        **Install:** `pip install fpdf2 markdown beautifulsoup4`
        """)

# ---------- Markdown Visualizer ----------
if st.session_state.file_content:
    st.subheader("👁️ Markdown Preview")
    
    if st.session_state.uploaded_file:
        st.caption(f"📊 File: {st.session_state.uploaded_file.name} | "
                  f"Size: {len(st.session_state.file_content):,} characters | "
                  f"Lines: {st.session_state.file_content.count(chr(10)) + 1}")
    
    st.markdown(st.session_state.file_content, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
else:
    st.subheader("📋 Instructions")
    
    col_inst1, col_inst2 = st.columns(2)
    
    with col_inst1:
        st.markdown("""
        **How to use:**
        1. 📁 **Upload** a text file (.txt or .md)
        2. 👁️ **Preview** the formatted content
        3. 🖨️ **Generate PDF** with one click
        4. 📄 **Download** your PDF file
        
        **Supported formats:**
        - `.txt` files with Markdown syntax
        - `.md` Markdown files
        - Plain text with basic formatting
        """)
    
    with col_inst2:
        st.markdown("""
        **PDF Features:**
        - Professional A4 layout
        - Automatic page numbering
        - Clean formatting
        - Code block support
        - Smart page breaks
        - **Works on all platforms!**
        """)
    
    st.subheader("🎯 Example Markdown")
    example = """# Sample Document
## Introduction
This is a **sample** markdown document with *formatting*.

### Features
- Bullet points work great
- **Bold** and *italic* text
- Code blocks are supported

```python
def hello():
    print("Hello, World!")
```

### Lists
1. First item
2. Second item
3. Third item

> This is a blockquote
> It can span multiple lines
"""
    st.code(example, language="markdown")
    
    st.markdown("---")
    st.caption("Upload a file to get started!")