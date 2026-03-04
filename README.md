# Secret Image Embedder for PDF

Small utility to embed and extract images inside PDF files using three techniques:

- Metadata embedding (base64-compressed image stored in PDF Info/metadata)
- Trailing-data embedding (append custom binary blob after the PDF EOF)
- Hidden object (attach the image as an embedded file in the PDF catalog)

This repository contains the main script `embed_image_in_pdf.py`.

Requirements
------------
- Python 3.8+
- PyPDF2

Install requirements:

```bash
pip install PyPDF2
```

Usage
-----
Run the script in interactive mode (menus):

```bash
python embed_image_in_pdf.py
```

Embed via CLI:

```bash
# embed <pdf> <image> <output> [method]
# method: 1=metadata, 2=trailing, 3=hidden object (attachment)
python embed_image_in_pdf.py embed input.pdf secret.png output.pdf 1
python embed_image_in_pdf.py embed input.pdf secret.png output.pdf 2
python embed_image_in_pdf.py embed input.pdf secret.png output.pdf 3
```

Extract via CLI:

```bash
# extract <pdf> <output>
# The extractor will attempt metadata → hidden-object → trailing-data
python embed_image_in_pdf.py extract somefile.pdf recovered.png
```

Notes and behavior
------------------
- Metadata method stores a compressed, base64-encoded copy of the image in the PDF's metadata. This is convenient but limited by metadata size and viewer support.
- Trailing-data appends a custom structured blob after the PDF. Many PDF readers ignore extra bytes after EOF, so the PDF remains viewable.
- Hidden-object uses the official PDF embedded-files mechanism (attachment). Most viewers expose attachments (for example, Adobe Reader shows them in the attachments pane).
- The extractor attempts methods in this order: metadata, hidden-object (attachment), then trailing-data. It logs each attempt.

Limitations and safety
----------------------
- Embedding increases file size by the size of the image (or compressed image for metadata).
- When embedding large images in metadata, some PDF tools or services may truncate or reject large metadata fields.
- The script resolves indirect PDF objects when reading attachments but does not handle exotic PDF encryption or heavily corrupted files.

Files
-----
- `embed_image_in_pdf.py`: main script with embed/extract functionality.

Quick test
----------
1. Embed a test image as an attachment:

```bash
python embed_image_in_pdf.py embed input.pdf secret.png output_attached.pdf 3
```

2. Extract it back:

```bash
python embed_image_in_pdf.py extract output_attached.pdf recovered.png
```

If `recovered.png` matches the original `secret.png` the roundtrip succeeded.