import sys
import os

sys.path.append(os.getcwd())

print("=" * 60)
print("Testing Document Handlers with OllamaVision OCR")
print("=" * 60)

# Test 1: DOCX
docx_path = r"C:\Users\rudra\Downloads\Brochure.docx"
if os.path.exists(docx_path):
    print(f"\n[DOCX] Testing: {docx_path}")
    from scratchy.document_handlers.docx import DocxHandler
    handler = DocxHandler(docx_path)
    try:
        text = handler.get_text()
        print(f"  ✅ Success: {len(text)} chars extracted")
        print(f"  Preview: {text[:200]}..." if len(text) > 200 else f"  Preview: {text}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
else:
    print(f"\n[DOCX] Skipped: {docx_path} not found")

# Test 2: PDF
pdf_path = r"C:\Users\rudra\Desktop\kulkarni2011.pdf"
if os.path.exists(pdf_path):
    print(f"\n[PDF] Testing: {pdf_path}")
    from scratchy.document_handlers.pdf import PDFHandler
    handler = PDFHandler(pdf_path)
    try:
        text = handler.get_text()
        print(f"  ✅ Success: {len(text)} chars extracted")
        print(f"  Preview: {text[:200]}..." if len(text) > 200 else f"  Preview: {text}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
else:
    print(f"\n[PDF] Skipped: {pdf_path} not found")

# Test 3: PPTX
pptx_path = r"C:\Users\rudra\Desktop\Basic Presentation.pptx"
if os.path.exists(pptx_path):
    print(f"\n[PPTX] Testing: {pptx_path}")
    from scratchy.document_handlers.pptx import PPTXHandler
    handler = PPTXHandler(pptx_path)
    try:
        text = handler.get_text()
        print(f"  ✅ Success: {len(text)} chars extracted")
        print(f"  Preview: {text[:200]}..." if len(text) > 200 else f"  Preview: {text}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
else:
    print(f"\n[PPTX] Skipped: {pptx_path} not found")

# Test 4: Image
img_path = r"C:\Users\rudra\Desktop\test_image.png"
if os.path.exists(img_path):
    print(f"\n[IMAGE] Testing: {img_path}")
    from scratchy.document_handlers.image import ImageHandler
    handler = ImageHandler(img_path)
    try:
        text = handler.get_text()
        print(f"  ✅ Success: {len(text)} chars extracted")
        print(f"  Preview: {text[:200]}..." if len(text) > 200 else f"  Preview: {text}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
else:
    print(f"\n[IMAGE] Skipped: {img_path} not found")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)