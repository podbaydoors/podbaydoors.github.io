import sys
import os
import time
import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MarkdownEventHandler(FileSystemEventHandler):
    def __init__(self, input_file, output_file, debounce_interval=1.0):
        self.input_file = os.path.abspath(input_file)
        self.output_file = os.path.abspath(output_file)
        self.debounce_interval = debounce_interval
        self.last_conversion = 0
        print(f"[DEBUG] Watching file: {self.input_file}")
        # Do an initial conversion
        self.convert_markdown()

    def on_modified(self, event):
        event_path = os.path.normcase(os.path.abspath(event.src_path))
        target_path = os.path.normcase(self.input_file)
        print(f"[DEBUG] on_modified event triggered for: {event_path}")

        # Check if the modified file is the markdown file we are watching
        if event_path != target_path:
            return

        # Debounce: ignore events that occur too close together.
        now = time.time()
        if now - self.last_conversion < self.debounce_interval:
            print("[DEBUG] Change event ignored due to debounce.")
            return

        self.last_conversion = now
        print("[DEBUG] Change detected in the monitored markdown file.")
        self.convert_markdown()

    def convert_markdown(self):
        print("[DEBUG] Converting markdown to HTML...")
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                md_text = f.read()
            print("[DEBUG] Markdown file read successfully.")
        except Exception as e:
            print(f"[ERROR] Error reading input file: {e}")
            return

        # Enable fenced code blocks extension.
        html_body = markdown.markdown(md_text, extensions=['fenced_code'])

        html_doc = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Converted Markdown</title>
        <link rel="stylesheet" type="text/css" href="sakura.css">
    </head>
    <body>
    {html_body}
    </body>
    </html>
    """
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_doc)
            print(f"[DEBUG] Conversion complete: '{self.input_file}' -> '{self.output_file}'")
        except Exception as e:
            print(f"[ERROR] Error writing output file: {e}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py input.md output.html [-live]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    live_mode = '-live' in sys.argv[3:]

    print(f"[DEBUG] Input file: {input_file}")
    print(f"[DEBUG] Output file: {output_file}")
    print(f"[DEBUG] Live mode: {'ON' if live_mode else 'OFF'}")

    # Create the event handler (performs an initial conversion)
    event_handler = MarkdownEventHandler(input_file, output_file)

    # If live mode is not specified, exit after the initial conversion
    if not live_mode:
        print("[DEBUG] Live mode not enabled. Exiting after initial conversion.")
        return

    # Set up the watchdog observer on the directory containing the input file
    directory = os.path.dirname(os.path.abspath(input_file))
    print(f"[DEBUG] Monitoring directory: {directory}")
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    print("[DEBUG] Live mode active. Monitoring for changes... (Press Ctrl+C to exit)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[DEBUG] KeyboardInterrupt received. Stopping live monitoring...")
        observer.stop()
    observer.join()
    print("[DEBUG] Observer stopped.")

if __name__ == '__main__':
    main()
