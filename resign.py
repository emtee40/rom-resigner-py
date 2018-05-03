from xml.dom import minidom
import re
import os
import mmap
import subprocess

cwd = os.getcwd()

romdir = "/Users/erfanabdi/GitHub/ROM_resigner/files"
securitydir = "/Users/erfanabdi/GitHub/android_build/target/product/security"
mac_permissions = "plat_mac_permissions.xml"

xmldoc = minidom.parse(mac_permissions)
itemlist = xmldoc.getElementsByTagName('signer')
certlen = len(itemlist)

signatures = []
signatures64 = []
seinfos = []

tmpdir = cwd + "/tmp"
signapkjar = cwd + "/signapk.jar"

def CheckCert(filetoopen, cert):
    f = open(filetoopen)
    s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    if s.find(cert) != -1:
        return True
    else:
        return False

def getcert(jar, out):
    extractjar = "jar -xvf " + jar
    extractcert = "openssl pkcs7 -in "+ tmpdir + "/META-INF/CERT.RSA -print_certs -inform DER -out " + out
    output = subprocess.check_output(['bash','-c', extractjar])
    output += subprocess.check_output(['bash','-c', extractcert])
    #print(output)

def sign(jar, certtype):
    if not os.path.exists(securitydir + "/" + certtype + ".pk8"):
        print(certtype + ".pk8 not found in security dir")
        return False
    
    jartmpdir = tmpdir + "/JARTMP"
    if not os.path.exists(jartmpdir):
        os.makedirs(jartmpdir)

    signjarcmd = "java -jar " + signapkjar + " " + securitydir + "/" + certtype + ".x509.pem " + securitydir + "/" + certtype + ".pk8 " + jar + " " + jartmpdir + "/" + os.path.basename(jar)

    movecmd = "mv " + jartmpdir + "/" + os.path.basename(jar) + " " + jar
    output = subprocess.check_output(['bash','-c', signjarcmd])
    output += subprocess.check_output(['bash','-c', movecmd])
    #print(output)
    print(os.path.basename(jar) + " signed as " + seinfo)

index = 0
for s in itemlist:
    signatures.append(s.attributes['signature'].value)
    test64 = s.attributes['signature'].value.decode("hex").encode("base64")
    test64 = test64.decode('utf-8').replace('\n', '')
    
    signatures64.append(re.sub("(.{64})", "\\1\n", test64, 0, re.DOTALL))

    seinfos.append(xmldoc.getElementsByTagName('seinfo')[index].attributes['value'].value)
    index += 1

for root, dirs, files in os.walk(romdir):
    for file in files:
        if file.endswith(".apk") or file.endswith(".jar"):
            jarfile=os.path.join(root, file)
            
            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)
            os.chdir(tmpdir)
            
            out = "foo.cer"
            getcert(jarfile, out)
            
            index = 0
            for seinfo in seinfos:
                if CheckCert(out, signatures64[index]):
                    sign(jarfile, seinfo)
                    break
                index += 1
            if index == certlen:
                print(os.path.basename(jarfile) + " : Unknown => keeping signature")
