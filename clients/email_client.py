import os
from dotenv import load_dotenv
from data.email_message import EmailMessage
import win32com.client
import pythoncom
from datetime import datetime

class EmailClient:
    def __init__(self, account_name: str = None):
        load_dotenv()
        self.account_name = account_name or os.getenv("OUTLOOK_ACCOUNT")

    def connect_inbox(self):
        pythoncom.CoInitialize()
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        for account in outlook.Folders:
            if account.Name.lower() == self.account_name.lower():
                return account.Folders["Boîte de réception"], account.Folders["Archive"]
        raise Exception(f"Compte Outlook '{self.account_name}' introuvable.")

    def fetch_emails(self, limit=None, source_folder="inbox"):
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        emails = []
        count = 0
        for message in items:
            if limit and count >= limit:
                break
            try:
                email_msg = self._parse_message(message, source_folder)
                emails.append(email_msg)
                count += 1
            except Exception as e:
                print(f"Erreur lors du traitement d'un e-mail : {e}")
        return emails

    def count_total_emails(self, source_folder="inbox"):
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        return len(items)

    def list_all_email_ids(self, limit=None, source_folder="inbox"):
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        ids = []
        count = 0
        for message in items:
            if limit and count >= limit:
                break
            try:
                ids.append(message.EntryID)
                count += 1
            except Exception:
                pass
        return ids

    def fetch_email_by_id(self, entry_id, source_folder="inbox"):
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        for message in items:
            if message.EntryID == entry_id:
                return self._parse_message(message, source_folder)
        return None

    def archive_email_by_id(self, entry_id: str) -> EmailMessage:
        inbox, archive = self.connect_inbox()
        items = inbox.Items
        for message in items:
            if message.EntryID == entry_id:
                archived = message.Move(archive)
                return self._parse_message(archived, source_folder="archive")
        raise ValueError(f"Email avec ID {entry_id} introuvable.")

    def archive_emails_by_ids(self, ids: list[str]) -> list[EmailMessage]:
        return [self.archive_email_by_id(entry_id) for entry_id in ids]

    def send_email(self, to: list[str], subject: str, body: str, attachments: list[str] = None):
        pythoncom.CoInitialize()
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(to)
        mail.Subject = subject
        mail.Body = body
        if attachments:
            for path in attachments:
                if os.path.exists(path):
                    mail.Attachments.Add(Source=path)
                else:
                    print(f"Pièce jointe introuvable : {path}")
        mail.Send()

    def reply_to_all(self, entry_id: str, message: str):
        pythoncom.CoInitialize()
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        for item in items:
            if item.EntryID == entry_id:
                reply = item.ReplyAll()
                reply.Body = f"{message}\n\n{item.Body}"
                reply.Send()
                return True
        raise ValueError(f"Email avec ID {entry_id} introuvable pour reply_to_all.")

    def forward_email(self, entry_id: str, to: list[str], message: str = ""):
        pythoncom.CoInitialize()
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        for item in items:
            if item.EntryID == entry_id:
                fwd = item.Forward()
                fwd.To = ";".join(to)
                fwd.Body = f"{message}\n\n{item.Body}"
                fwd.Send()
                return True
        raise ValueError(f"Email avec ID {entry_id} introuvable pour forward.")

    def search_emails_by_subject(self, keyword: str, limit: int = 10, source_folder="inbox") -> list[EmailMessage]:
        inbox, _ = self.connect_inbox()
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        results = []
        count = 0
        keyword_lower = keyword.lower()
        for message in items:
            try:
                if keyword_lower in (message.Subject or "").lower():
                    results.append(self._parse_message(message, source_folder))
                    count += 1
                    if count >= limit:
                        break
            except Exception as e:
                print(f"Erreur de lecture d'email : {e}")
        return results

    def _parse_message(self, message, source_folder="inbox"):
        subject = self._clean_subject(message.Subject)
        body = message.Body or ""
        date = message.ReceivedTime if message.ReceivedTime else datetime.now()
        sender = self._get_sender(message)
        recipients = self._extract_recipients(message)

        return EmailMessage(
            subject=subject,
            body=body,
            date=date,
            sender=sender,
            recipients=recipients,
            source=source_folder
        )

    def _clean_subject(self, subject):
        if not subject:
            return "(Sans sujet)"
        return subject.lower().replace("re:", "").replace("tr:", "").replace("fw:", "").strip().capitalize()

    def _get_sender(self, msg):
        try:
            pa = msg.PropertyAccessor
            smtp = pa.GetProperty("http://schemas.microsoft.com/mapi/proptag/0x5D01001F")
            if smtp:
                return smtp
        except Exception:
            pass
        try:
            if hasattr(msg, "SenderEmailAddress") and msg.SenderEmailAddress:
                return msg.SenderEmailAddress
            if hasattr(msg, "SenderName") and msg.SenderName:
                return msg.SenderName
        except Exception:
            pass
        return "Expéditeur inconnu"

    def _extract_recipients(self, msg):
        dest = []
        try:
            if msg.To:
                dest += [email.strip() for email in msg.To.split(';') if email.strip()]
            if msg.CC:
                dest += [email.strip() for email in msg.CC.split(';') if email.strip()]
        except Exception:
            pass
        return list(dict.fromkeys(dest))  # Supprime les doublons en conservant l'ordre
