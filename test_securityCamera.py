import unittest
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.encoders import encode_base64
import os
from securityCamera import create_message

class TestCreateMessage(unittest.TestCase):

    def setUp(self):
        # Create a temporary file to use as an attachment
        self.attachment_path = "test_attachment.jpg"
        with open(self.attachment_path, "wb") as f:
            f.write(b"Test image content")

        self.from_addr = "sender@example.com"
        self.to_addr = "recipient@example.com"
        self.subject = "Test Subject"
        self.body = "This is a test email."

    def tearDown(self):
        # Remove the temporary file after the test
        if os.path.exists(self.attachment_path):
            os.remove(self.attachment_path)

    def test_create_message_structure(self):
        msg = create_message(
            self.from_addr,
            self.to_addr,
            self.subject,
            self.body,
            self.attachment_path
        )

        # Check if the returned object is an instance of MIMEMultipart
        self.assertIsInstance(msg, MIMEMultipart)

        # Check the email headers
        self.assertEqual(msg["From"], self.from_addr)
        self.assertEqual(msg["To"], self.to_addr)
        self.assertEqual(msg["Subject"], self.subject)

        # Check the email body
        body = msg.get_payload(0)
        self.assertIsInstance(body, MIMEText)
        self.assertEqual(body.get_payload(), self.body)

        # Check the attachment
        attachment = msg.get_payload(1)
        self.assertIsInstance(attachment, MIMEBase)
        self.assertEqual(attachment.get_content_type(), "image/jpeg")
        self.assertEqual(attachment.get_filename(), self.attachment_path)

    def test_create_message_with_missing_attachment(self):
        with self.assertRaises(FileNotFoundError):
            create_message(
                self.from_addr,
                self.to_addr,
                self.subject,
                self.body,
                "non_existent_file.jpg"
            )

if __name__ == "__main__":
    unittest.main()