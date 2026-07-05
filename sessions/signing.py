from django.core.signing import TimestampSigner

signer = TimestampSigner()


def generate_qr(session_id):
    return signer.sign(session_id)
