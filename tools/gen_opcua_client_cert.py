"""Gera o certificado de CLIENTE OPC UA do backend (autoassinado, so para desenvolvimento local).
Saida em work/pki/ (fora do Git). Depois de gerado, o servidor do Control Win coloca o certificado em
'Nao confiaveis'/'Em quarentena' na Tela de seguranca: confie nele ali (decisao sua)."""
import datetime as dt
import ipaddress
import socket
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "work/pki")
OUT.mkdir(parents=True, exist_ok=True)
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "LFAM backend (dev)")])
now = dt.datetime.now(dt.timezone.utc)
cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier("urn:lfam:backend"),
                                                    x509.DNSName(socket.gethostname()), x509.DNSName("localhost"),
                                                    x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
        .add_extension(x509.KeyUsage(True, True, True, True, False, False, False, False, False), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(key, hashes.SHA256()))
(OUT / "client_cert.der").write_bytes(cert.public_bytes(serialization.Encoding.DER))
(OUT / "client_key.pem").write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                                       serialization.NoEncryption()))
print("gerado em", OUT.resolve())
