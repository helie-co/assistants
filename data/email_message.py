from datetime import datetime
from typing import List, Optional

class EmailMessage:
    def __init__(
        self,
        subject: str,
        body: str,
        date: datetime,
        sender: str,
        recipients: List[str],
        source: str = "inbox",
        id: Optional[str] = None
    ):
        self.subject = subject
        self.body = body
        self.date = date
        self.sender = sender
        self.recipients = recipients
        self.source = source
        self.id = id or self._generate_id()

    def _generate_id(self):
        date_str = self.date.strftime("%Y-%m-%d_%H-%M")
        return f"{date_str}_mail"

    def __repr__(self):
        return (
            f"<EmailMessage {self.id} | {self.subject} | {self.sender} -> {self.recipients} | {self.date}>"
        )
