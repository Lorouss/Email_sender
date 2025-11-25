import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import json
import os
import time
import random
from datetime import datetime
import re
from html.parser import HTMLParser
import tempfile
import webbrowser

# ------------------------------------------------------------------
# المساعد: HTML to Text Extractor
# ------------------------------------------------------------------
class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_style = False
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            self.in_style = True
        elif tag == 'script':
            self.in_script = True
        elif tag == 'a':
            self.text.append("[Link: ")
        elif tag == 'br':
            self.text.append('\n')
        elif tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'tr']:
            if self.text and self.text[-1] != '\n':
                 self.text.append('\n')

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False
        elif tag == 'script':
            self.in_script = False
        elif tag == 'a':
             self.text.append("] ")
        elif tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'tr']:
            self.text.append('\n')

    def handle_data(self, data):
        if not self.in_style and not self.in_script:
            clean_data = data.strip()
            if clean_data:
                self.text.append(clean_data + ' ')

class BulkEmailSender:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Sender")
        self.root.geometry("1280x800")
        self.root.configure(bg="#1e1e2e")

        # Configuration file
        self.config_file = "smtp_config.json"
        self.smtp_config = self.load_smtp_config()

        # متغير لتتبع ملف المتصفح المؤقت
        self.temp_html_file = None

        # Style configuration
        self.setup_styles()

        # Create main container
        main_container = ttk.Frame(root, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container, style="TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 1. Create tab frames and necessary variables first
        self.create_smtp_tab()
        self.create_recipients_tab()
        self.create_send_tab()
        self.create_compose_tab()

        # 2. Add tabs to the notebook in the desired visual order (الترتيب المرئي)
        self.notebook.add(self.smtp_frame, text="📧 SMTP Settings")
        self.notebook.add(self.recipients_frame, text="👥 Recipients")
        self.notebook.add(self.compose_frame, text="✍️ Compose Email")
        self.notebook.add(self.send_frame, text="🚀 Send")

        # 3. Define helpers and start auto-update
        self.HTMLTextExtractor = HTMLTextExtractor

        self.schedule_preview_update()

    def setup_styles(self):
        # ... (لم يتغير) ...
        style = ttk.Style()
        style.theme_use('clam')

        # Main frame style
        style.configure("Main.TFrame", background="#1e1e2e")

        # Notebook style
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab",
                        background="#2d2d44",
                        foreground="#cdd6f4",
                        padding=[20, 10],
                        font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#45475a")],
                  foreground=[("selected", "#89dceb")])

        # Frame style
        style.configure("Card.TFrame", background="#2d2d44", relief="flat")

        # Label style
        style.configure("TLabel",
                        background="#2d2d44",
                        foreground="#cdd6f4",
                        font=("Segoe UI", 10))
        style.configure("Header.TLabel",
                        background="#2d2d44",
                        foreground="#89dceb",
                        font=("Segoe UI", 14, "bold"))

        # Button style
        style.configure("Accent.TButton",
                        background="#89b4fa",
                        foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        focuscolor="none",
                        padding=[20, 10])
        style.map("Accent.TButton",
                  background=[("active", "#74c7ec")])

        style.configure("Success.TButton",
                        background="#a6e3a1",
                        foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        padding=[20, 10])

    def create_smtp_tab(self):
        # ... (لم يتغير) ...
        """SMTP Configuration Tab"""
        smtp_frame = ttk.Frame(self.notebook, style="Main.TFrame")
        self.smtp_frame = smtp_frame

        # Card container
        card = ttk.Frame(smtp_frame, style="Card.TFrame", padding=30)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = ttk.Label(card, text="SMTP Configuration", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=2, pady=(0, 30), sticky="w")

        # SMTP Server
        ttk.Label(card, text="SMTP Server:").grid(row=1, column=0, sticky="w", pady=10)
        self.smtp_server = ttk.Entry(card, width=40, font=("Segoe UI", 10))
        self.smtp_server.grid(row=1, column=1, sticky="ew", pady=10, padx=(10, 0))
        self.smtp_server.insert(0, self.smtp_config.get("server", "smtp.gmail.com"))

        # SMTP Port
        ttk.Label(card, text="SMTP Port:").grid(row=2, column=0, sticky="w", pady=10)
        self.smtp_port = ttk.Entry(card, width=40, font=("Segoe UI", 10))
        self.smtp_port.grid(row=2, column=1, sticky="ew", pady=10, padx=(10, 0))
        self.smtp_port.insert(0, self.smtp_config.get("port", "587"))

        # Email
        ttk.Label(card, text="Your Email:").grid(row=3, column=0, sticky="w", pady=10)
        self.smtp_email = ttk.Entry(card, width=40, font=("Segoe UI", 10))
        self.smtp_email.grid(row=3, column=1, sticky="ew", pady=10, padx=(10, 0))
        self.smtp_email.insert(0, self.smtp_config.get("email", ""))

        # Password
        ttk.Label(card, text="Password/App Password:").grid(row=4, column=0, sticky="w", pady=10)
        self.smtp_password = ttk.Entry(card, width=40, show="*", font=("Segoe UI", 10))
        self.smtp_password.grid(row=4, column=1, sticky="ew", pady=10, padx=(10, 0))
        self.smtp_password.insert(0, self.smtp_config.get("password", ""))

        # Delay between emails (anti-spam)
        ttk.Label(card, text="Delay Between Emails (sec):").grid(row=5, column=0, sticky="w", pady=10)
        self.email_delay = ttk.Entry(card, width=40, font=("Segoe UI", 10))
        self.email_delay.grid(row=5, column=1, sticky="ew", pady=10, padx=(10, 0))
        self.email_delay.insert(0, self.smtp_config.get("delay", "2"))

        # Buttons frame
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(30, 0))

        ttk.Button(btn_frame, text="💾 Save Configuration",
                   command=self.save_smtp_config,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="🧪 Test Connection",
                   command=self.test_smtp_connection,
                   style="Success.TButton").pack(side=tk.LEFT, padx=5)

        # Configure grid weights
        card.columnconfigure(1, weight=1)

        # Info label
        info_text = "💡 Tip: Use App Passwords for Gmail/Outlook for better security and deliverability"
        info_label = ttk.Label(card, text=info_text, foreground="#f9e2af")
        info_label.grid(row=7, column=0, columnspan=2, pady=(20, 0))

    def create_compose_tab(self):
        # ... (لم يتغير) ...
        """Email Composition Tab"""
        compose_frame = ttk.Frame(self.notebook, style="Main.TFrame")
        self.compose_frame = compose_frame

        # Main container with two columns
        main_container = ttk.Frame(compose_frame, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side - Editor
        left_frame = ttk.Frame(main_container, style="Card.TFrame", padding=20)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Header
        header = ttk.Label(left_frame, text="Compose Your Email", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 20))

        # Subject
        subject_frame = ttk.Frame(left_frame, style="Card.TFrame")
        subject_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(subject_frame, text="Subject:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.email_subject = ttk.Entry(subject_frame, font=("Segoe UI", 11))
        self.email_subject.pack(fill=tk.X, pady=(5, 0))

        # HTML Editor
        html_frame = ttk.Frame(left_frame, style="Card.TFrame")
        html_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        ttk.Label(html_frame, text="HTML Content:", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.html_editor = scrolledtext.ScrolledText(
            html_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat",
            padx=10,
            pady=10
        )
        self.html_editor.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # ربط زر Ctrl+A لتحديد الكل
        self.html_editor.bind("<Control-a>", self.select_all_text)
        self.html_editor.bind("<Command-a>", self.select_all_text)

        # Buttons for left frame (Editor controls)
        btn_frame_left = ttk.Frame(left_frame, style="Card.TFrame")
        btn_frame_left.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame_left, text="📄 Load Template",
                   command=self.load_html_template,
                   style="Success.TButton").pack(side=tk.LEFT, padx=5)

        # Right side - Preview
        right_frame = ttk.Frame(main_container, style="Card.TFrame", padding=20)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Preview header
        preview_header = ttk.Label(right_frame, text="Live Preview", style="Header.TLabel")
        preview_header.pack(anchor="w", pady=(0, 20))

        # Preview frame with border
        preview_container = ttk.Frame(right_frame, style="Card.TFrame")
        preview_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Preview text widget (read-only HTML display)
        self.preview_display = scrolledtext.ScrolledText(
            preview_container,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="solid",
            borderwidth=2,
            padx=15,
            pady=15,
            state='disabled'
        )
        self.preview_display.pack(fill=tk.BOTH, expand=True)

        # Buttons for right frame (Preview controls)
        btn_frame_right = ttk.Frame(right_frame, style="Card.TFrame")
        btn_frame_right.pack(fill=tk.X, pady=(10, 0))

        # زر Open/Update in Browser الوحيد
        ttk.Button(btn_frame_right, text="🌐 Open/Update in Browser",
                   command=self.preview_email,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)


        # Default HTML template
        default_html = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .button { background: #667eea; color: white; padding: 12px 30px;
                  text-decoration: none; border-radius: 5px; display: inline-block; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Hello {{name}}!</h1>
        </div>
        <div class="content">
            <p>This is your personalized email message.</p>
            <p>You can customize this template with HTML and CSS.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="#" class="button">Call to Action</a>
            </p>
            <ul><li>Item 1</li><li>Item 2</li></ul>
        </div>
        <div class="footer">
            <p>© 2025 Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
        self.html_editor.insert("1.0", default_html)

        self.update_text_preview()

    # الدالة الجديدة لتحديد الكل (Select All)
    def select_all_text(self, event):
        # ... (لم يتغير) ...
        """Selects all text in the HTML editor on Ctrl+A or Cmd+A."""
        event.widget.event_generate("<<SelectAll>>")
        return "break"

    def create_recipients_tab(self):
        # ... (لم يتغير) ...
        """Recipients Management Tab"""
        recipients_frame = ttk.Frame(self.notebook, style="Main.TFrame")
        self.recipients_frame = recipients_frame

        # Card container
        card = ttk.Frame(recipients_frame, style="Card.TFrame", padding=30)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = ttk.Label(card, text="Manage Recipients", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 20))

        # Import buttons
        import_frame = ttk.Frame(card, style="Card.TFrame")
        import_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(import_frame, text="📂 Import CSV",
                   command=lambda: self.import_recipients("csv"),
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(import_frame, text="📄 Import TXT",
                   command=lambda: self.import_recipients("txt"),
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(import_frame, text="🗑️ Clear All",
                   command=self.clear_recipients,
                   style="Success.TButton").pack(side=tk.LEFT, padx=5)

        # Recipients text area
        ttk.Label(card, text="Recipients (one email per line or CSV format: email,name):",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.recipients_text = scrolledtext.ScrolledText(
            card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat",
            padx=10,
            pady=10,
            height=15
        )
        self.recipients_text.pack(fill=tk.BOTH, expand=True)

        # Info
        info_text = "💡 Format: email@example.com or email@example.com,John Doe"
        ttk.Label(card, text=info_text, foreground="#f9e2af").pack(anchor="w", pady=(10, 0))

    def create_send_tab(self):
        # ... (لم يتغير) ...
        """Send Email Tab"""
        send_frame = ttk.Frame(self.notebook, style="Main.TFrame")
        self.send_frame = send_frame

        # Card container
        card = ttk.Frame(send_frame, style="Card.TFrame", padding=30)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = ttk.Label(card, text="Send Campaign", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 20))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            card,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 20))

        # Status text (يتم تعريفها هنا)
        self.status_text = scrolledtext.ScrolledText(
            card,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat",
            padx=10,
            pady=10,
            height=20
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Send button
        self.send_button = ttk.Button(
            card,
            text="🚀 Start Sending Campaign",
            command=self.send_bulk_email,
            style="Success.TButton"
        )
        self.send_button.pack(pady=10)


    def update_text_preview(self):
        # ... (لم يتغير) ...
        """Updates the text-only preview display."""
        try:
            html_content = self.html_editor.get("1.0", tk.END).strip()
            # لا نحتاج لإزالة علامة Beefree هنا، لأنها لا تؤثر على المعاينة النصية.
            html_content = html_content.replace("{{name}}", "Preview User")

            parser = self.HTMLTextExtractor()
            parser.feed(html_content)

            preview_text = ''.join(parser.text)
            preview_text = re.sub(r'[\s]{2,}', ' ', preview_text).strip()
            preview_text = preview_text.replace('\n ', '\n').replace(' \n', '\n')

            self.preview_display.config(state='normal')
            self.preview_display.delete("1.0", tk.END)
            self.preview_display.insert("1.0", preview_text)
            self.preview_display.config(state='disabled')

        except Exception as e:
            pass


    def _update_temp_file(self):
        # ... (لم يتغير) ...
        """Updates the content of the temporary HTML file silently."""
        if not self.temp_html_file or not os.path.exists(self.temp_html_file):
            return

        html_content = self.html_editor.get("1.0", tk.END)
        # لا نطبق التنظيف هنا لأننا نريد رؤية الكود الأصلي في المحرر.
        html_content = html_content.replace("{{name}}", "Preview User")

        try:
            with open(self.temp_html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            self.log_status(f"❌ Error writing to temp file: {str(e)}")


    def preview_email(self):
        # ... (لم يتغير) ...
        """Opens the HTML content in the browser, or updates it if already open."""

        # 1. احصل على المحتوى
        html_content = self.html_editor.get("1.0", tk.END)
        html_content = html_content.replace("{{name}}", "Preview User")

        # 2. إنشاء أو تحديث الملف المؤقت وفتحه لأول مرة
        if not self.temp_html_file or not os.path.exists(self.temp_html_file):
            # إنشاء الملف وفتحه لأول مرة
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                self.temp_html_file = f.name

            webbrowser.open('file://' + self.temp_html_file, new=0)
            self.log_status(f"🌐 Opened live preview in browser: {self.temp_html_file}")
        else:
            # إذا كان الملف موجوداً بالفعل، قم بالتحديث
            self._update_temp_file()
            # لإجبار المتصفح على إعادة التحميل عند النقر على الزر مرة أخرى
            webbrowser.open('file://' + self.temp_html_file, new=0)


    def schedule_preview_update(self):
        # ... (لم يتغير) ...
        """Schedules the preview update every 1000ms (1 second)."""

        # تحديث المعاينة النصية الداخلية دائماً
        self.update_text_preview()

        # تحديث ملف المتصفح المؤقت بهدوء (إذا كان المتصفح مفتوحًا)
        if self.temp_html_file and os.path.exists(self.temp_html_file):
            self._update_temp_file()

        # جدولة التحديث التالي
        self.root.after(1000, self.schedule_preview_update)

    # 💡 الدالة الجديدة: إزالة علامة Beefree
    def _remove_beefree_watermark(self, html_content):
        """
        Removes the specific <tr> block containing the "Designed with Beefree" watermark
        and the Beefree logo image from the HTML content.
        """
        # تعبير نمطي قوي للبحث عن أي <tr> يحتوي على النص أو رابط الشعار وإزالته
        # نبحث عن <tr> الذي يحتوي داخله على Beefree-logo.png أو designedwithbeefree.com
        # Flags=re.DOTALL تسمح لـ . بمطابقة السطور الجديدة

        # هذا التعبير النمطي يطابق من أول <tr> إلى إغلاقه </tr> بشرط أن يحتوي على إحدى العلامات
        pattern = re.compile(
            r'<tr>.*?Beefree-logo\.png.*?</tr>',
            re.IGNORECASE | re.DOTALL
        )

        cleaned_html = pattern.sub('', html_content)

        # محاولة تنظيف ثانية قد تكون أكثر شمولاً لبعض الهياكل
        pattern_2 = re.compile(
            r'<table.*?designedwithbeefree\.com.*?</table>',
            re.IGNORECASE | re.DOTALL
        )
        cleaned_html = pattern_2.sub('', cleaned_html)

        return cleaned_html


    def send_bulk_email(self):
        """Send bulk emails"""
        # ... (التأكد من البيانات لم يتغير) ...
        if not self.smtp_server.get() or not self.smtp_email.get() or not self.smtp_password.get():
            messagebox.showerror("Error", "❌ Please configure SMTP settings first!")
            return

        if not self.email_subject.get():
            messagebox.showerror("Error", "❌ Please enter email subject!")
            return

        recipients = self.parse_recipients()
        if not recipients:
            messagebox.showerror("Error", "❌ No valid recipients found!")
            return

        # Confirm sending
        if not messagebox.askyesno("Confirm",
                                   f"Send email to {len(recipients)} recipients?"):
            return

        # Disable send button
        self.send_button.config(state="disabled")

        # Clear status
        self.status_text.delete("1.0", tk.END)
        self.log_status(f"📧 Starting campaign for {len(recipients)} recipients...")

        # Get delay
        try:
            delay = float(self.email_delay.get())
        except:
            delay = 2

        # احصل على المحتوى الأصلي لـ HTML مرة واحدة
        original_html_content = self.html_editor.get("1.0", tk.END)

        # 💡 تطبيق دالة التنظيف على المحتوى قبل الإرسال
        base_html_content = self._remove_beefree_watermark(original_html_content)

        # Send emails
        success_count = 0
        fail_count = 0

        try:
            server = smtplib.SMTP(self.smtp_server.get(), int(self.smtp_port.get()))
            server.starttls()
            server.login(self.smtp_email.get(), self.smtp_password.get())

            for idx, recipient in enumerate(recipients):
                try:
                    # Create message
                    msg = MIMEMultipart('alternative')
                    msg['From'] = self.smtp_email.get()
                    msg['To'] = recipient['email']
                    msg['Subject'] = self.email_subject.get()

                    # Personalize HTML (نستخدم المحتوى المنظف)
                    html_content = base_html_content.replace("{{name}}",
                                                         recipient['name'] or recipient['email'].split('@')[0])

                    # Attach HTML
                    html_part = MIMEText(html_content, 'html')
                    msg.attach(html_part)

                    # Send email
                    server.send_message(msg)

                    success_count += 1
                    self.log_status(f"✅ Sent to: {recipient['email']}")

                    # Update progress
                    progress = ((idx + 1) / len(recipients)) * 100
                    self.progress_var.set(progress)

                    # Random delay (anti-spam)
                    if idx < len(recipients) - 1:
                        sleep_time = delay + random.uniform(0, 1)
                        time.sleep(sleep_time)

                except Exception as e:
                    fail_count += 1
                    self.log_status(f"❌ Failed to send to {recipient['email']}: {str(e)}")

            server.quit()

            # Final summary
            self.log_status("\n" + "="*50)
            self.log_status(f"📊 Campaign completed!")
            self.log_status(f"✅ Successful: {success_count}")
            self.log_status(f"❌ Failed: {fail_count}")
            self.log_status(f"📈 Success rate: {(success_count/len(recipients)*100):.1f}%")

            messagebox.showinfo("Complete",
                                 f"Campaign finished!\n✅ Sent: {success_count}\n❌ Failed: {fail_count}")

        except Exception as e:
            self.log_status(f"❌ Fatal error: {str(e)}")
            messagebox.showerror("Error", f"❌ Campaign failed: {str(e)}")

        finally:
            # Re-enable send button
            self.send_button.config(state="normal")
            self.progress_var.set(0)


    # ... (بقية الدوال لم تتغير) ...
    def load_smtp_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_smtp_config(self):
        config = {
            "server": self.smtp_server.get(),
            "port": self.smtp_port.get(),
            "email": self.smtp_email.get(),
            "password": self.smtp_password.get(),
            "delay": self.email_delay.get()
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Success", "✅ SMTP configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Failed to save configuration: {str(e)}")

    def test_smtp_connection(self):
        try:
            server = smtplib.SMTP(self.smtp_server.get(), int(self.smtp_port.get()))
            server.starttls()
            server.login(self.smtp_email.get(), self.smtp_password.get())
            server.quit()
            messagebox.showinfo("Success", "✅ SMTP connection successful!")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Connection failed: {str(e)}")

    def load_html_template(self):
        filename = filedialog.askopenfilename(
            title="Select HTML Template",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.html_editor.delete("1.0", tk.END)
                    self.html_editor.insert("1.0", f.read())
                messagebox.showinfo("Success", "✅ Template loaded successfully!")
                self.update_text_preview()
            except Exception as e:
                messagebox.showerror("Error", f"❌ Failed to load template: {str(e)}")

    def import_recipients(self, file_type):
        if file_type == "csv":
            filename = filedialog.askopenfilename(
                title="Select CSV File",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if row:
                                self.recipients_text.insert(tk.END, ','.join(row) + '\n')
                    messagebox.showinfo("Success", "✅ Recipients imported successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"❌ Failed to import: {str(e)}")

        elif file_type == "txt":
            filename = filedialog.askopenfilename(
                title="Select TXT File",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        self.recipients_text.insert(tk.END, f.read())
                    messagebox.showinfo("Success", "✅ Recipients imported successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"❌ Failed to import: {str(e)}")

    def clear_recipients(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all recipients?"):
            self.recipients_text.delete("1.0", tk.END)

    def parse_recipients(self):
        recipients = []
        text = self.recipients_text.get("1.0", tk.END).strip()

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            if ',' in line:
                parts = line.split(',')
                email = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else ""
            else:
                email = line.strip()
                name = ""

            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                recipients.append({"email": email, "name": name})

        return recipients

    def log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()

def main():
    """Main application entry point"""
    root = tk.Tk()

    # Set window icon (optional)
    try:
        root.iconbitmap('email_icon.ico')
    except:
        pass

    # Center window on screen
    root.update_idletasks()
    width = 1200
    height = 800
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # Prevent window from being too small
    root.minsize(900, 600)

    # Create application
    app = BulkEmailSender(root)

    # إضافة دالة تنظيف الملف المؤقت عند إغلاق التطبيق
    def cleanup():
        if app.temp_html_file and os.path.exists(app.temp_html_file):
            try:
                os.remove(app.temp_html_file)
            except Exception as e:
                print(f"Could not clean up temp file: {e}")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", cleanup)

    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
