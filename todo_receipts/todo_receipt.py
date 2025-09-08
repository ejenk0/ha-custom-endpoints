from escpos.printer import Network
from dotenv import load_dotenv
import os


def obtain_network_printer(ip_address: str, port: int = 9100):
    """
    Obtain a network printer instance.

    :param ip_address: The IP address of the printer.
    :param port: The port number to connect to the printer.
    :param timeout: Connection timeout in seconds.
    :return: An instance of Network printer.
    """
    return Network(ip_address, port=port, timeout=5)


def html_to_image(html_content: str) -> str:
    """
    Convert HTML content to an image file.

    :param html_content: The HTML content to convert.
    :return: The path to the saved image file.
    """
    import imgkit
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        imgkit.from_string(
            html_content,
            temp_file.name,
            options={
                "width": 576,  # 72mm thermal printer width
                "encoding": "UTF-8",
                "disable-local-file-access": "",
                "crop-w": 576,  # Crop to exact width
            },
        )
        return temp_file.name


def url_to_image(url: str) -> str:
    """
    Convert a URL to an image file.

    :param url: The URL to convert.
    :return: The path to the saved image file.
    """
    import imgkit
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        imgkit.from_url(
            url,
            temp_file.name,
            options={
                "width": 576,  # 72mm thermal printer width
                "encoding": "UTF-8",
                "disable-local-file-access": "",
                "crop-w": 576,  # Crop to exact width
            },
        )
        return temp_file.name


def build_todo_html(
    title: str,
    notes: str | None = None,
    lightning_count: int = 2,
    due_date_str: str | None = None,
    is_command: bool = False,
) -> str:
    """Build the TODO HTML, conditionally rendering sections for notes and due date.

    :param title: Task title (required)
    :param notes: Optional description (can be None or empty)
    :param lightning_count: Priority level (1-3)
    :param due_date_str: Optional formatted due date string (e.g., 'Aug 20, 2025')
    :param is_command: Whether this is a command print (no notes/due date)
    :return: HTML string
    """
    try:
        lc = int(lightning_count)
    except Exception:
        lc = 2
    lc = max(1, min(3, lc))
    priority_icons = ("⚡" if not is_command else "♥️") * lc

    has_notes = bool(notes and notes.strip())
    has_due = bool(due_date_str and str(due_date_str).strip())

    command_section = (
        f'<div style="text-align:center;font-weight:350;font-size:24px;line-height:1.2;margin:8px 0 10px;font-style:italic;">This is Ellie\'s command.</div>'
        if is_command
        else ""
    )

    divider_top_optional = (
        '<div style="height:0;border-top:4px solid #000;margin:16px 0;"></div>'
        if ((not is_command) and (has_notes or has_due))
        else ""
    )
    divider_between = (
        '<div style="height:0;border-top:4px solid #000;margin:18px 0;"></div>'
        if ((not is_command) and (has_notes and has_due))
        else ""
    )

    notes_section = (
        f'<div style="text-align:center;font-size:28px;line-height:1.5;white-space:pre-wrap;">{notes}</div>'
        if (has_notes and not is_command)
        else ""
    )
    due_section = (
        f'<div style="text-align:center;font-size:24px;font-weight:600;">Due: {due_date_str}</div>'
        if (has_due and not is_command)
        else ""
    )

    return f"""
<html>
<head>
    <link href='https://fonts.googleapis.com/css2?family=Noto+Emoji:wght@400' rel='stylesheet' type='text/css'>
</head>
  <body style="margin:0;padding:0;background:#fff;color:#111;font-family:DejaVu Sans, Arial, sans-serif;">
    <div style="width:524px;margin:0 auto;padding:24px 20px 20px;border:6px solid #000;border-radius:8px;">
            <div style="text-align:center;
                                    font-size:68px;
                                    letter-spacing:8px;
                                    line-height:1;
                                    margin-bottom:12px;
                                    font-family:'Noto Emoji','Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',DejaVu Sans,Arial,sans-serif;">
                {priority_icons}
            </div>
      <div style="text-align:center;
                  font-weight:700;
                  font-size:48px;
                  line-height:1.2;
                  margin:12px 0 10px;">
        {title}
      </div>
      {divider_top_optional}
      {notes_section}
      {divider_between}
      {due_section}
      {command_section}
    </div>
  </body>
</html>
    """


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    from shutil import copyfile

    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Render/print a TODO as a receipt image"
    )
    parser.add_argument(
        "--command", action="store_true", help="Print as command (no notes/due)"
    )
    parser.add_argument("--title", type=str, help="Title of the TODO")
    parser.add_argument("--notes", type=str, help="Optional description/notes")
    parser.add_argument(
        "--priority", type=int, choices=[1, 2, 3], help="Priority lightning count (1-3)"
    )
    parser.add_argument("--due", type=str, help="Optional due date in YYYY-MM-DD")
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Only render image; do not send to printer",
    )
    parser.add_argument(
        "--out", type=str, help="Path to save rendered image (copied from temp)"
    )

    args = parser.parse_args()

    # Resolve values from CLI first, then env vars, then defaults
    task_title = args.title or os.getenv("TODO_TITLE") or "Sample TODO"
    raw_notes = args.notes if args.notes is not None else os.getenv("TODO_NOTES")
    task_notes = raw_notes if raw_notes is not None else ""

    prio_env = os.getenv("TODO_PRIORITY")
    if args.priority is not None:
        lightning_count = args.priority
    elif prio_env is not None:
        try:
            lightning_count = int(prio_env)
        except ValueError:
            lightning_count = 2
    else:
        lightning_count = 2
    lightning_count = max(1, min(3, int(lightning_count)))

    due_input = args.due or os.getenv("TODO_DUE_DATE")
    due_date_str = None
    if due_input:
        try:
            due_dt = datetime.strptime(due_input, "%Y-%m-%d")
            due_date_str = due_dt.strftime("%b %d, %Y")
        except ValueError:
            print("Invalid due date format (expected YYYY-MM-DD); ignoring.")

    html = build_todo_html(
        title=task_title,
        notes=task_notes,
        lightning_count=lightning_count,
        due_date_str=due_date_str,
        is_command=args.command,
    )

    img_path = html_to_image(html)

    # Save/copy to output path if provided
    if args.out:
        try:
            copyfile(img_path, args.out)
            print(f"Saved image to {args.out}")
        except Exception as e:
            print(f"Failed to save to {args.out}: {e}")

    if args.no_print:
        print("Rendering complete (no print).")
    else:
        # Only require printer settings when actually printing
        printer_ip = os.getenv("PRINTER_IP")
        printer_port = os.getenv("PRINTER_PORT")
        if not printer_ip or not printer_port:
            raise ValueError(
                "Please set PRINTER_IP and PRINTER_PORT in the .env file or use --no-print."
            )

        printer_port = int(printer_port)
        p = obtain_network_printer(printer_ip, port=printer_port)
        print(f"Connected to printer at {printer_ip}:{printer_port}")
        p.image(img_path)
        p.cut()
        p.close()
