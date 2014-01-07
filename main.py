from __future__ import with_statement
import urllib
import webapp2
import csv
from StringIO import StringIO

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import files
from Crypto.PublicKey import RSA
from Crypto import Random

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(
            '''
            <html>
              <body>
                <form action="/upload" enctype="multipart/form-data" method="post">
                  <input type="file" name="file"/>
                  Enter Key: <textarea name="key"></textarea>
                  <input type="submit" />
                </form>
              <body/>
            <html/>
            '''
        )

class UploadHandler(webapp2.RequestHandler):
    
        
    @staticmethod
    def crypt(plaintext, key):
        # Use a fixed private key here to get a deterministic result for testing
        key = RSA.importKey(key)
        enc_data = key.encrypt(plaintext, 32)
        
        # encode the byte data into ASCII data so that it could be printed out in the browser
        return enc_data[0].encode('base64')
    
    def old_crypt(self, plaintext):
        # Use a fixed private key here to get a deterministic result for testing
        public_key = key.publickey()
        enc_data = public_key.encrypt(plaintext, 32)
        
        # encode the byte data into ASCII data so that it could be printed out in the browser
        return enc_data[0].encode('base64')

    def post(self):
        rows=self.request.POST.get('file').value
        key = self.request.POST.get('key')
        file_name = files.blobstore.create(mime_type='text/plain')
        with files.open(file_name, 'a') as f:
            writer = csv.writer(f , delimiter=',')
            for row in csv.reader(StringIO(rows), delimiter=','):
                if len(row) > 1:
                    row[1] = self.crypt(row[1], key)
                writer.writerow(row)
        files.finalize(file_name)
        
        blobs = blobstore.BlobInfo.all()
        blob_links = [
                      '<a href="/serve/%s">File %s</a><br/>' % (blob.key(), index+1)
                      for index, blob in enumerate(blobs)
                     ]
        
        self.response.out.write(
            '''
               <html>
                 <body>
                 %s
                 </body>
                </html>
            ''' % "".join(blob_links)
        )

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/upload', UploadHandler),
                               ('/serve/([^/]+)?', ServeHandler)],
                              debug=True)
