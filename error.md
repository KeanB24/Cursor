(base) PS C:\Users\CRANB1\Cursor\Cursor> pip install -r requirements.txt             

[notice] A new release of pip is available: 25.2 -> 26.2.1
[notice] To update, run: python.exe -m pip install --upgrade pip
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'


3, in resolve_redonline_token
    raise RuntimeError(
RuntimeError: Set REDONLINE_API_KEY (or REDONLINE_TOKEN), or OAuth via REDONLINE_TOKEN_URL + REDONLINE_CLIENT_ID + REDONLINE_CLIENT_SECRET


(base) PS C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest> python scripts/discover_rol_schema.py
Calling list_sites...
  FAILED: RuntimeError: REDONLINE_BASE_URL is required when not in mock mode
Calling list_users_by_site...
  FAILED: RuntimeError: REDONLINE_BASE_URL is required when not in mock mode
Calling list_mapping_references...
  FAILED: RuntimeError: REDONLINE_BASE_URL is required when not in mock mode
Calling list_tasks_by_user...
  FAILED: RuntimeError: REDONLINE_BASE_URL is required when not in mock mode


  PS C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest> python scripts/discover_rol_schema.py
Calling list_sites...
  FAILED: ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)
Calling list_users_by_site...
  FAILED: ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)
Calling list_mapping_references...
  FAILED: ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)
Calling list_tasks_by_user...
  FAILED: ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)

![alt text](image.png)


(base) PS C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest> python scripts/run_local.py --dry-run
2026-10-04 20:38:04,538 INFO redonline_cdf.pipeline.ingest Cascaded ingest: fetching sites
Traceback (most recent call last):
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_transports\default.py", line 101, in map_httpcore_exceptions
    yield
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_transports\default.py", line 250, in handle_request
    resp = self._pool.handle_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpcore\_sync\connection_pool.py", line 216, in handle_request
    raise exc from None
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpcore\_sync\connection_pool.py", line 196, in handle_request
    response = connection.handle_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpcore\_sync\http_proxy.py", line 317, in handle_request
    stream = stream.start_tls(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpcore\_sync\http11.py", line 383, in start_tls
    return self._stream.start_tls(ssl_context, server_hostname, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpcore\_backends\sync.py", line 152, in start_tls
    with map_exceptions(exc_map):
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\contextlib.py", line 155, in __exit__
    self.gen.throw(typ, value, traceback)
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpcore\_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\scripts\run_local.py", line 15, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\src\redonline_cdf\cli.py", line 73, in main
    result = run_ingest(
             ^^^^^^^^^^^
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\src\redonline_cdf\pipeline\ingest.py", line 413, in run_ingest
    return pipeline.run(entities=entities).as_dict()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\src\redonline_cdf\pipeline\ingest.py", line 147, in run
    coerce_record(i) for i in self.redonline.fetch_all("list_sites")
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\src\redonline_cdf\redonline\client.py", line 253, in fetch_all
    return list(self.iter_items(endpoint_name, since=since, path_vars=path_vars))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\src\redonline_cdf\redonline\client.py", line 272, in iter_items
    payload = self._request(
              ^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest\src\redonline_cdf\redonline\client.py", line 241, in _request
    resp = self._http.request(method, url, headers=headers, params=query)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_client.py", line 825, in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_client.py", line 914, in send
    response = self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_client.py", line 942, in _send_handling_auth
    response = self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_client.py", line 979, in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_client.py", line 1014, in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_transports\default.py", line 249, in handle_request
    with map_httpcore_exceptions():
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\contextlib.py", line 155, in __exit__
    self.gen.throw(typ, value, traceback)
  File "C:\Users\CRANB1\AppData\Local\anaconda3\Lib\site-packages\httpx\_transports\default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)
(base) PS C:\Users\CRANB1\Cursor\Cursor\redonline-cdf-ingest> 