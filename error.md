(base) PS C:\Users\CRANB1\Cursor\Cursor> pip install -r requirements.txt             

[notice] A new release of pip is available: 25.2 -> 26.2.1
[notice] To update, run: python.exe -m pip install --upgrade pip
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'


3, in resolve_redonline_token
    raise RuntimeError(
RuntimeError: Set REDONLINE_API_KEY (or REDONLINE_TOKEN), or OAuth via REDONLINE_TOKEN_URL + REDONLINE_CLIENT_ID + REDONLINE_CLIENT_SECRET