# Certificados adicionales

`sectigo_public_server_auth_ca_ov_r36.pem` es el certificado intermedio
"Sectigo Public Server Authentication CA OV R36".

El servidor de la Superintendencia de Bancos (`www.superbancos.gob.ec`)
no envía este intermedio en el handshake TLS (`openssl s_client ... -showcerts`
solo devuelve el certificado hoja, `Verify return code: 21 (unable to verify
the first certificate)`), un error de configuración del lado del servidor.
Los navegadores lo toleran porque hacen "AIA chasing" (descargan el intermedio
faltante automáticamente); `requests`/`urllib3` no lo hacen, así que toda
descarga vía `requests.Session()` fallaba con `HTTPSConnectionPool` desde
al menos el 2026-09-08.

`descargar.py` combina este archivo con el bundle de `certifi` en vez de
desactivar la verificación SSL (`verify=False`), para no debilitar la
seguridad de la descarga.

Obtenido de la propia cadena AIA del certificado hoja:
`http://crt.sectigo.com/SectigoPublicServerAuthenticationCAOVR36.crt`
