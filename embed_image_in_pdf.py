"""
Secret Image Embedding in PDF
Embeds image data directly into PDF structure without steganography
"""

import os
import base64
import struct
import zlib
from pathlib import Path

try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import DictionaryObject, ArrayObject, TextStringObject, NameObject
except ImportError:
    PdfReader = None
    PdfWriter = None


class SecretImageEmbedder:
    """Embed images secretly into PDF files"""
    
    # Magic signature to identify embedded data
    MAGIC_SIGNATURE = b'\x53\x45\x43\x52\x45\x54\x49\x4D\x47'  # SECRETIMG
    VERSION = b'\x01'  # Version 1
    
    @staticmethod
    def embed_in_metadata(pdf_path, image_path, output_pdf_path):
        """
        Embed image data in PDF metadata/info dictionary
        The image data is stored in custom metadata fields
        
        Args:
            pdf_path: Path to input PDF
            image_path: Path to image file to embed
            output_pdf_path: Path to output PDF
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        # Read image
        print("[*] Reading image...")
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_name = os.path.basename(image_path)
        print(f"[*] Image size: {len(image_data)} bytes")
        print(f"[*] Image name: {image_name}")
        
        # Compress image data to reduce size
        print("[*] Compressing image...")
        compressed_data = zlib.compress(image_data, 6)  # Use level 6 instead of 9 for speed
        print(f"[*] Compressed size: {len(compressed_data)} bytes")
        print(f"[*] Compression ratio: {len(compressed_data)/len(image_data):.2%}")
        
        # Encode as base64 for safe storage in PDF
        print("[*] Encoding...")
        encoded_data = base64.b64encode(compressed_data).decode('ascii')
        
        # Read PDF
        print("[*] Reading PDF...")
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Copy all pages
        print("[*] Copying pages...")
        for page in reader.pages:
            writer.add_page(page)
        
        # Add custom metadata with embedded image
        if writer._info is None:
            writer._info = DictionaryObject()
        
        # Get the actual dictionary object (in case it's an indirect reference)
        info = writer._info
        if hasattr(info, 'get_object'):
            info = info.get_object()
        
        # Create custom metadata fields
        info[NameObject("/EmbeddedImage")] = TextStringObject(image_name)
        info[NameObject("/EmbeddedImageData")] = TextStringObject(encoded_data)
        info[NameObject("/EmbeddedImageSize")] = TextStringObject(str(len(image_data)))
        info[NameObject("/Secret")] = TextStringObject("Image embedded in metadata")
        
        # Write output
        print("[*] Writing PDF...")
        with open(output_pdf_path, 'wb') as f:
            writer.write(f)
        
        print(f"[+] Image embedded in PDF metadata: {output_pdf_path}")
        return True
    
    @staticmethod
    def extract_from_metadata(pdf_path, output_image_path):
        """
        Extract image from PDF metadata
        
        Args:
            pdf_path: Path to PDF with embedded image
            output_image_path: Path to save extracted image
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        reader = PdfReader(pdf_path)
        
        # Get metadata
        if reader.metadata is None:
            print("[!] No metadata found in PDF")
            return False
        
        # Look for embedded image data
        if "/EmbeddedImageData" not in reader.metadata:
            print("[!] No embedded image found in metadata")
            return False
        
        try:
            image_name = reader.metadata.get("/EmbeddedImage", "extracted_image")
            encoded_data = reader.metadata["/EmbeddedImageData"]
            
            # Decode from base64
            compressed_data = base64.b64decode(encoded_data)
            
            # Decompress
            image_data = zlib.decompress(compressed_data)
            
            # Save image
            with open(output_image_path, 'wb') as f:
                f.write(image_data)
            
            print(f"[+] Image extracted: {output_image_path}")
            print(f"[*] Original image name: {image_name}")
            print(f"[*] Size: {len(image_data)} bytes")
            return True
        
        except Exception as e:
            print(f"[!] Error extracting image: {e}")
            return False
    
    @staticmethod
    def embed_as_trailing_data(pdf_path, image_path, output_pdf_path):
        """
        Embed image by appending to PDF file as trailing data
        PDFs are tolerant of data after the EOF marker
        
        Args:
            pdf_path: Path to input PDF
            image_path: Path to image file to embed
            output_pdf_path: Path to output PDF
        """
        # Read original PDF
        print("[*] Reading PDF...")
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Read image
        print("[*] Reading image...")
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_name = os.path.basename(image_path)
        print(f"[*] Image size: {len(image_data)} bytes")
        
        # Create trailing data structure
        # Format: MAGIC | VERSION | name_length | name | image_length | image | checksum
        print("[*] Creating trailing data structure...")
        trailing_data = bytearray()
        trailing_data.extend(SecretImageEmbedder.MAGIC_SIGNATURE)
        trailing_data.extend(SecretImageEmbedder.VERSION)
        
        # Add image name length and name
        name_bytes = image_name.encode('utf-8')
        trailing_data.extend(struct.pack('>H', len(name_bytes)))
        trailing_data.extend(name_bytes)
        
        # Add image length and image data
        trailing_data.extend(struct.pack('>I', len(image_data)))
        trailing_data.extend(image_data)
        
        # Add CRC32 checksum
        checksum = zlib.crc32(image_data) & 0xffffffff
        trailing_data.extend(struct.pack('>I', checksum))
        
        # Write combined file
        print("[*] Writing output PDF...")
        with open(output_pdf_path, 'wb') as f:
            f.write(pdf_data)
            f.write(b'\n')  # PDF friendly separator
            f.write(trailing_data)
        
        print(f"[+] Image embedded as trailing data: {output_pdf_path}")
        return True
    
    @staticmethod
    def extract_trailing_data(pdf_path, output_image_path):
        """
        Extract image from trailing data in PDF
        
        Args:
            pdf_path: Path to PDF with trailing data
            output_image_path: Path to save extracted image
        """
        with open(pdf_path, 'rb') as f:
            file_data = f.read()
        
        # Find the magic signature
        magic_index = file_data.rfind(SecretImageEmbedder.MAGIC_SIGNATURE)
        
        if magic_index == -1:
            print("[!] No embedded data signature found")
            return False
        
        try:
            offset = magic_index
            
            # Skip magic and version
            offset += len(SecretImageEmbedder.MAGIC_SIGNATURE)
            version = file_data[offset:offset+1]
            offset += 1
            
            if version != SecretImageEmbedder.VERSION:
                print(f"[!] Unsupported version: {version.hex()}")
                return False
            
            # Read image name
            name_length = struct.unpack('>H', file_data[offset:offset+2])[0]
            offset += 2
            image_name = file_data[offset:offset+name_length].decode('utf-8')
            offset += name_length
            
            # Read image data
            image_length = struct.unpack('>I', file_data[offset:offset+4])[0]
            offset += 4
            image_data = file_data[offset:offset+image_length]
            offset += image_length
            
            # Verify checksum
            stored_checksum = struct.unpack('>I', file_data[offset:offset+4])[0]
            actual_checksum = zlib.crc32(image_data) & 0xffffffff
            
            if stored_checksum != actual_checksum:
                print("[!] Checksum mismatch - data may be corrupted")
                return False
            
            # Save image
            with open(output_image_path, 'wb') as f:
                f.write(image_data)
            
            print(f"[+] Image extracted: {output_image_path}")
            print(f"[*] Original name: {image_name}")
            print(f"[*] Size: {len(image_data)} bytes")
            return True
        
        except Exception as e:
            print(f"[!] Error extracting image: {e}")
            return False
    
    @staticmethod
    def extract(pdf_path, output_image_path):
        """
        High‑level extraction: metadata → hidden-object → trailing data.  Logs each
        attempt so the user can see what’s happening.
        """
        # metadata
        print("[*] Trying metadata extraction...")
        try:
            if SecretImageEmbedder.extract_from_metadata(pdf_path, output_image_path):
                return True
        except Exception:
            pass
        # hidden object
        print("[*] Trying hidden-object extraction...")
        try:
            if SecretImageEmbedder.extract_hidden_object(pdf_path, output_image_path):
                return True
        except Exception as e:
            print(f"[!] Hidden-object extraction error: {e}")
        # trailing data
        print("[*] Trying trailing data extraction...")
        return SecretImageEmbedder.extract_trailing_data(pdf_path, output_image_path)

    @staticmethod
    def extract_hidden_object(pdf_path, output_image_path):
        """
        Extract an embedded file attachment from a PDF and write it out as the
        recovered image.  Only the first file is used; additional attachments
        are ignored.  The method returns False if no embedded files are present.
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")

        reader = PdfReader(pdf_path)
        root = reader.trailer.get("/Root")
        if hasattr(root, 'get_object'):
            root = root.get_object()
        if not root:
            print("[!] PDF structure missing Root")
            return False
        names = root.get("/Names")
        if hasattr(names, 'get_object'):
            names = names.get_object()
        if not names or "/EmbeddedFiles" not in names:
            print("[!] No embedded files present")
            return False
        ef = names["/EmbeddedFiles"].get("/Names")
        if not ef or len(ef) < 2:
            print("[!] Embedded files list empty")
            return False
        # ef is [name1, filespec1, name2, filespec2, ...]
        fname = ef[0]
        filespec = ef[1]
        try:
            file_obj = filespec["/EF"]["/F"].get_object()
            data = file_obj.get_data()
        except Exception as e:
            print(f"[!] Failed to read embedded file stream: {e}")
            return False
        with open(output_image_path, 'wb') as f:
            f.write(data)
        print(f"[+] Hidden object extracted: {output_image_path}")
        print(f"[*] Original attachment name: {fname}")
        print(f"[*] Size: {len(data)} bytes")
        return True

    @staticmethod
    def embed_as_hidden_object(pdf_path, image_path, output_pdf_path):
        """
        Embed image in PDF as a hidden object (file attachment).
        This creates an embedded file entry in the document catalog, which is
        supported by most PDF viewers but is not visible on any page.  This is a
        more 'official' mechanism than appending trailing bytes.
        
        Args:
            pdf_path: Path to input PDF
            image_path: Path to image file to embed
            output_pdf_path: Path to output PDF
        """
        if PdfReader is None or PdfWriter is None:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")

        # read original PDF pages
        print("[*] Reading PDF...")
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        # read image data
        print("[*] Reading image for attachment...")
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_name = os.path.basename(image_path)
        print(f"[*] Adding {image_name} as embedded file")

        # use PdfWriter API to add attachment
        writer.add_attachment(image_name, image_data)

        # write output
        print("[*] Writing output PDF with hidden object...")
        with open(output_pdf_path, 'wb') as f:
            writer.write(f)

        print(f"[+] Image embedded as hidden object: {output_pdf_path}")
        return True


def embed_image_interactive():
    """Interactive mode for embedding images"""
    print("\n=== Secret Image Embedder ===\n")
    
    # Get PDF path
    pdf_path = input("Enter PDF file path: ").strip()
    if not os.path.exists(pdf_path):
        print("[!] PDF file not found")
        return
    
    # Get image path
    image_path = input("Enter image file path: ").strip()
    if not os.path.exists(image_path):
        print("[!] Image file not found")
        return
    
    # Get output path
    output_pdf = input("Enter output PDF name (default: output.pdf): ").strip()
    if not output_pdf:
        output_pdf = "output.pdf"
    
    # Choose embedding method
    print("\nEmbedding methods:")
    print("1. Metadata (fast, small overhead, ~5-10MB limit)")
    print("2. Trailing data (faster, unlimited capacity)")
    print("3. Hidden object/attachment (invisible file)")
    
    method = input("Choose method (1-3): ").strip()
    
    try:
        embedder = SecretImageEmbedder()
        
        if method == "1":
            embedder.embed_in_metadata(pdf_path, image_path, output_pdf)
        elif method == "2":
            embedder.embed_as_trailing_data(pdf_path, image_path, output_pdf)
        elif method == "3":
            embedder.embed_as_hidden_object(pdf_path, image_path, output_pdf)
        else:
            print("[!] Invalid method")
            return
        
        print(f"\n[+] Done! Output: {output_pdf}")
        
    except Exception as e:
        print(f"[!] Error: {e}")


def extract_image_interactive():
    """Interactive mode for extracting images"""
    print("\n=== Secret Image Extractor ===\n")
    
    pdf_path = input("Enter PDF file path: ").strip()
    if not os.path.exists(pdf_path):
        print("[!] PDF file not found")
        return
    
    output_image = input("Enter output image name (default: extracted.png): ").strip()
    if not output_image:
        output_image = "extracted.png"
    
    embedder = SecretImageEmbedder()
    
    print("[*] Attempting to recover embedded image...")
    if embedder.extract(pdf_path, output_image):
        return
    
    print("[!] Could not extract image using any method")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "embed":
            # Command line mode: embed <pdf> <image> <output>
            if len(sys.argv) >= 5:
                pdf = sys.argv[2]
                img = sys.argv[3]
                out = sys.argv[4]
                method = sys.argv[5] if len(sys.argv) > 5 else "1"
                
                try:
                    embedder = SecretImageEmbedder()
                    if method == "1":
                        embedder.embed_in_metadata(pdf, img, out)
                    elif method == "2":
                        embedder.embed_as_trailing_data(pdf, img, out)
                    elif method == "3":
                        embedder.embed_as_hidden_object(pdf, img, out)
                    else:
                        print("Invalid method - use 1, 2 or 3")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Usage: python script.py embed <pdf> <image> <output> [method]")
                print("Methods: 1=metadata, 2=trailing, 3=hidden object")
        
        elif sys.argv[1] == "extract":
            # Command line mode: extract <pdf> <output>
            if len(sys.argv) >= 4:
                pdf = sys.argv[2]
                out = sys.argv[3]
                
                embedder = SecretImageEmbedder()
                embedder.extract(pdf, out)
            else:
                print("Usage: python script.py extract <pdf> <output>")
        else:
            print("Usage: python script.py [embed|extract|interactive]")
    else:
        # Interactive mode
        print("\nSecret Image Embedder")
        print("====================")
        print("1. Embed image in PDF")
        print("2. Extract image from PDF")
        print("3. Exit")
        
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            embed_image_interactive()
        elif choice == "2":
            extract_image_interactive()
        else:
            print("Exiting...")
