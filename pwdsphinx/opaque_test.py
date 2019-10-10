#!/usr/bin/env python

import sphinxlib as o
from binascii import b2a_hex

pwd = "simple guessable dictionary password"
print("trying server inspects password registration flow")
extra = "some additional secret data stored in the blob"
rec = o.opaque_store(pwd, extra)
print("usrSession")
pub, sec = o.opaque_session_usr_start(pwd)
print("srvSession")
resp, sk_s = o.opaque_session_srv(pub, rec)
print("usrSessionEnd")
sk_u, extra = o.opaque_session_usr_finish(pwd, resp, sec)
print("sk_s", b2a_hex(sk_s))
print("sk_u", b2a_hex(sk_u))
assert(sk_s == sk_u)
#print "extra", extra
print("f(sk_s,0)", b2a_hex(o.opaque_f(sk_s, 0x30)))     # 0x30 == '0'
print("f(sk_u,0)", b2a_hex(o.opaque_f(sk_u, 0x30)))
assert(o.opaque_f(sk_s, 0x30)==o.opaque_f(sk_u, 0x30))

print("trying alternative/private registration flow")
# alternative/private registration flow:
print("opaque_private_init_usr_start")
r, alpha = o.opaque_private_init_usr_start(pwd)
print("opaque_private_init_srv_respond")
sec_s, pub_s = o.opaque_private_init_srv_respond(alpha)
print("opaque_private_init_usr_respond")
rec = o.opaque_private_init_usr_respond(pwd, r, pub_s, extra)
print("opaque_private_init_srv_finish")
rec = o.opaque_private_init_srv_finish(sec_s, pub_s, rec)

print("usrSession")
pub, sec = o.opaque_session_usr_start(pwd)
print("srvSession")
resp, sk_s = o.opaque_session_srv(pub, rec)
print("usrSessionEnd")
sk_u, extra = o.opaque_session_usr_finish(pwd, resp, sec)
print("sk_s", b2a_hex(sk_s))
print("sk_u", b2a_hex(sk_u))
assert(sk_s == sk_u)
print("extra", extra)
su = o.opaque_f(sk_s, 0x31) # 0x31 == '1'
us = o.opaque_f(sk_u, 0x31)
print("f(sk_s,1)", b2a_hex(su))
print("f(sk_u,1)", b2a_hex(us))
assert(su==us)
su = o.opaque_f(sk_s, 0x32) # 0x32 == '2'
us = o.opaque_f(sk_u, 0x32)
print("f(sk_s,2)", b2a_hex(su))
print("f(sk_u,2)", b2a_hex(us))
assert(us==su)
