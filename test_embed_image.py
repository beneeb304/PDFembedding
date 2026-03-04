import os
import tempfile
import unittest
from embed_image_in_pdf import SecretImageEmbedder

HERE = os.path.dirname(__file__)
INPUT_PDF = os.path.join(HERE, 'input.pdf')
INPUT_IMG = os.path.join(HERE, 'secret.png')

class TestEmbedExtract(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='steg_test_')

    def tearDown(self):
        # remove files created during tests
        for fname in os.listdir(self.tmpdir):
            try:
                os.remove(os.path.join(self.tmpdir, fname))
            except Exception:
                pass
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def _compare_files(self, a, b):
        with open(a, 'rb') as fa, open(b, 'rb') as fb:
            self.assertEqual(fa.read(), fb.read())

    def test_metadata_roundtrip(self):
        out_pdf = os.path.join(self.tmpdir, 'out_meta.pdf')
        recovered = os.path.join(self.tmpdir, 'rec_meta.png')

        ok = SecretImageEmbedder.embed_in_metadata(INPUT_PDF, INPUT_IMG, out_pdf)
        self.assertTrue(ok)

        ok2 = SecretImageEmbedder.extract_from_metadata(out_pdf, recovered)
        self.assertTrue(ok2)
        self._compare_files(INPUT_IMG, recovered)

    def test_trailing_roundtrip(self):
        out_pdf = os.path.join(self.tmpdir, 'out_trail.pdf')
        recovered = os.path.join(self.tmpdir, 'rec_trail.png')

        ok = SecretImageEmbedder.embed_as_trailing_data(INPUT_PDF, INPUT_IMG, out_pdf)
        self.assertTrue(ok)

        ok2 = SecretImageEmbedder.extract_trailing_data(out_pdf, recovered)
        self.assertTrue(ok2)
        self._compare_files(INPUT_IMG, recovered)

    def test_hidden_object_roundtrip(self):
        out_pdf = os.path.join(self.tmpdir, 'out_hidden.pdf')
        recovered = os.path.join(self.tmpdir, 'rec_hidden.png')

        ok = SecretImageEmbedder.embed_as_hidden_object(INPUT_PDF, INPUT_IMG, out_pdf)
        self.assertTrue(ok)

        ok2 = SecretImageEmbedder.extract_hidden_object(out_pdf, recovered)
        self.assertTrue(ok2)
        self._compare_files(INPUT_IMG, recovered)

    def test_unified_extract(self):
        # embed as hidden object then use unified extract()
        out_pdf = os.path.join(self.tmpdir, 'out_unified.pdf')
        recovered = os.path.join(self.tmpdir, 'rec_unified.png')
        SecretImageEmbedder.embed_as_hidden_object(INPUT_PDF, INPUT_IMG, out_pdf)
        ok = SecretImageEmbedder.extract(out_pdf, recovered)
        self.assertTrue(ok)
        self._compare_files(INPUT_IMG, recovered)

    def test_encrypted_pdf_behavior(self):
        """Create an encrypted copy of the input PDF and verify extractor behavior.

        The test verifies that attempting to extract from an encrypted PDF
        (without supplying a password) does not silently succeed. Then we
        decrypt a copy and verify extraction succeeds on the decrypted file.
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except Exception:
            self.skipTest('PyPDF2 required for encryption tests')

        password = 'testpass'
        enc_pdf = os.path.join(self.tmpdir, 'enc_input.pdf')
        dec_pdf = os.path.join(self.tmpdir, 'dec_input.pdf')

        # create encrypted PDF from INPUT_PDF
        reader = PdfReader(INPUT_PDF)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        writer.encrypt(password)
        with open(enc_pdf, 'wb') as f:
            writer.write(f)

        # Attempt extraction from encrypted PDF should fail (no password supplied)
        out_encrypted_recovered = os.path.join(self.tmpdir, 'rec_enc.png')
        ok = SecretImageEmbedder.extract(enc_pdf, out_encrypted_recovered)
        self.assertFalse(ok, 'Extraction should not succeed on encrypted PDF without password')

        # Now decrypt to a new file and confirm extraction works on decrypted PDF
        # (simulate a user providing the password by writing an unencrypted copy)
        r2 = PdfReader(enc_pdf)
        # decrypt and write decrypted copy
        try:
            r2.decrypt(password)
        except Exception:
            # older/newer PyPDF2 variants differ; try reader with password param
            pass
        w2 = PdfWriter()
        for p in r2.pages:
            w2.add_page(p)
        with open(dec_pdf, 'wb') as f:
            w2.write(f)

        # Embed attachment into decrypted copy and extract using unified extractor
        out_after = os.path.join(self.tmpdir, 'out_after.pdf')
        recovered_after = os.path.join(self.tmpdir, 'rec_after.png')
        SecretImageEmbedder.embed_as_hidden_object(dec_pdf, INPUT_IMG, out_after)
        ok2 = SecretImageEmbedder.extract(out_after, recovered_after)
        self.assertTrue(ok2)
        self._compare_files(INPUT_IMG, recovered_after)

if __name__ == '__main__':
    unittest.main()
